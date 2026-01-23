from PySide6.QtWidgets import QLabel
from PySide6.QtWidgets import QSizePolicy


class CustomLabel(QLabel):
    def __init__(
        self,
        text: str = "",
        parent=None,
        is_bold: bool = False,
        is_word_wrap: bool = False,
    ):
        super().__init__(text, parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        if is_bold:
            font = self.font()
            font.setBold(True)
            self.setFont(font)
        if is_word_wrap:
            self.setWordWrap(True)
