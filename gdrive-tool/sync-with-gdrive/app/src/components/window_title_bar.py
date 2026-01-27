from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QFrame,
)
from PySide6.QtCore import Qt
from configs.configs import ThemeColors
from components.label import CustomLabel
from components.button import CustomButton
from utils.helpers import get_svg_as_icon


class CustomWindowTitleBar(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(40)  # Chiều cao thanh tiêu đề
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setObjectName("CustomWindowTitleBar")
        self.setStyleSheet(
            f"""
            #CustomWindowTitleBar {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border-top-right-radius: 7px;
                border-top-left-radius: 7px;
            }}
        """
        )  # Màu nền thanh tiêu đề

        # 1. Tiêu đề
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        self_title_logo = CustomLabel()
        self_title_logo.setFixedSize(20, 20)
        self_title_logo.setPixmap(get_svg_as_icon("app_logo", 20, None, None, 2))
        self._title_label = CustomLabel("Đồng bộ với Google Drive")
        self._title_label.setObjectName("CustomWindowTitleLabel")
        self._title_label.setStyleSheet(
            """
            #CustomWindowTitleLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-top-left-radius: 7px;
            }
        """
        )
        title_layout.addWidget(self_title_logo)
        title_layout.addWidget(self._title_label)
        self._layout.addLayout(title_layout)
        self._layout.addStretch()  # Đẩy các nút về bên phải

        # 2. Các nút điều khiển (Minimize, Close)
        # Style chung cho nút
        btn_style = """
            #WindowTitleBarButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 16px;
                width: 50px;
                height: 40px;
                border-top-right-radius: 7px;
            }
            #WindowTitleBarButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """

        # Nút Close đỏ đặc trưng khi hover
        close_btn_style = (
            btn_style
            + """
            #WindowTitleBarButton:hover {
                background-color: #e81123; 
            }
        """
        )

        self._btn_minimize = CustomButton("─")
        self._btn_minimize.setObjectName("WindowTitleBarButton")
        self._btn_minimize.setStyleSheet(btn_style)
        self._btn_minimize.clicked.connect(self.window().showMinimized)

        self._btn_close = CustomButton("✕")
        self._btn_close.setObjectName("WindowTitleBarButton")
        self._btn_close.setStyleSheet(close_btn_style)
        self._btn_close.clicked.connect(self.window().close)

        self._layout.addWidget(self._btn_minimize)
        self._layout.addWidget(self._btn_close)

        # Biến để xử lý việc kéo thả cửa sổ
        self._start_pos = None

    # --- Xử lý kéo thả cửa sổ ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_pos = (
                event.globalPosition().toPoint()
                - self.window().frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._start_pos:
            self.window().move(event.globalPosition().toPoint() - self._start_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._start_pos = None
