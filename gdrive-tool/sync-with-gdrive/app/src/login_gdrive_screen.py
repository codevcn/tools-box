from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QFrame,
)
from PySide6.QtCore import Qt


class LoginGDriveScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.remote_name_input: QLineEdit
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Thiết lập giao diện chính của dialog."""
        self.setWindowTitle("Đăng nhập Google Drive")
        self.resize(600, 400)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Thêm các section
        main_layout.addWidget(self._create_title_section())
        main_layout.addWidget(self._create_description_section())
        main_layout.addLayout(self._create_input_section())
        main_layout.addStretch()
        main_layout.addLayout(self._create_action_section())

    def _create_title_section(self) -> QLabel:
        """Tạo tiêu đề chính."""
        title = QLabel("Đặt tên cho Kho Lưu Trữ của bạn trên Google Drive")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        
        # Style cho tiêu đề
        font = title.font()
        font.setPointSize(16)
        font.setBold(True)
        title.setFont(font)
        
        return title

    def _create_description_section(self) -> QFrame:
        """Tạo khung mô tả với nền vàng nhạt."""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #FFF9E6;
                border: 1px solid #FFE082;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 12, 12, 12)
        
        description = QLabel(
            "Tên của kho lưu trữ giúp bạn phân biệt các tài khoản Google Drive với nhau "
            "nếu bạn có nhiều tài khoản Google Drive. Ví dụ: bạn có 1 tài khoản Google Drive A "
            "và 1 tài khoản Google Drive B và nhiều tài khoản Google Drive khác nữa."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #000000; background-color: transparent;")
        
        layout.addWidget(description)
        
        return frame

    def _create_input_section(self) -> QVBoxLayout:
        """Tạo section nhập tên remote."""
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        label = QLabel("Tên kho lưu trữ:")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        
        self.remote_name_input = QLineEdit()
        self.remote_name_input.setPlaceholderText(
            "Ví dụ: MyDrive, WorkDrive, PersonalDrive..."
        )
        self.remote_name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        
        layout.addWidget(label)
        layout.addWidget(self.remote_name_input)
        
        return layout

    def _create_action_section(self) -> QVBoxLayout:
        """Tạo section với nút hành động."""
        layout = QVBoxLayout()
        
        login_btn = QPushButton("Tiến hành đăng nhập")
        login_btn.setFixedHeight(44)
        login_btn.clicked.connect(self._on_login_clicked)
        
        # Style cho nút
        font = login_btn.font()
        font.setBold(True)
        login_btn.setFont(font)
        
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        
        layout.addWidget(login_btn)
        
        return layout

    def _on_login_clicked(self) -> None:
        """Xử lý khi người dùng nhấn nút đăng nhập."""
        remote_name = self.remote_name_input.text().strip()
        
        if not remote_name:
            # TODO: Hiển thị thông báo lỗi
            return
        
        # TODO: Thực hiện logic đăng nhập
        print(f"Đăng nhập với remote name: {remote_name}")
