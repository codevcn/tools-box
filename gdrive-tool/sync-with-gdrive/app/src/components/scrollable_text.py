from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QScrollArea, QSizePolicy
from PySide6.QtCore import Qt


class ScrollableText(QFrame):
    def __init__(self, default_text: str = "", fixed_height: int = 120, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        self.setObjectName("ScrollableTextRoot")
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._label = QLabel()
        self._label.setWordWrap(True)
        self._label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )

        self._scroll.setObjectName("ScrollableTextScroll")
        self._label.setObjectName("ScrollableTextLabel")

        self._scroll.setWidget(self._label)

        root.addWidget(self._scroll)

        self.setFixedHeight(fixed_height)

        self.setText(default_text)

    def setText(self, text: str) -> None:
        self._label.setText(text)

    def clear_text(self) -> None:
        self._label.setText("")

    def get_text(self) -> str:
        return self._label.text()

    def set_font_size(self, size: int) -> None:
        font = self._label.font()
        font.setPointSize(size)
        self._label.setFont(font)

    def set_contents_margins(
        self, left: int, top: int, right: int, bottom: int
    ) -> None:
        self._label.setContentsMargins(left, top, right, bottom)
