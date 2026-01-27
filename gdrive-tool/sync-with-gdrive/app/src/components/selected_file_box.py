from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal
from utils.helpers import get_svg_as_icon
from typing import Callable


class FileInfoBox(QFrame):
    _is_clicked = Signal()
    _is_mouse_in = Signal()  # Signal khi chuột vào
    _is_mouse_out = Signal()  # Signal khi chuột ra

    mouse_state_for_outer: str = ""

    def __init__(
        self,
        text: str,
        svg_name: str,
        svg_fill_color: str | None = None,
        svg_stroke_color: str | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("FileInfoBox")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 6)
        layout.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(
            get_svg_as_icon(
                svg_name, 18, fill_color=svg_fill_color, stroke_color=svg_stroke_color
            )
        )
        icon.setFixedSize(18, 18)

        label = QLabel(text)
        label.setObjectName("FileInfoLabel")
        font = label.font()
        font.setPointSize(12)
        label.setFont(font)

        layout.addWidget(icon)
        layout.addWidget(label)

        self.setStyleSheet(
            """
            #FileInfoBox {
                border: 1px solid rgba(255,255,255,40);
                border-radius: 10px;
                background-color: rgba(255,255,255,12);
            }
            #FileInfoBox:hover {
                background-color: rgba(255,255,255,40);
            }
            #FileInfoLabel {
                color: white;
            }
            """
        )

    # --- CÁC HÀM XỬ LÝ SỰ KIỆN (OVERRIDES) ---
    def mousePressEvent(self, event):
        """Chạy khi Widget bị click"""
        self._is_clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Chạy khi chuột đi vào vùng Widget"""
        self._is_mouse_in.emit()  # Phát tín hiệu
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Chạy khi chuột rời khỏi vùng Widget"""
        self._is_mouse_out.emit()  # Phát tín hiệu
        super().leaveEvent(event)

    # --- CÁC HÀM ĐĂNG KÝ CALLBACK ---
    def on_clicked(self, callback: Callable):
        self._is_clicked.connect(callback)

    def on_mouse_in(self, callback: Callable):
        """Gán hàm sẽ chạy khi di chuột vào"""
        self._is_mouse_in.connect(callback)

    def on_mouse_out(self, callback: Callable):
        """Gán hàm sẽ chạy khi di chuột ra"""
        self._is_mouse_out.connect(callback)
