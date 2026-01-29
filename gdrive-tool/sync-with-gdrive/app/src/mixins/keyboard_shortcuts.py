from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QDialog, QWidget, QMessageBox
from PySide6.QtCore import QObject


class KeyboardShortcutsDialogMixin(QDialog):
    """Mixin cung cấp các phím tắt bàn phím cho ứng dụng."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Thiết lập các phím tắt bàn phím."""
        super().__init__(parent)
        self._add_keyboard_shortcuts()

    def _add_keyboard_shortcuts(self):
        # Ctrl + Q (thoát ứng dụng)
        shortcut_ctrl_q = QShortcut(QKeySequence("Ctrl+Q"), self)
        shortcut_ctrl_q.activated.connect(self.close)

        # Alt + Q (thoát ứng dụng)
        shortcut_alt_q = QShortcut(QKeySequence("Alt+Q"), self)
        shortcut_alt_q.activated.connect(self.close)


class KeyboardShortcutsAnnounceMixin(QObject):
    """Mixin cung cấp các phím tắt bàn phím cho widget."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Thiết lập các phím tắt bàn phím."""
        super().__init__(parent)
        self._add_keyboard_shortcuts()
        self._msg_box = QMessageBox

    def _add_keyboard_shortcuts(self):
        # Ctrl + Q (thoát ứng dụng)
        shortcut_ctrl_q = QShortcut(QKeySequence("Ctrl+Q"), self)
        shortcut_ctrl_q.activated.connect(self._msg_box.close)

        # Alt + Q (thoát ứng dụng)
        shortcut_alt_q = QShortcut(QKeySequence("Alt+Q"), self)
        shortcut_alt_q.activated.connect(self._msg_box.close)
