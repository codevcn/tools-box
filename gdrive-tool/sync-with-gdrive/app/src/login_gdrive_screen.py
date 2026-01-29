from PySide6.QtWidgets import (
    QVBoxLayout,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QSize, Signal
from .data.rclone_configs_manager import RCloneConfigManager
from .components.announcement import CustomAnnounce
from .data.data_manager import UserDataManager
from .utils.helpers import get_svg_as_icon
from .configs.configs import ThemeColors
from .components.label import AutoHeightLabel, CustomLabel
from PySide6.QtGui import QFontMetrics
from .components.button import CustomButton
from .workers.authorize_gdrive_worker import RcloneDriveSetup
from enum import Enum
from .mixins.keyboard_shortcuts import KeyboardShortcutsDialogMixin


class LoginResult(Enum):
    SUCCESS = 1  # user cấp quyền thành công
    CANCELLED = 2  # user hủy quá trình login
    INTERRUPTED = 3  # user đóng tab trình duyệt trong quá trình login


class LoginGDriveScreen(KeyboardShortcutsDialogMixin):
    login_result = Signal(LoginResult, str, str)  # (result, remote_name, error_msg)

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._data_manager: UserDataManager = UserDataManager()
        self._remote_name_input: QLineEdit
        self._action_button: CustomButton
        self._rclone_setup: RcloneDriveSetup = RcloneDriveSetup(
            rclone_exe=RCloneConfigManager.rclone_executable_path(), parent=self
        )
        self._rclone_setup.log.connect(self._on_login_log)
        self._rclone_setup.done.connect(self._on_login_done)
        self._pending_remote_name: str | None = None
        self._action_btn_svg_pixmap_enabled = get_svg_as_icon(
            "double_check_icon",
            30,
            None,
            "#000000",
            3,
            (0, 0, 8, 0),
        )
        self._action_btn_svg_pixmap_disabled = get_svg_as_icon(
            "double_check_icon",
            30,
            None,
            "#b8b8b8",
            3,
            (0, 0, 8, 0),
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Thiết lập giao diện chính của dialog."""
        self.setWindowTitle("Đăng nhập Google Drive")
        self.setMinimumWidth(600)

        main_layout = QVBoxLayout(self)
        main_layout.setSizeConstraints(
            QLayout.SizeConstraint.SetMaximumSize, QLayout.SizeConstraint.SetFixedSize
        )

        # Thêm các section
        main_layout.addWidget(self._create_title_section())
        main_layout.addWidget(self._create_description_section())
        main_layout.addLayout(self._create_input_section())
        main_layout.addLayout(self._create_action_section())

    def _create_title_section(self) -> CustomLabel:
        """Tạo tiêu đề chính."""
        title = CustomLabel("Đặt tên cho Kho Lưu Trữ của bạn trên Google Drive")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        fm = QFontMetrics(title.font())
        title.setFixedHeight(fm.height() + 8)

        # Style cho tiêu đề
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)

        return title

    def _create_description_section(self) -> QFrame:
        """Tạo khung mô tả với nền vàng nhạt."""
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        frame.setStyleSheet(
            """
            QFrame {
                background-color: #FFF9E6;
                border: 1px solid #FFE082;
                border-radius: 8px;
            }
        """
        )

        layout = QVBoxLayout(frame)
        layout.setSizeConstraints(
            QLayout.SizeConstraint.SetMaximumSize, QLayout.SizeConstraint.SetFixedSize
        )
        layout.setContentsMargins(4, 4, 4, 4)

        description = AutoHeightLabel(
            "Giải thích: Tên của kho lưu trữ giúp bạn phân biệt các tài khoản Google Drive với nhau "
            "nếu bạn có nhiều tài khoản Google Drive. Ví dụ: bạn có 1 tài khoản Google Drive A "
            "và 1 tài khoản Google Drive B và nhiều tài khoản Google Drive khác nữa."
        )
        description.setStyleSheet("color: #000000; background-color: transparent;")
        description.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(description)

        return frame

    def _handle_input_change(self, text: str) -> None:
        """Xử lý khi người dùng thay đổi nội dung trong ô nhập."""
        if text.strip():
            self._action_button.setEnabled(True)
            self._action_button.setStyleSheet(
                f"""
                CustomButton {{
                    background-color: {ThemeColors.MAIN};
                    border: none;
                    border-radius: 4px;
                    color: black;
                }}
                CustomButton:hover {{
                    background-color: {ThemeColors.LIGHT_MAIN};
                }}
                CustomButton:pressed {{
                    background-color: {ThemeColors.DARK_MAIN};
                }}
            """
            )
            self._action_button.setIcon(self._action_btn_svg_pixmap_enabled)
        else:
            self._action_button.setEnabled(False)
            self._action_button.setStyleSheet(
                """
                CustomButton {
                    background-color: #616060;
                    color: #b8b8b8;
                    border: none;
                    border-radius: 4px;
                }
            """
            )
            self._action_button.setIcon(self._action_btn_svg_pixmap_disabled)

    def _create_input_section(self) -> QVBoxLayout:
        """Tạo section nhập tên remote."""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 8, 0, 4)

        label = CustomLabel("Tên kho lưu trữ:")
        label.setContentsMargins(6, 0, 0, 0)
        font = label.font()
        font.setBold(True)
        label.setFont(font)

        self._remote_name_input = QLineEdit()
        self._remote_name_input.textChanged.connect(self._handle_input_change)
        self._remote_name_input.setPlaceholderText(
            "Ví dụ: Drive của tôi hoặc Google Drive A hoặc google-drive-a..."
        )
        self._remote_name_input.setStyleSheet(
            f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid #969696;
                border-radius: 4px;
            }}
            QLineEdit:focus {{
                border: 2px solid {ThemeColors.MAIN};
            }}
        """
        )

        layout.addWidget(label)
        layout.addWidget(self._remote_name_input)

        return layout

    def _create_action_section(self) -> QVBoxLayout:
        """Tạo section với nút hành động."""
        layout = QVBoxLayout()

        self._action_button = CustomButton("Tiến hành đăng nhập", default_enabled=False)
        self._action_button.setFixedHeight(44)
        self._action_button.clicked.connect(self._on_login_start)
        # Style cho nút
        self._handle_input_change("")
        self._action_button.setIconSize(QSize(30, 30))
        font = self._action_button.font()
        font.setBold(True)
        self._action_button.setFont(font)

        layout.addWidget(self._action_button)
        return layout

    def _do_save_remote_data(self, remote_name: str) -> None:
        """Lưu remote data do app quản lý (KHÔNG token)."""
        self._data_manager.add_new_remote(remote_name)
        self._data_manager.save_active_remote(remote_name)

    def _on_login_log(self, text: str):
        print(f">>> rclone log: {text}")

    def _on_login_done(self, ok: bool, msg: str):
        if ok and self._pending_remote_name:
            self._do_save_remote_data(self._pending_remote_name)
            self.login_result.emit(LoginResult.SUCCESS, self._pending_remote_name, "")
            self.accept()
        else:
            CustomAnnounce.warn(
                self,
                title="Lỗi",
                message=msg,
            )
        print(
            f">>> rclone done: ok={ok}, remote={self._pending_remote_name}, msg={msg}"
        )

    def _do_login(self, remote_name: str) -> None:
        """Bắt đầu quá trình đăng nhập Google Drive qua rclone."""
        self._rclone_setup.setup_drive_remote(remote_name, scope="drive")

    def _on_login_start(self) -> None:
        """Xử lý khi người dùng nhấn nút đăng nhập."""
        self._pending_remote_name = self._remote_name_input.text().strip()

        if not self._pending_remote_name:
            CustomAnnounce.warn(
                self,
                title="Lỗi",
                message="Vui lòng nhập tên kho lưu trữ trước khi đăng nhập.",
            )
            return

        self._do_login(self._pending_remote_name)

    def closeEvent(self, event):
        """Xử lý khi dialog bị đóng (user nhấn nút đóng)."""
        if self._rclone_setup.is_running():
            self._rclone_setup.cancel_process(wait_ms=200)
        event.accept()
