from PySide6.QtGui import QKeySequence, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QWidget, QFrame
from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QRect,
    QEvent,
    Qt,
)
import sys


class AppWindowMixin(QWidget):
    def __init__(self):
        super().__init__()
        self._root_shell = QFrame()  # Cửa sổ chính

    def _close_app_callback(self):
        """Hàm callback thực sự đóng ứng dụng."""
        QApplication.quit()
        sys.exit(0)

    def _close_app(self) -> None:
        """Đóng ứng dụng."""
        self._animate_close_zoom(self._close_app_callback)

    def _add_keyboard_shortcuts(self) -> None:
        """Bắt sự kiện nhấn các tổ hợp phím."""
        # Ctrl + Q (thoát ứng dụng)
        self.shortcut_ctrl_q = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_ctrl_q.activated.connect(self._close_app)

        # Alt + Q (thoát ứng dụng)
        self.shortcut_alt_q = QShortcut(QKeySequence("Alt+Q"), self)
        self.shortcut_alt_q.activated.connect(self._close_app)

    def changeEvent(self, event):
        """Xử lý sự kiện thay đổi trạng thái cửa sổ."""
        event_type = event.type()

        if event_type == QEvent.Type.ActivationChange:
            self._root_shell.setProperty("is_focused", self.isActiveWindow())
            self._root_shell.style().unpolish(self._root_shell)
            self._root_shell.style().polish(self._root_shell)

        # Xử lý khi Maximize: Bỏ bo góc và viền đi cho liền mạch
        elif event_type == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMaximized:
                self._root_shell.setProperty("is_maximized", True)
                # Khi maximize, set margin về 0 để full màn hình
                window_layout = self.layout()
                if window_layout:
                    window_layout.setContentsMargins(0, 0, 0, 0)
            else:
                self._root_shell.setProperty("is_maximized", False)
                # Khi restore, trả lại margin (nếu app.py có set) hoặc giữ nguyên 0

            self._root_shell.style().unpolish(self._root_shell)
            self._root_shell.style().polish(self._root_shell)

        super().changeEvent(event)

    # --- PHẦN XỬ LÝ HIỆU ỨNG ANIMATION ĐÓNG MỞ APP---
    def _get_center_rect(self, scale_factor=0.9) -> QRect:
        """Tính toán hình chữ nhật thu nhỏ nằm giữa tâm cửa sổ hiện tại."""
        current_rect = self.geometry()
        width = current_rect.width()
        height = current_rect.height()

        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        # Tính toán vị trí x, y để hình chữ nhật mới nằm giữa tâm
        new_x = current_rect.x() + (width - new_width) // 2
        new_y = current_rect.y() + (height - new_height) // 2

        return QRect(new_x, new_y, new_width, new_height)

    def _animate_open_zoom(self):
        """Hiệu ứng Zoom In khi mở App."""
        # 1. Lấy kích thước chuẩn (đích đến)
        target_rect = self.geometry()

        # 2. Thiết lập trạng thái bắt đầu (Nhỏ hơn và trong suốt)
        start_rect = self._get_center_rect(scale_factor=0.95)  # Thu nhỏ 5%
        self.setGeometry(start_rect)
        self.setWindowOpacity(0)

        # 3. Tạo Animation Group (Chạy song song Fade + Resize)
        self.anim_group = QParallelAnimationGroup()

        # Animation 1: Fade In (Mờ -> Rõ)
        anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        anim_opacity.setDuration(250)  # 250ms
        anim_opacity.setStartValue(0)
        anim_opacity.setEndValue(1)
        anim_opacity.setEasingCurve(QEasingCurve.Type.OutCubic)  # Gia tốc mượt

        # Animation 2: Zoom In (Nhỏ -> To)
        anim_geometry = QPropertyAnimation(self, b"geometry")
        anim_geometry.setDuration(250)
        anim_geometry.setStartValue(start_rect)
        anim_geometry.setEndValue(target_rect)
        anim_geometry.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_group.addAnimation(anim_opacity)
        self.anim_group.addAnimation(anim_geometry)
        self.anim_group.start()

    def _animate_close_zoom(self, callback):
        """Hiệu ứng Zoom Out khi đóng App."""
        # 1. Đích đến (Nhỏ lại và mờ đi)
        end_rect = self._get_center_rect(scale_factor=0.95)

        self.anim_group = QParallelAnimationGroup()

        # Animation 1: Fade Out
        anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        anim_opacity.setDuration(200)  # Nhanh hơn lúc mở chút
        anim_opacity.setStartValue(1)
        anim_opacity.setEndValue(0)
        anim_opacity.setEasingCurve(QEasingCurve.Type.InCubic)

        # Animation 2: Zoom Out
        anim_geometry = QPropertyAnimation(self, b"geometry")
        anim_geometry.setDuration(200)
        anim_geometry.setStartValue(self.geometry())
        anim_geometry.setEndValue(end_rect)
        anim_geometry.setEasingCurve(QEasingCurve.Type.InCubic)

        self.anim_group.addAnimation(anim_opacity)
        self.anim_group.addAnimation(anim_geometry)

        # Khi chạy xong thì mới gọi hàm thoát (callback)
        self.anim_group.finished.connect(callback)
        self.anim_group.start()
