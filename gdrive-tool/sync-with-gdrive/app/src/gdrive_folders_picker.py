# src/gdrive_folders_picker.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QLabel,
    QHBoxLayout,
    QPushButton,
)
from PySide6.QtCore import Qt, QSize
from .mixins.keyboard_shortcuts import KeyboardShortcutsDialogMixin
from .data.data_manager import UserDataManager
from .utils.helpers import get_svg_as_icon
from .workers.fetch_folders_worker import FetchFoldersWorker
from .components.loading import LoadingDots  # Giả sử bạn có hoặc dùng QLabel tạm
from .configs.configs import ThemeColors


class GDriveFoldersPicker(KeyboardShortcutsDialogMixin):
    """
    Dialog chọn thư mục Google Drive để đồng bộ.
    """

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Chọn thư mục Google Drive")
        self.resize(500, 600)

        self._data_manager = UserDataManager()
        self._worker = None
        self._current_path = (
            ""  # Đường dẫn hiện tại (để sau này có thể navigate sâu hơn)
        )

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # 1. Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 2. Header / Info
        self.lbl_info = QLabel("Đang tải danh sách thư mục...")
        self.lbl_info.setStyleSheet("color: #b8b8b8; font-size: 14px;")
        layout.addWidget(self.lbl_info)

        # 3. List Widget hiển thị thư mục
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {ThemeColors.GRAY_BACKGROUND if hasattr(ThemeColors, 'GRAY_BACKGROUND') else '#2d2d2d'};
                border: 1px solid {ThemeColors.GRAY_BORDER if hasattr(ThemeColors, 'GRAY_BORDER') else '#4d4d4d'};
                border-radius: 6px;
                color: white;
                font-size: 14px;
                padding: 5px;
            }}
            QListWidget::item {{
                height: 36px;
                padding-left: 5px;
            }}
            QListWidget::item:hover {{
                background-color: {ThemeColors.GRAY_HOVER if hasattr(ThemeColors, 'GRAY_HOVER') else '#3d3d3d'};
            }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.MAIN if hasattr(ThemeColors, 'MAIN') else '#7289DA'};
                color: black;
            }}
        """
        )
        layout.addWidget(self.list_widget)

        # 4. Buttons (Refresh / Select)
        btn_layout = QHBoxLayout()

        self.btn_refresh = QPushButton("Làm mới")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self._load_data)
        btn_layout.addWidget(self.btn_refresh)

        btn_layout.addStretch()

        self.btn_select = QPushButton("Chọn thư mục này")
        self.btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_select.setStyleSheet(
            f"background-color: {ThemeColors.MAIN if hasattr(ThemeColors, 'MAIN') else 'blue'}; color: black; font-weight: bold; padding: 6px 12px; border-radius: 4px;"
        )
        self.btn_select.clicked.connect(self._on_select_folder)
        btn_layout.addWidget(self.btn_select)

        layout.addLayout(btn_layout)

        # Style chung cho Window
        self.setStyleSheet(f"background-color: #1e1e1e; color: white;")

    def _load_data(self):
        """Khởi động worker để lấy dữ liệu"""
        remote_name = self._data_manager.get_active_remote()

        if not remote_name:
            self.lbl_info.setText(
                "Chưa chọn tài khoản (Remote). Vui lòng cấu hình trước."
            )
            self.list_widget.clear()
            return

        self.lbl_info.setText(f"Đang lấy danh sách từ: {remote_name}...")
        self.list_widget.clear()
        self.btn_refresh.setEnabled(False)
        self.list_widget.setEnabled(False)

        # Khởi tạo và chạy Worker
        self._worker = FetchFoldersWorker(remote_name, self._current_path)
        self._worker.data_ready.connect(self._on_data_loaded)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_data_loaded(self, folders: list, error_msg: str):
        """Callback khi Worker hoàn thành"""
        self.btn_refresh.setEnabled(True)
        self.list_widget.setEnabled(True)

        if error_msg:
            QMessageBox.warning(
                self, "Lỗi Rclone", f"Không thể lấy danh sách:\n{error_msg}"
            )
            self.lbl_info.setText("Lỗi khi tải dữ liệu.")
            return

        # Hiển thị dữ liệu
        icon = get_svg_as_icon(
            "folder_icon", 20, fill_color="#FFD700"
        )  # Màu vàng cho folder

        if not folders:
            self.list_widget.addItem("(Thư mục trống)")
        else:
            for folder_name in folders:
                item = QListWidgetItem(icon, folder_name)
                self.list_widget.addItem(item)

        self.lbl_info.setText(f"Tìm thấy {len(folders)} thư mục.")

    def _on_select_folder(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            print(f"Đã chọn: {current_item.text()}")
            # Tại đây bạn có thể emit signal hoặc xử lý logic lưu config
            self.accept()
        else:
            QMessageBox.information(
                self, "Thông báo", "Vui lòng chọn một thư mục trong danh sách."
            )
