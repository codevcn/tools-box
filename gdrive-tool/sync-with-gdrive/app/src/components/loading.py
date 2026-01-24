import sys
import math
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QBrush, QColor, QPaintEvent, QShowEvent, QHideEvent
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton


class LoadingDots(QWidget):
    def __init__(
        self,
        parent=None,
        dot_count=3,
        dot_size=16,
        color="#3498db",
        spacing=8,
        speed_factor=1.0,  # Thay đổi: Dùng hệ số nhân để chỉnh tốc độ (1.0 là mặc định)
    ):
        super().__init__(parent)

        # --- Properties ---
        self._dot_count = dot_count
        self._dot_size = dot_size
        self._color = QColor(color)
        self._spacing = spacing
        self._max_scale = 1.3  # Scale đỉnh là 130%

        # Speed config: Base step (0.15) * speed_factor
        self._base_step = 0.15
        self._speed_factor = speed_factor

        # --- Animation State ---
        self._counter = 0.0
        self._is_running = False  # Trạng thái logic (người dùng muốn chạy hay không)

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 FPS
        self._timer.timeout.connect(self._on_timeout)

        # Quan trọng: Set size policy để widget không bị co giãn lung tung
        self.setSizePolicy(
            self.sizePolicy().Policy.Fixed, self.sizePolicy().Policy.Fixed
        )
        self.updateGeometry()

    # --- Public API (Control) ---
    def start(self):
        """Bắt đầu animation."""
        self._is_running = True
        if self.isVisible():
            self._timer.start()
        self.update()  # Vẽ lại ngay lập tức

    def stop(self):
        """Dừng animation."""
        self._is_running = False
        self._timer.stop()
        self.update()

    def set_speed(self, factor: float):
        """Điều chỉnh tốc độ runtime. 1.0 là bình thường, 2.0 là nhanh gấp đôi."""
        self._speed_factor = factor

    # --- Event Handlers (Resource Optimization) ---
    def showEvent(self, event: QShowEvent):
        """Chỉ chạy timer khi widget thực sự hiện lên màn hình."""
        super().showEvent(event)
        if self._is_running:
            self._timer.start()

    def hideEvent(self, event: QHideEvent):
        """Tự động tắt timer khi widget bị ẩn để tiết kiệm CPU."""
        super().hideEvent(event)
        self._timer.stop()

    def _on_timeout(self):
        # Tăng counter dựa trên speed factor
        self._counter += self._base_step * self._speed_factor
        self.update()

    # --- Geometry & Layout ---
    def sizeHint(self):
        """Tính toán kích thước chính xác để không bị cắt hình."""
        max_dot_w = self._dot_size * self._max_scale
        total_width = (max_dot_w * self._dot_count) + (
            self._spacing * (self._dot_count - 1)
        )
        # Thêm padding nhỏ (2px) để an toàn
        return QSize(int(total_width + 2), int(max_dot_w + 2))

    def update_properties(
        self, dot_count=None, dot_size=None, spacing=None, color=None
    ):
        """Hàm helper để update nhiều thuộc tính cùng lúc."""
        if dot_count is not None:
            self._dot_count = dot_count
        if dot_size is not None:
            self._dot_size = dot_size
        if spacing is not None:
            self._spacing = spacing
        if color is not None:
            self._color = QColor(color)

        # CỰC KỲ QUAN TRỌNG: Báo cho Layout biết size đã đổi
        self.updateGeometry()
        self.update()

    # --- Painting ---
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Center vertical
        center_y = self.height() / 2
        # Tính toán lại max width dot hiện tại
        max_dot_w = self._dot_size * self._max_scale

        # Vẽ từng dot
        for i in range(self._dot_count):
            scale_factor = 1.0

            # Chỉ tính toán scale khi đang chạy
            if self._is_running:
                # Math: Sin wave + Phase shift (i * 0.7)
                wave = math.sin(self._counter - (i * 0.7))
                # Normalize sin (-1 to 1) -> (0 to 1)
                norm = (wave + 1) / 2

                # Easing simulation (làm chuyển động nảy hơn)
                # Nếu muốn scale mượt đều thì dùng norm trực tiếp
                scale_factor = 1.0 + (self._max_scale - 1.0) * norm

            # Tính toán kích thước và vị trí
            current_size = self._dot_size * scale_factor

            # Tính x: (vị trí i) + (offset center để dot phình ra từ tâm)
            x_base = i * (max_dot_w + self._spacing)
            # Dịch vào giữa ô chứa của nó
            x_center_offset = (max_dot_w - current_size) / 2

            draw_x = x_base + x_center_offset
            draw_y = center_y - (current_size / 2)

            painter.drawEllipse(
                int(draw_x), int(draw_y), int(current_size), int(current_size)
            )
