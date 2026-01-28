from PySide6.QtGui import QKeySequence, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QWidget, QFrame
from PySide6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QEvent,
    Qt,
)
import sys
from mixins.window import GeneralWindowMixin
from typing import Callable


class MainWindowMixin(QWidget, GeneralWindowMixin):
    def __init__(self):
        super().__init__()
        self._root_shell = QFrame()  # Cửa sổ chính

    def close_app_by_quit(self):
        """Hàm callback thực sự đóng ứng dụng."""
        QApplication.quit()
        sys.exit(0)

    def close_app(self):
        self._animate_close_window(self.close_app_by_quit)

    def set_animate_close_window(self, animate_close_window: Callable):
        """Thiết lập hàm callback đóng ứng dụng với hiệu ứng animation."""
        self._animate_close_window = animate_close_window

    def _add_keyboard_shortcuts(self) -> None:
        """Bắt sự kiện nhấn các tổ hợp phím."""
        # Ctrl + Q (thoát ứng dụng)
        self.shortcut_ctrl_q = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_ctrl_q.activated.connect(self.close_app)

        # Alt + Q (thoát ứng dụng)
        self.shortcut_alt_q = QShortcut(QKeySequence("Alt+Q"), self)
        self.shortcut_alt_q.activated.connect(self.close_app)

    # --- PHẦN XỬ LÝ HIỆU ỨNG ANIMATION ĐÓNG MỞ APP---
    def _animate_open_zoom(self):
        """Hiệu ứng Zoom In khi mở App."""
        # 1. Lấy kích thước chuẩn (đích đến)
        target_rect = self.geometry()

        # 2. Thiết lập trạng thái bắt đầu (Nhỏ hơn và trong suốt)
        start_rect = self._get_center_rect(self, scale_factor=0.95)  # Thu nhỏ 5%
        self.setGeometry(start_rect)
        self.setWindowOpacity(0)

        # 3. Tạo Animation Group (Chạy song song Fade + Resize)
        self._anim_group = QParallelAnimationGroup()

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

        self._anim_group.addAnimation(anim_opacity)
        self._anim_group.addAnimation(anim_geometry)
        self._anim_group.start()

    # --- CẬP NHẬT: Xử lý sự kiện Restore (Mở lại) ---
    def changeEvent(self, event):
        """Xử lý sự kiện thay đổi trạng thái cửa sổ."""
        event_type = event.type()

        if event_type == QEvent.Type.ActivationChange:
            self._root_shell.setProperty("is_focused", self.isActiveWindow())
            self._root_shell.style().unpolish(self._root_shell)
            self._root_shell.style().polish(self._root_shell)

        elif event_type == QEvent.Type.WindowStateChange:
            old_state = event.oldState()
            new_state = self.windowState()

            # CASE 1: RESTORE (Từ Minimized -> Bình thường)
            if (old_state & Qt.WindowState.WindowMinimized) and not (
                new_state & Qt.WindowState.WindowMinimized
            ):
                # Khi restore, chạy animation Zoom In (giống lúc mở App)
                self._animate_open_zoom()

            # CASE 2: MAXIMIZE
            elif new_state & Qt.WindowState.WindowMaximized:
                self._root_shell.setProperty("is_maximized", True)
                layout = self.layout()
                if layout:
                    layout.setContentsMargins(0, 0, 0, 0)

            # CASE 3: NORMAL
            else:
                self._root_shell.setProperty("is_maximized", False)
                # Lưu ý: Nếu bạn có set margin ở app.py, cần restore lại ở đây nếu muốn chuẩn xác 100%

            self._root_shell.style().unpolish(self._root_shell)
            self._root_shell.style().polish(self._root_shell)

        super().changeEvent(event)
