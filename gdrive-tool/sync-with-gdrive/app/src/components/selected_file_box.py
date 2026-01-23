from PySide6.QtWidgets import QFrame, QLabel, QHBoxLayout, QSizePolicy
from PySide6.QtCore import Qt
from utils.helpers import svg_to_pixmap


class FileInfoBox(QFrame):
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
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )  # optional
        font = label.font()
        font.setPointSize(12)
        label.setFont(font)

        layout.addWidget(icon)
        layout.addWidget(label)

        # style: bo tròn + nền + border
        self.setStyleSheet(
            """
            QFrame#FileInfoBox {
                border: 1px solid rgba(255,255,255,40);
                border-radius: 10px;
                background-color: rgba(255,255,255,12);
            }
            QLabel {
                color: white;
            }
            """
        )
