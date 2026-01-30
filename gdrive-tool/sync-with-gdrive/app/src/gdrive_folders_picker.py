from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QStyledItemDelegate,
    QStyle,
    QStackedLayout,
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


class FolderDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        # 1. Vẽ nội dung mặc định (Nền, Text, Icon Folder bên trái)
        super().paint(painter, option, index)

        # 2. Kiểm tra nếu item đang được chọn
        if option.state & QStyle.StateFlag.State_Selected:
            # Lấy icon check màu đen (để hợp với text màu đen khi select)
            check_icon = get_svg_as_icon(
                "check_icon", 24, stroke_color="black", stroke_width=3
            )

            # Tính toán vị trí vẽ (Căn phải)
            icon_size = 24
            padding_right = 10  # Cách lề phải 10px

            # Tọa độ X: Lề phải của item - padding - kích thước icon
            rect_x = option.rect.right() - icon_size - padding_right
            # Tọa độ Y: Căn giữa theo chiều dọc
            rect_y = option.rect.center().y() - (icon_size // 2)

            target_rect = QRect(rect_x, rect_y, icon_size, icon_size)

            # Vẽ icon lên
            painter.drawPixmap(target_rect, check_icon)


class GDriveFoldersPicker(KeyboardShortcutsDialogMixin):
    """
    Dialog chọn thư mục Google Drive để đồng bộ.
    """

    folder_picked = Signal(str)  # Signal phát ra folder path khi chọn xong

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Chọn thư mục Google Drive")
        self.resize(500, 400)

        self._data_manager = UserDataManager()
        self._worker = None
        self._current_path = ""  # Đường dẫn hiện tại
        self._selected_folder_name = ""  # Tên thư mục được chọn
        self._selected_folder_path: list[str] = (
            []
        )  # Đường dẫn đầy đủ của thư mục được chọn bắt đầu từ root của active remote
        self._folders_are_empty = False

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 1. Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # --- HEADER SECTION ---
        self.lbl_info = CustomLabel(
            "Đang tải danh sách thư mục...", font_size=14, is_bold=True
        )
        self.lbl_info.setStyleSheet("color: #b8b8b8;")
        main_layout.addWidget(self.lbl_info)

        # --- CONTENT SECTION (Dùng StackedLayout) ---
        self.content_layout = QStackedLayout()

        # Layer 0: Loading Dots Container
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

        # Layer 1: List Widget
        self.list_widget = QListWidget(self)
        self.list_widget.setIconSize(QSize(24, 24))
        self.list_widget.setItemDelegate(FolderDelegate(self.list_widget))
        self.list_widget.setStyleSheet(
            f"""
            QListWidget {{
                outline: 0;
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 6px;
                color: white;
                font-size: 18px;
                padding: 5px;
            }}
            QListWidget::item {{
                height: 30px;
                padding: 8px;
            }}
            QListWidget::item:hover {{
                background-color: {ThemeColors.GRAY_HOVER};
            }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.MAIN};
                color: black;
            }}
        """
        )
        # Kích hoạt double click để chọn
        self.list_widget.itemDoubleClicked.connect(self._on_select_folder)
        # Kích hoạt sự kiện thay đổi lựa chọn (single click)
        self.list_widget.itemSelectionChanged.connect(self._on_item_selection_changed)

        # Add layers vào stack
        self.content_layout.addWidget(loading_container)  # Index 0
        self.content_layout.addWidget(self.list_widget)  # Index 1

        main_layout.addLayout(self.content_layout)

        # --- FOOTER SECTION ---
        btn_layout = QHBoxLayout()
        self.btn_refresh = CustomButton("Làm mới")
        self.btn_refresh.setIcon(
            get_svg_as_icon(
                "refresh_icon", 24, stroke_color="black", margins=(0, 0, 4, 0)
            )
        )
        self.btn_refresh.setIconSize(QSize(24, 24))
        self.btn_refresh.on_clicked(self._load_data)
        btn_layout.addWidget(self.btn_refresh)

        btn_layout.addStretch()

        self.btn_select = CustomButton(
            "Chọn thư mục này",
            is_bold=True,
        )
        self.btn_select.setIcon(
            get_svg_as_icon(
                "double_check_icon", 24, stroke_color="black", margins=(0, 0, 4, 0)
            )
        )
        self.btn_select.setIconSize(QSize(24, 24))
        self.btn_select.on_clicked(self._on_select_folder)
        btn_layout.addWidget(self.btn_select)

        main_layout.addLayout(btn_layout)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

    def _enable_buttons(
        self, enable_refresh_btn: bool, enable_select_btn: bool
    ) -> None:
        """Bật/Tắt nút bấm"""
        self.btn_refresh.setEnabled(enable_refresh_btn)
        self.btn_select.setEnabled(enable_select_btn)
        if enable_refresh_btn:
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
        if enable_select_btn:
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

    def _set_loading_state(self, is_loading: bool):
        """
        Hàm trung tâm quản lý trạng thái UI (Loading vs Finished).
        """
        # 1. Xử lý Nút bấm (Enable/Disable & Màu sắc)
        # Khi setEnabled(False), nút sẽ tự động chuyển sang màu xám (disabled state)
        # Khi setEnabled(True), nút sẽ trở lại màu gốc (xanh/trắng)
        self.btn_refresh.setEnabled(not is_loading)
        self.btn_select.setEnabled(not is_loading)

        # 2. Xử lý Layout & Animation
        if is_loading:
            # Hiện Loading, Ẩn List
            self.content_layout.setCurrentIndex(0)
            self.loading_dots.start()
            self._enable_buttons(False, bool(self._selected_folder_name))
        else:
            # Ẩn Loading, Hiện List
            self.loading_dots.stop()
            self.content_layout.setCurrentIndex(1)
            self._enable_buttons(True, bool(self._selected_folder_name))

    def _load_data(self):
        """Khởi động worker"""
        remote_name = self._data_manager.get_active_remote()
        if not remote_name:
            self.lbl_info.setText("Chưa chọn tài khoản (Remote).")
            self.list_widget.clear()
            return

        # Dọn dẹp worker cũ an toàn
        if self._worker is not None:
            try:
                if self._worker.isRunning():
                    self._worker.quit()
                    self._worker.wait()
                self._worker.deleteLater()
            except RuntimeError:
                pass
            self._worker = None

        # --- BẬT trạng thái LOADING ---
        self.lbl_info.setText(f"Đang lấy danh sách từ: {remote_name}...")
        self.list_widget.clear()

        # Gọi hàm quản lý state
        self._set_loading_state(True)

        # Chạy Worker
        self._worker = FetchFoldersWorker(remote_name, self._current_path)
        self._worker.data_ready.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, folders: list, error_msg: str):
        """Callback khi xong"""
        # --- TẮT trạng thái LOADING ---
        self._set_loading_state(False)

        # Xử lý kết quả
        if error_msg:
            CustomAnnounce.error(
                self,
                title="Lỗi tải dữ liệu",
                message=f"Không thể lấy danh sách:\n{error_msg}",
            )
            self.lbl_info.setText("Lỗi khi tải dữ liệu.")
            return

        if not folders:
            self.list_widget.addItem("(Thư mục trống)")
            self._folders_are_empty = True
        else:
            self._folders_are_empty = False
            pixmap_normal = get_svg_as_icon(
                "folder_icon",
                24,
                stroke_color="#FFD700",
                stroke_width=3,
                margins=(0, 0, 4, 0),
            )
            pixmap_selected = get_svg_as_icon(
                "folder_icon",
                24,
                stroke_color="#000000",
                stroke_width=3,
                margins=(0, 0, 4, 0),
            )

            icon = QIcon()
            icon.addPixmap(pixmap_normal, QIcon.Mode.Normal)
            icon.addPixmap(pixmap_selected, QIcon.Mode.Selected)
            icon.addPixmap(pixmap_selected, QIcon.Mode.Active)

            for folder_name in folders:
                item = QListWidgetItem(icon, folder_name)
                item.setToolTip(folder_name)
                self.list_widget.addItem(item)

        self.lbl_info.setText(f"Tìm thấy {len(folders)} thư mục.")

    def _on_item_selection_changed(self):
        """Xử lý khi người dùng chọn (click) vào một item trong danh sách."""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            self._selected_folder_name = ""
            self._enable_buttons(True, False)
            return

        item_text = selected_items[0].text()

        # Bỏ qua nếu là item thông báo trống
        if self._folders_are_empty:
            self._selected_folder_name = ""
            self._enable_buttons(True, False)
            return

        self._selected_folder_name = item_text
        # Enable nút Select vì đã có thư mục hợp lệ được chọn
        self._enable_buttons(True, True)

    def _on_select_folder(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            print(f">>> Đã chọn folder: {current_item.text()}")
            # Tại đây bạn có thể emit signal hoặc xử lý logic lưu config
            self.on_folder_picked(current_item.text())
            self.accept()
        else:
            CustomAnnounce.warn(
                self, "Thông báo", "Vui lòng chọn một thư mục trong danh sách."
            )

    def on_folder_picked(self, folder_name: str):
        """Hàm gọi khi folder được chọn xong"""
        self.folder_picked.emit(folder_name)

    def closeEvent(self, event: QCloseEvent):
        """Đảm bảo worker dừng chạy khi đóng cửa sổ"""
        if self._worker is not None:
            try:
                if self._worker.isRunning():
                    self._worker.quit()
                    self._worker.wait()
            except RuntimeError:
                pass

        self.loading_dots.stop()
        super().closeEvent(event)
