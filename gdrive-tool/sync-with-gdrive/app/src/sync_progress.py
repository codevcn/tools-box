from PySide6.QtWidgets import QDialog, QWidget


class SyncProgress(QDialog):
    """Window hiển thị tiến trình đồng bộ."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
