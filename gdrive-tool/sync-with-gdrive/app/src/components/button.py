from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt


class CustomButton(QPushButton):
    def __init__(
        self,
        text="",
        parent=None,
        default_enabled=True,
    ):
        super().__init__(text, parent)
        self.setEnabled(bool(default_enabled))

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        if enabled:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
