from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QHBoxLayout,
    QStyledItemDelegate,
    QStyle,
    QStackedLayout,
    QHeaderView,
)
from PySide6.QtCore import Qt, QSize, Signal, QRect
from PySide6.QtGui import QIcon, QPainter, QCloseEvent
from .components.label import CustomLabel
from .components.announcement import CustomAnnounce
from .mixins.keyboard_shortcuts import KeyboardShortcutsDialogMixin
from .data.data_manager import UserDataManager
from .utils.helpers import get_svg_as_icon
from .workers.fetch_folders_worker import FetchFoldersWorker
from .components.loading import LoadingDots
from .configs.configs import ThemeColors
from .components.button import CustomButton


class FolderTreeDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        super().paint(painter, option, index)

        if option.state & QStyle.StateFlag.State_Selected:
            # --- THAY ĐỔI 1: Tăng resolution khi tạo ảnh ---
            # Thay vì 24, hãy render ra 64 hoặc 96.
            # Dù ảnh to nhưng ta sẽ vẽ nó co lại vào khung 24px sau.
            high_res_size = 64

            check_icon = get_svg_as_icon(
                "check_icon",
                high_res_size,  # Render to để nét căng
                stroke_color="black",
                stroke_width=3,
            )

            # Tính toán khung vẽ (Vẫn giữ logic vị trí cũ 24px)
            display_size = 24
            padding_right = 10
            rect_x = option.rect.right() - display_size - padding_right
            rect_y = option.rect.center().y() - (display_size // 2)
            target_rect = QRect(rect_x, rect_y, display_size, display_size)

            # --- THAY ĐỔI 2: Bật khử răng cưa khi vẽ ---
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(
                QPainter.RenderHint.SmoothPixmapTransform
            )  # <--- Quan trọng

            # Vẽ ảnh 64px vào khung 24px -> Mịn tuyệt đối
            painter.drawPixmap(target_rect, check_icon)

            painter.restore()


class GDriveFoldersPicker(KeyboardShortcutsDialogMixin):
    """
    Dialog chọn thư mục Google Drive dạng cây (Tree) với Lazy Loading.
    """

    folder_picked = Signal(str)  # Signal phát ra folder path khi chọn xong

    # Role dùng để lưu trạng thái đã load children chưa
    LOADED_ROLE = Qt.ItemDataRole.UserRole + 1
    # Role lưu full path (hoặc tên folder để tái tạo path)
    FULL_PATH_ROLE = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Chọn thư mục Google Drive")
        self.resize(600, 500)

        self._data_manager = UserDataManager()
        self._worker = None

        # State
        self._selected_full_path = ""
        self._loading_nodes = set()  # Track nodes đang loading

        self._setup_ui()

        # Load root folders ngay khi mở
        self._load_root_data()

    def _setup_ui(self):
        # 1. Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # --- HEADER SECTION ---
        self.lbl_info = CustomLabel("Danh sách thư mục:", font_size=14, is_bold=True)
        self.lbl_info.setStyleSheet("color: #b8b8b8;")
        main_layout.addWidget(self.lbl_info)

        # --- CONTENT SECTION ---
        # StackedLayout: Layer 0 (Loading toàn màn hình - ít dùng), Layer 1 (Tree)
        self.content_layout = QStackedLayout()

        # Input Loading Dots (cho lúc load root ban đầu)
        self.loading_dots = LoadingDots(
            self,
            dot_count=4,
            dot_size=14,
            color=ThemeColors.MAIN,
        )
        loading_container = QWidget()
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.addWidget(
            self.loading_dots, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Tree Widget
        self.tree_widget = QTreeWidget(self)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setIconSize(QSize(24, 24))
        self.tree_widget.setItemDelegate(FolderTreeDelegate(self.tree_widget))
        self.tree_widget.setColumnCount(1)
        self.tree_widget.setIndentation(20)

        # Style cho Tree
        self.tree_widget.setStyleSheet(
            f"""
            QTreeWidget {{
                outline: 0;
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 6px;
                color: white;
                font-size: 16px;
            }}
            QTreeWidget::item {{
                height: 32px;
                padding: 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: {ThemeColors.GRAY_HOVER};
            }}
            QTreeWidget::item:selected {{
                background-color: {ThemeColors.MAIN};
                color: black;
            }}
            /* Mũi tên expand/collapse */
            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {{
                border-image: none;
                image: url(:/icons/right_arrow_icon.svg); 
            }}
            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {{
                border-image: none;
                image: url(:/icons/down_arrow_icon.svg);
            }}
            """
        )

        # Events
        self.tree_widget.itemExpanded.connect(self._on_item_expanded)
        self.tree_widget.itemSelectionChanged.connect(self._on_item_selection_changed)
        # Double click để chọn luôn và đóng
        self.tree_widget.itemDoubleClicked.connect(self._on_confirm_selection)

        self.content_layout.addWidget(loading_container)  # 0
        self.content_layout.addWidget(self.tree_widget)  # 1
        self.content_layout.setCurrentIndex(1)  # Mặc định hiện tree trắng

        main_layout.addLayout(self.content_layout)

        # --- FOOTER SECTION ---
        btn_layout = QHBoxLayout()
        self.btn_refresh = CustomButton("Làm mới toàn bộ")
        self.btn_refresh.setIcon(
            get_svg_as_icon(
                "refresh_icon", 24, stroke_color="black", margins=(0, 0, 4, 0)
            )
        )
        self.btn_refresh.on_clicked(self._load_root_data)

        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()

        self.btn_select = CustomButton("Chọn thư mục này", is_bold=True)
        self.btn_select.setIcon(
            get_svg_as_icon(
                "double_check_icon", 24, stroke_color="black", margins=(0, 0, 4, 0)
            )
        )
        self.btn_select.on_clicked(self._on_confirm_selection)
        btn_layout.addWidget(self.btn_select)

        main_layout.addLayout(btn_layout)

        # Theme chung
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        # Init state buttons
        self._enable_buttons(True, False)

    def _enable_buttons(self, enable_refresh: bool, enable_select: bool):
        self.btn_refresh.setEnabled(enable_refresh)
        self.btn_select.setEnabled(enable_select)

        # Style update
        if enable_refresh:
            self.btn_refresh.setStyleSheet(
                f"""
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                color: white;
                padding: 4px 12px 6px;
                border-radius: 6px;
                """
            )
            self.btn_refresh.update_icon_color("white")
        else:
            self.btn_refresh.setStyleSheet(
                f"""
                background-color: {ThemeColors.STRONG_GRAY};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                color: black;
                padding: 4px 12px 6px;
                border-radius: 6px;
                """
            )
            self.btn_refresh.update_icon_color("black")

        if enable_select:
            self.btn_select.setStyleSheet(
                f"""
                background-color: {ThemeColors.MAIN};
                color: black;
                padding: 4px 12px 6px;
                border-radius: 6px;
                """
            )
        else:
            self.btn_select.setStyleSheet(
                f"""
                background-color: {ThemeColors.STRONG_GRAY};
                color: black;
                padding: 4px 12px 6px;
                border-radius: 6px;
                """
            )

    def _get_remote_name(self):
        remote = self._data_manager.get_active_remote()
        if not remote:
            self.lbl_info.setText("Chưa chọn tài khoản (Remote).")
            return None
        return remote

    # --- LOGIC: ROOT FILES ---
    def _load_root_data(self):
        remote_name = self._get_remote_name()
        if not remote_name:
            return

        # UI State
        self.tree_widget.clear()
        self.content_layout.setCurrentIndex(0)  # Loading
        self.loading_dots.start()
        self.lbl_info.setText(f"Đang tải danh sách gốc từ: {remote_name}...")
        self._enable_buttons(False, False)

        # Worker
        self._start_fetch_worker(remote_name, "", is_root=True)

    # --- LOGIC: EXPAND NODE ---
    def _on_item_expanded(self, item: QTreeWidgetItem):
        # Kiểm tra xem node này đã load chưa
        if item.data(0, self.LOADED_ROLE) == True:
            return

        remote_name = self._get_remote_name()
        if not remote_name:
            return

        # Lấy path của node hiện tại
        # Path được lưu trong FULL_PATH_ROLE hoặc tái tạo từ parent
        # Ở đây ta nên lưu full path từ lúc tạo node cha
        current_path = item.data(0, self.FULL_PATH_ROLE)

        # Đánh dấu đang load (để tránh spam)
        # Có thể đổi icon sang loading
        self._set_item_loading_state(item, True)

        self.lbl_info.setText(f"Đang tải con của: {current_path}...")
        self._start_fetch_worker(remote_name, current_path, parent_item=item)

    def _start_fetch_worker(self, remote_name, path, is_root=False, parent_item=None):
        # Stop worker cũ nếu đang chạy (chỉ áp dụng nếu user spam refresh root,
        # còn expand nhiều node cùng lúc thì nên hỗ trợ queue hoặc worker riêng biêt?
        # Code cũ dùng 1 biến self._worker, nên tạm thời ta chấp nhận 1 worker tại 1 thời điểm
        # hoặc tạo worker cục bộ. Để an toàn và đơn giản: tạo worker mới, không lưu vào self._worker
        # nếu muốn concurrent, nhưng FetchFoldersWorker là QThread, cần giữ ref.
        # => Tạm thời: cancel worker cũ nếu có (chấp nhận chỉ load 1 cái 1 lúc).

        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()

        worker = FetchFoldersWorker(remote_name, path)
        worker.data_ready.connect(
            lambda folders, err: self._on_worker_finished(
                folders, err, is_root, parent_item, worker
            )
        )
        self._worker = worker  # Keep reference
        worker.start()

    def _on_worker_finished(self, folders, error_msg, is_root, parent_item, worker_ref):
        # Clean up ref
        if self._worker == worker_ref:
            self._worker = None

        if error_msg:
            CustomAnnounce.error(self, "Lỗi tải dữ liệu", error_msg)
            if is_root:
                self.content_layout.setCurrentIndex(1)  # Back to tree (empty)
                self.loading_dots.stop()
                self._enable_buttons(True, False)
            else:
                # Revert loading state của item
                self._set_item_loading_state(parent_item, False)
            return

        # Success
        if is_root:
            self.content_layout.setCurrentIndex(1)
            self.loading_dots.stop()
            self._populate_tree(
                self.tree_widget.invisibleRootItem(), folders, parent_path=""
            )
            self.lbl_info.setText("Đã tải xong danh sách gốc.")
            self._enable_buttons(True, False)
        else:
            # Xử lý cho node con
            self._populate_tree(
                parent_item,
                folders,
                parent_path=parent_item.data(0, self.FULL_PATH_ROLE),
            )
            self._set_item_loading_state(parent_item, False)  # Sets icon back to folder
            # Mark as loaded
            parent_item.setData(0, self.LOADED_ROLE, True)
            self.lbl_info.setText("Đã tải xong.")

    def _populate_tree(self, parent_node, folder_names, parent_path=""):
        # parent_node có thể là invisibleRootItem hoặc 1 QTreeWidgetItem

        # Nếu là node con, xóa dummy item "Loading..." trước
        if isinstance(parent_node, QTreeWidgetItem):
            # Xóa hết con cũ (thường là dummy)
            parent_node.takeChildren()

        if not folder_names:
            if isinstance(parent_node, QTreeWidgetItem):
                # Nếu không có con, set child indicator policy thành Don'tShow để mất mũi tên
                parent_node.setChildIndicatorPolicy(
                    QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator
                )  # Vẫn hiện? hay ẩn?
                # Thực ra nếu rỗng thì không cần làm gì, nó tự hết expand
            return

        # Icons
        icon_folder = get_svg_as_icon(
            "folder_icon", 24, stroke_color="#FFD700", stroke_width=3
        )

        items_to_add = []
        for name in folder_names:
            item = QTreeWidgetItem()
            item.setText(0, name)
            item.setIcon(0, icon_folder)

            # Tính full path
            full_path = f"{parent_path}/{name}" if parent_path else name
            item.setData(0, self.FULL_PATH_ROLE, full_path)
            item.setData(0, self.LOADED_ROLE, False)  # Chưa load con

            # Thêm dummy child để hiện mũi tên expand
            dummy = QTreeWidgetItem()
            dummy.setText(0, "Đang tải...")
            item.addChild(dummy)

            items_to_add.append(item)

        if isinstance(parent_node, QTreeWidget):  # Root
            parent_node.addTopLevelItems(items_to_add)
        else:
            parent_node.addChildren(items_to_add)

    def _set_item_loading_state(self, item: QTreeWidgetItem, is_loading: bool):
        if is_loading:
            # Có thể đổi icon thành loading hoặc text tạm
            # item.setText(0, f"{item.text(0)} (Đang tải...)")
            pass
        else:
            # item.setText(0, item.text(0).replace(" (Đang tải...)", ""))
            pass

    def _on_item_selection_changed(self):
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            self._selected_full_path = ""
            self._enable_buttons(True, False)
            return

        item = selected_items[0]
        # Bỏ qua nếu chọn phải dummy item
        if item.text(0) == "Đang tải...":
            self._selected_full_path = ""
            self._enable_buttons(True, False)
            return

        self._selected_full_path = item.data(0, self.FULL_PATH_ROLE)
        self._enable_buttons(True, True)

    def _on_confirm_selection(self):
        if self._selected_full_path:
            self.folder_picked.emit(self._selected_full_path)
            self.accept()
        else:
            # Nếu double click vào item dummy
            if (
                self.tree_widget.currentItem()
                and self.tree_widget.currentItem().text(0) == "Đang tải..."
            ):
                return
            CustomAnnounce.warn(self, "Chưa chọn", "Vui lòng chọn một thư mục.")

    def closeEvent(self, event: QCloseEvent):
        if self._worker is not None and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()
        self.loading_dots.stop()
        super().closeEvent(event)
