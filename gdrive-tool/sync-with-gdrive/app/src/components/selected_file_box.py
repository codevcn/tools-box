from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal
from utils.helpers import svg_to_pixmap
from typing import Callable


class FileInfoBox(QFrame):
    is_clicked = Signal()

    def __init__(
        self,
        text: str,
        svg_path: str,
        svg_fill_color: str | None = None,
        svg_stroke_color: str | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.setObjectName("FileInfoBox")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 6)  # padding trong box
        layout.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(
            svg_to_pixmap(
                svg_path, 18, fill_color=svg_fill_color, stroke_color=svg_stroke_color
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

        # style: bo tròn + nền + border
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

    def mousePressEvent(self, event):
        self.is_clicked.emit()
        super().mousePressEvent(event)

    def on_clicked(self, callback: Callable):
        self.is_clicked.connect(callback)
