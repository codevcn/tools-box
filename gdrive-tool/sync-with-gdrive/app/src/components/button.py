from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt
from typing import Callable


class CustomButton(QPushButton):
    def __init__(
        self,
        text="",
        parent=None,
        default_enabled=True,
        is_bold: bool = True,
        font_size: int | None = None,
        fixed_height: int | None = None,
    ):
        super().__init__(text, parent)
        self.setEnabled(bool(default_enabled))

        font = self.font()
        if is_bold:
            font.setBold(True)
        if font_size is not None:
            font.setPointSize(font_size)
        self.setFont(font)

        if fixed_height:
            self.setFixedHeight(fixed_height)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        if enabled:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ForbiddenCursor)

    def on_clicked(self, func: Callable) -> None:
        self.clicked.connect(func)
