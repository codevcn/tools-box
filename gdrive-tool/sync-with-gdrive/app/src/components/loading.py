import math
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QBrush, QColor, QPaintEvent, QShowEvent, QHideEvent
from PySide6.QtWidgets import (
    QWidget,
)


class LoadingDots(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        dot_count=3,
        dot_size=12,
        color='#000000',
        spacing=8,
        speed_factor=1.0,
        max_scale=1.4,
        stagger_delay=150,  # Mặc định delay 150ms
    ):
        super().__init__(parent)

        # --- Properties ---
        self._dot_count = dot_count
        self._dot_size = dot_size
        self._color = QColor(color)
        self._spacing = spacing
        self._max_scale = max_scale
        self._stagger_delay = stagger_delay

        # Speed config
        # Base step càng lớn thì tốc độ "nảy" của 1 dot càng nhanh
        self._base_step = 0.15
        self._speed_factor = speed_factor

        # --- Calculated State ---
        self._delay_rad = 0.0  # Delay quy đổi ra radian
        self._cycle_rad = 0.0  # Tổng chiều dài vòng lặp (radian)
        self._pulse_rad = math.pi  # Một nhịp nảy là PI (0 -> 1 -> 0)

        self._recalc_params()

        # --- Animation State ---
        self._counter = 0.0
        self._is_running = False

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 FPS
        self._timer.timeout.connect(self._on_timeout)

        self.setSizePolicy(
            self.sizePolicy().Policy.Fixed, self.sizePolicy().Policy.Fixed
        )
        self.updateGeometry()

    def _recalc_params(self):
        """
        Tính toán lại các thông số vật lý của animation.
        Logic:
        1. Tính xem mỗi milisecond tương ứng bao nhiêu đơn vị 'step' (radian).
        2. Tính tổng chu kỳ sao cho Dot 1 phải đợi Dot N xong mới chạy.
        """
        # Tốc độ tăng counter mỗi frame (16ms)
        step_per_frame = self._base_step * self._speed_factor

        # 1. Quy đổi Delay (ms) -> Radian
        # Delay bao nhiêu frame?
        frames_delay = self._stagger_delay / 16.0
        self._delay_rad = frames_delay * step_per_frame

        # 2. Tính tổng chu kỳ (Cycle Length)
        # Dot cuối cùng bắt đầu tại: (N-1) * delay
        # Dot cuối cùng kết thúc tại: Start + Pulse_Width (PI)
        last_dot_finish_time = (
            (self._dot_count - 1) * self._delay_rad
        ) + self._pulse_rad

        # Tổng chu kỳ phải ÍT NHẤT bằng lúc dot cuối kết thúc.
        # Thêm một chút padding (0.5) để animation thở được một chút trước khi lặp lại
        self._cycle_rad = last_dot_finish_time + 0.5

    # --- Public API ---
    def start(self):
        self._is_running = True
        if self.isVisible():
            self._timer.start()
        self.update()

    def stop(self):
        self._is_running = False
        self._timer.stop()
        self.update()

    def update_properties(
        self,
        max_scale: float | None = None,
        stagger_delay: int | None = None,
        speed_factor: float | None = None,
        color: str | None = None,
        dot_size: int | None = None,
    ):
        need_recalc = False

        if color is not None:
            self._color = QColor(color)

        if max_scale is not None:
            self._max_scale = max_scale
            self.updateGeometry()

        if speed_factor is not None:
            self._speed_factor = speed_factor
            need_recalc = True

        if stagger_delay is not None:
            self._stagger_delay = stagger_delay
            need_recalc = True

        if dot_size is not None:
            self._dot_size = dot_size
            need_recalc = (
                True  # Dot count/size đổi có thể ảnh hưởng (nếu logic phức tạp hơn)
            )
            self.updateGeometry()

        if need_recalc:
            self._recalc_params()

        self.update()

    # --- Event Handlers ---
    def showEvent(self, event: QShowEvent):
        super().showEvent(event)
        if self._is_running:
            self._timer.start()

    def hideEvent(self, event: QHideEvent):
        super().hideEvent(event)
        self._timer.stop()

    def _on_timeout(self):
        # Counter tăng vô tận, nhưng logic vẽ sẽ dùng modulo (%)
        self._counter += self._base_step * self._speed_factor
        self.update()

    # --- Geometry ---
    def sizeHint(self):
        max_dot_w = self._dot_size * self._max_scale
        total_width = (max_dot_w * self._dot_count) + (
            self._spacing * (self._dot_count - 1)
        )
        return QSize(int(total_width + 4), int(max_dot_w + 4))

    # --- Painting ---
    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)

        center_y = self.height() / 2
        max_dot_w = self._dot_size * self._max_scale

        for i in range(self._dot_count):
            scale_factor = 1.0

            if self._is_running:
                # LOGIC MỚI: PULSE & REST

                # 1. Tính thời gian cục bộ (Local Time) cho từng dot
                # Offset thời gian của dot i là: i * delay
                # Dùng Modulo (%) để tạo vòng lặp

                # current_pos là vị trí của dot i trong vòng lặp [0 -> cycle_rad]
                current_pos = (self._counter - (i * self._delay_rad)) % self._cycle_rad

                # 2. Kiểm tra xem dot có đang trong giai đoạn "Nảy" (Pulse) không?
                # Giai đoạn nảy là từ 0 đến PI (khoảng 3.14)
                if 0 <= current_pos <= self._pulse_rad:
                    # Tính giá trị sin (0 -> 1 -> 0)
                    val = math.sin(current_pos)

                    # Map sang scale
                    scale_factor = 1.0 + (self._max_scale - 1.0) * val
                else:
                    # Ngoài khoảng này là thời gian "Nghỉ" (Rest) đợi các dot khác
                    scale_factor = 1.0

            current_size = self._dot_size * scale_factor

            # Vẽ từ tâm
            x_base = i * (max_dot_w + self._spacing)
            x_center_offset = (max_dot_w - current_size) / 2

            draw_x = x_base + x_center_offset
            draw_y = center_y - (current_size / 2)

            painter.drawEllipse(
                int(draw_x), int(draw_y), int(current_size), int(current_size)
            )
