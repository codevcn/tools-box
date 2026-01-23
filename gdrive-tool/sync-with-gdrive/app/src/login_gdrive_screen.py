from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QFrame,
    QSizePolicy,
    QLayout,
)
from PySide6.QtCore import Qt, QObject, Signal, QProcess, QSize
from components.popup import CustomPopup
from data.data_manager import DataManager
from utils.helpers import get_svg_file_path, svg_to_pixmap
from configs.configs import ThemeColors
from components.label import AutoHeightLabel, CustomLabel
from PySide6.QtGui import QFontMetrics
from components.button import CustomButton


class RcloneDriveSetup(QObject):
    log = Signal(str)
    done = Signal(bool, str)  # (ok, message)

    def __init__(self, rclone_exe: str = "rclone", parent=None):
        super().__init__(parent)
        self.rclone_exe = rclone_exe
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        self.proc.readyReadStandardOutput.connect(self._on_ready_read)
        self.proc.finished.connect(self._on_finished)

        self._queue: list[list[str]] = []
        self._current_step = ""

    def setup_drive_remote(self, remote_name: str, *, scope: str = "drive") -> None:
        # tạo remote (không token)
        # rồi reconnect để rclone tự login + lưu token
        self._queue = [
            ["config", "create", remote_name, "drive", f"scope={scope}"],
            ["config", "reconnect", f"{remote_name}:"],
        ]
        self._run_next()

    def _run_next(self) -> None:
        if not self._queue:
            self.done.emit(True, "Remote đã được tạo và đăng nhập thành công.")
            return

        args = self._queue.pop(0)
        self._current_step = " ".join(args)
        self.log.emit(f">>> rclone {self._current_step}")
        self.proc.start(self.rclone_exe, args)

        if not self.proc.waitForStarted(3000):
            self.done.emit(
                False, "Không chạy được rclone. Kiểm tra PATH hoặc rclone_exe."
            )

    def _on_ready_read(self) -> None:
        text = bytes(self.proc.readAllStandardOutput().data()).decode(
            "utf-8", errors="replace"
        )
        if not text.strip():
            return
        self.log.emit(f">>> {text.rstrip()}")
        # detect câu hỏi refresh token từ rclone
        if "Already have a token - refresh?" in text:
            self.log.emit(">>> Auto-answer: Yes (refresh token)")
            self.proc.write(b"y\n")

    def _on_finished(self, exit_code: int, _status) -> None:
        if exit_code != 0:
            # lỗi khi chạy step hiện tại
            self.done.emit(
                False,
                f"Lỗi khi chạy: rclone {self._current_step} (exit_code={exit_code})",
            )
            self._queue = []
        else:
            # chạy step tiếp theo
            self._run_next()


class LoginGDriveScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager: DataManager = DataManager()
        self.remote_name_input: QLineEdit
        self.action_button: CustomButton
        self.rclone_setup: RcloneDriveSetup = RcloneDriveSetup(parent=self)
        self.rclone_setup.log.connect(self._on_login_log)
        self.rclone_setup.done.connect(self._on_login_done)
        self._pending_remote_name: str | None = None
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
            "Giải thích: Tên của kho lưu trữ là 1 văn bản giúp bạn phân biệt các tài khoản Google Drive "
            "với nhau nếu bạn có nhiều tài khoản Google Drive. Ví dụ: bạn có 1 tài khoản Google Drive A "
            "và 1 tài khoản Google Drive B và nhiều tài khoản Google Drive khác nữa."
        )
        description.setStyleSheet("color: #000000; background-color: transparent;")
        description.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(description)

        return frame

    def _handle_input_change(self, text: str) -> None:
        """Xử lý khi người dùng thay đổi nội dung trong ô nhập."""
        if text.strip():
            self.action_button.setEnabled(True)
            self.action_button.setStyleSheet(
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
            self.action_button.setIcon(
                svg_to_pixmap(
                    get_svg_file_path("double_check_icon.svg")[0],
                    30,
                    None,
                    "#000000",
                    3,
                    (0, 0, 8, 0),
                )
            )
        else:
            self.action_button.setEnabled(False)
            self.action_button.setStyleSheet(
                """
                CustomButton {
                    background-color: #616060;
                    color: #b8b8b8;
                    border: none;
                    border-radius: 4px;
                }
            """
            )
            self.action_button.setIcon(
                svg_to_pixmap(
                    get_svg_file_path("double_check_icon.svg")[0],
                    30,
                    None,
                    "#b8b8b8",
                    3,
                    (0, 0, 8, 0),
                )
            )

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

        self.remote_name_input = QLineEdit()
        self.remote_name_input.textChanged.connect(self._handle_input_change)
        self.remote_name_input.setPlaceholderText(
            "Ví dụ: Drive của tôi / Google Drive A / google-drive-a..."
        )
        self.remote_name_input.setStyleSheet(
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
        layout.addWidget(self.remote_name_input)

        return layout

    def _create_action_section(self) -> QVBoxLayout:
        """Tạo section với nút hành động."""
        layout = QVBoxLayout()

        self.action_button = CustomButton("Tiến hành đăng nhập", default_enabled=False)
        self.action_button.setFixedHeight(44)
        self.action_button.clicked.connect(self._on_login_start)
        # Style cho nút
        self._handle_input_change("")
        self.action_button.setIconSize(QSize(30, 30))
        font = self.action_button.font()
        font.setBold(True)
        self.action_button.setFont(font)

        layout.addWidget(self.action_button)
        return layout

    def _do_save_remote_data(self, remote_name: str) -> None:
        """Lưu remote data do app quản lý (KHÔNG token)."""
        self.data_manager.add_new_remote(remote_name)
        self.data_manager.save_active_remote(remote_name)

    def _on_login_log(self, text: str):
        print(f">>> rclone log: {text}")

    def _on_login_done(self, ok: bool, msg: str):
        if ok and self._pending_remote_name:
            self._do_save_remote_data(self._pending_remote_name)
            self.accept()
        else:
            popup = CustomPopup(
                self,
                title="Lỗi",
                text=msg,
                icon_pixmap=svg_to_pixmap(
                    get_svg_file_path("warn_icon.svg")[0],
                    35,
                    None,
                    "#ff0000",
                    margins=(0, 0, 8, 0),
                ),
            )
            popup.exec_and_get()
            self._pending_remote_name = None
            self.reject()
        print(f">>> rclone done: ok={ok}, msg={msg}")

    def _do_login(self, remote_name: str) -> None:
        """Bắt đầu quá trình đăng nhập Google Drive qua rclone."""
        self.rclone_setup.setup_drive_remote(remote_name, scope="drive")

    def _on_login_start(self) -> None:
        """Xử lý khi người dùng nhấn nút đăng nhập."""
        self._pending_remote_name = self.remote_name_input.text().strip()

        if not self._pending_remote_name:
            popup = CustomPopup(
                self,
                title="Lỗi",
                text="Vui lòng nhập tên kho lưu trữ trước khi đăng nhập.",
                icon_pixmap=svg_to_pixmap(
                    get_svg_file_path("warn_icon.svg")[0],
                    35,
                    None,
                    "#ff0000",
                    margins=(0, 0, 8, 0),
                ),
            )
            popup.exec_and_get()
            return

        self._do_login(self._pending_remote_name)
