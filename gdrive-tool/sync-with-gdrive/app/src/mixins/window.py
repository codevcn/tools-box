from PySide6.QtCore import QRect
from PySide6.QtWidgets import QWidget


class GeneralWindowMixin:
    def _get_center_rect(self, window_widget: QWidget, scale_factor=0.9) -> QRect:
        """Tính toán hình chữ nhật thu nhỏ nằm giữa tâm cửa sổ hiện tại."""
        current_rect = window_widget.geometry()
        width = current_rect.width()
        height = current_rect.height()

        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        # Tính toán vị trí x, y để hình chữ nhật mới nằm giữa tâm
        new_x = current_rect.x() + (width - new_width) // 2
        new_y = current_rect.y() + (height - new_height) // 2

        return QRect(new_x, new_y, new_width, new_height)
