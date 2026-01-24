from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QScrollArea,
    QWidget,
    QFrame,
    QHBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QCursor
from components.button import CustomButton
from data.data_manager import DataManager
from utils.helpers import get_svg_as_icon
from configs.configs import ThemeColors
from components.label import CustomLabel


class RemoteItem(QWidget):
    """Widget hiển thị một remote trong danh sách"""

    clicked = Signal(str)  # Emit remote name khi click

    def __init__(
        self, remote_name: str, is_active: bool = False, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.remote_name = remote_name
        self.is_active = is_active
        self._setup_ui()

    def _setup_ui(self):
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setObjectName("RemoteItemInList")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Icon Google Drive
        icon_label = CustomLabel()
        icon_label.setPixmap(get_svg_as_icon("gdrive_logo_icon", 24, None, None, 3))
        icon_label.setFixedSize(24, 24)
        layout.addWidget(icon_label)

        # Remote name
        name_label = CustomLabel(self.remote_name)
        name_label.setStyleSheet("color: white;")
        name_label.set_font_size(17)
        layout.addWidget(name_label, 1)

        # Check icon (nếu active)
        if self.is_active:
            check_label = CustomLabel()
            check_label.setPixmap(
                get_svg_as_icon("check_icon", 22, None, ThemeColors.MAIN, 3)
            )
            check_label.setFixedSize(22, 22)
            layout.addWidget(check_label)

        # Style
        self.setStyleSheet(
            f"""
            #RemoteItemInList {{
                border-radius: 4px;
                border: 2px solid {ThemeColors.MAIN if self.is_active else ThemeColors.GRAY_BORDER};
            }}
            #RemoteItemInList:hover {{
                background-color: {ThemeColors.GRAY_HOVER};
            }}
        """
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.remote_name)
        super().mousePressEvent(event)


class ActiveRemoteScreen(QDialog):
    """Window hiển thị danh sách remotes để chọn"""

    remote_selected = Signal(str)  # Emit khi user chọn remote

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._data_manager = DataManager()
        self._remotes_layout: QVBoxLayout
        self._setup_ui()
        self._load_remotes()

    def _setup_ui(self):
        self.setWindowTitle("Chọn Kho Lưu Trữ")
        self.resize(600, 450)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title section
        title_section = QFrame()
        title_section.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        title_section.setStyleSheet(f"background-color: {ThemeColors.GRAY_BACKGROUND};")

        title_layout = QVBoxLayout(title_section)
        title_layout.setContentsMargins(12, 8, 12, 8)
        title_layout.setSpacing(8)

        title_label = CustomLabel(
            "Chọn Kho Lưu Trữ", is_bold=True, align=Qt.AlignmentFlag.AlignCenter
        )
        title_label.setStyleSheet("color: white;")
        title_label.set_font_size(16)
        title_layout.addWidget(title_label)

        subtitle_label = CustomLabel(
            "Chọn tài khoản Google Drive để đồng bộ dữ liệu của bạn",
            align=Qt.AlignmentFlag.AlignCenter,
        )
        subtitle_label.setStyleSheet("color: #b8b8b8;")
        subtitle_label.set_font_size(14)
        title_layout.addWidget(subtitle_label)

        main_layout.addWidget(title_section)

        # Scrollable area for remotes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: #2d2d2d;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4d4d4d;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5d5d5d;
            }
        """
        )

        # Container widget for remotes
        remotes_container = QFrame()
        self._remotes_layout = QVBoxLayout(remotes_container)
        self._remotes_layout.setContentsMargins(8, 8, 8, 8)
        self._remotes_layout.setSpacing(8)

        # OK button
        ok_btn_layout = QHBoxLayout()
        ok_btn_layout.setContentsMargins(8, 0, 8, 8)
        ok_btn_layout.setSpacing(8)
        ok_button = CustomButton("Đóng", font_size=16, is_bold=True, fixed_height=40)
        ok_button.setIcon(
            get_svg_as_icon("check_icon", 24, None, "black", 3, margins=(0, 0, 8, 0))
        )
        ok_button.setIconSize(QSize(24, 24))
        ok_button.on_clicked(self.accept)
        ok_button.setStyleSheet(
            f"""
            CustomButton {{
                background-color: {ThemeColors.MAIN};
                color: black;
                border-radius: 8px;
            }}
        """
        )
        ok_btn_layout.addWidget(ok_button)

        scroll_area.setWidget(remotes_container)
        main_layout.addWidget(scroll_area, 1)
        main_layout.addLayout(ok_btn_layout)

        # Style
        self.setStyleSheet(
            """
            QDialog {
                background-color: #2d2d2d;
            }
        """
        )

    def _load_remotes(self):
        """Load danh sách remotes từ data manager"""
        # Get remotes
        config = self._data_manager.get_entire_config()
        remotes = config.get("remotes", [])
        active_remote = config.get("active_remote")

        if not remotes:
            # Show empty state
            empty_label = CustomLabel("Chưa có kho lưu trữ nào.\nVui lòng đăng nhập.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #b8b8b8;")
            empty_label.set_font_size(16)
            self._remotes_layout.addWidget(empty_label)
            return

        # Add remote items
        for remote in remotes:
            is_active = remote == active_remote
            item = RemoteItem(remote, is_active, self)
            item.clicked.connect(self._on_remote_picked)
            self._remotes_layout.addWidget(item)

        self._remotes_layout.addStretch()

    def _on_remote_picked(self, remote_name: str):
        """Xử lý khi user click vào một remote"""
        # Update active remote
        self._data_manager.save_active_remote(remote_name)

        # Emit signal
        self.remote_selected.emit(remote_name)

        # Close dialog
        self.accept()
