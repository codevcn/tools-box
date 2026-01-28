from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QFrame,
)
from ..mixins.window import GeneralWindowMixin
from ..configs.configs import ThemeColors
from ..components.label import CustomLabel
from ..components.button import CustomButton
from ..utils.helpers import get_svg_as_icon
from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    Qt,
)
from typing import Callable


class CustomWindowTitleBar(QFrame, GeneralWindowMixin):
    def __init__(
        self,
        root_shell: QWidget,
        close_app_handler: Callable,
        parent: QWidget,
    ):
        super().__init__(parent)
        self._root_shell = root_shell
        self._close_app_handler = close_app_handler
        self._parent = parent

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
        self._btn_minimize.on_clicked(self._animate_minimize_window)

        self._btn_close = CustomButton("✕")
        self._btn_close.setObjectName("WindowTitleBarButton")
        self._btn_close.setStyleSheet(close_btn_style)
        self._btn_close.on_clicked(
            lambda: self._animate_close_window(self._close_app_handler)
        )

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

    def _animate_close_window(self, callback):
        """Hiệu ứng Zoom Out khi đóng App."""
        # 1. Đích đến (Nhỏ lại và mờ đi)
        end_rect = self._get_center_rect(self._parent, scale_factor=0.95)

        self._anim_group = QParallelAnimationGroup()

        # Animation 1: Fade Out
        anim_opacity = QPropertyAnimation(self._parent, b"windowOpacity")
        anim_opacity.setDuration(200)  # Nhanh hơn lúc mở chút
        anim_opacity.setStartValue(1)
        anim_opacity.setEndValue(0)
        anim_opacity.setEasingCurve(QEasingCurve.Type.InCubic)

        # Animation 2: Zoom Out
        anim_geometry = QPropertyAnimation(self._parent, b"geometry")
        anim_geometry.setDuration(200)
        anim_geometry.setStartValue(self._parent.geometry())
        anim_geometry.setEndValue(end_rect)
        anim_geometry.setEasingCurve(QEasingCurve.Type.InCubic)

        self._anim_group.addAnimation(anim_opacity)
        self._anim_group.addAnimation(anim_geometry)

        # Khi chạy xong thì mới gọi hàm thoát (callback)
        self._anim_group.finished.connect(callback)
        self._anim_group.start()

    # --- THÊM MỚI: Logic Minimize có Animation ---
    def _animate_minimize_window(self):
        """Hàm gọi khi nhấn nút Minimize."""
        # 1. Lưu lại geometry hiện tại (để khi restore không bị lỗi kích thước)
        self._saved_geo_before_min = self._parent.geometry()

        # 2. Chạy animation Zoom Out (tái sử dụng animation đóng app)
        # Khi animation chạy xong, nó sẽ gọi hàm _on_minimize_finished
        self._animate_close_window(self._on_minimize_finished)

    def _on_minimize_finished(self):
        """Được gọi khi animation zoom nhỏ đã chạy xong."""
        # 3. Thực hiện minimize thật sự
        self._parent.showMinimized()

        # 4. Quan trọng: Reset lại trạng thái cửa sổ về chuẩn (ngầm)
        # Để khi người dùng nhấn mở lại từ Taskbar, cửa sổ đã có size đúng
        if self._saved_geo_before_min:
            self._parent.setGeometry(self._saved_geo_before_min)

        # Đặt Opacity về 0 để chuẩn bị cho animation "Zoom In" lúc Restore
        # (Giúp tránh hiện tượng nháy hình khi cửa sổ hiện lên lại)
        self._parent.setWindowOpacity(0)
