from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Dict

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget, QLabel


ButtonCallback = Callable[[], None]


@dataclass(frozen=True)
class PopupButtonSpec:
    key: str
    text: str
    role: QMessageBox.ButtonRole = QMessageBox.ButtonRole.ActionRole
    icon: Optional[QIcon] = None
    on_click: Optional[ButtonCallback] = None
    closes: bool = True  # True: auto close popup after click


class CustomPopup(QObject):
    """
    Wrapper cho QMessageBox để:
    - Custom buttons (text/icon/role)
    - Gắn logic riêng khi nhấn
    - Hỗ trợ block (exec) và non-block (open)
    """

    finished = Signal(str)  # emit button key khi popup đóng bằng 1 button

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "",
        text: str = "",
        informative_text: str | None = None,
        detailed_text: str | None = None,
        icon: QMessageBox.Icon = QMessageBox.Icon.NoIcon,
        icon_pixmap: QPixmap | None = None,
        stylesheet: str | None = None,
    ) -> None:
        super().__init__(parent)

        self._msg = QMessageBox(parent)
        self._msg.setWindowTitle(title)
        self._msg.setText(text)

        if informative_text:
            self._msg.setInformativeText(informative_text)
        if detailed_text:
            self._msg.setDetailedText(detailed_text)

        if icon_pixmap is not None:
            self._msg.setIconPixmap(icon_pixmap)
        else:
            self._msg.setIcon(icon)

        if stylesheet:
            self._msg.setStyleSheet(stylesheet)

        self._customize_layout()

        self._buttons: Dict[str, QPushButton] = {}
        self._specs: Dict[str, PopupButtonSpec] = {}
        self._result_key: Optional[str] = None

        # Nếu user đóng bằng X, treat như cancel (nếu có)
        self._msg.rejected.connect(self._on_rejected)

    def _customize_layout(self) -> None:
        """
        Can thiệp vào layout lưới (GridLayout) của QMessageBox
        để đẩy cả Icon và Text lên sát lề trên cùng.
        """
        layout = self._msg.layout()
        if layout:
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(0)
            # Duyệt qua các item trong layout (Icon label, Text label)
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and isinstance(widget, QLabel):
                        widget.setContentsMargins(0, 0, 0, 0)

    # -------------------------
    # Core API
    # -------------------------
    def set_title(self, title: str) -> None:
        self._msg.setWindowTitle(title)

    def set_text(self, text: str) -> None:
        self._msg.setText(text)

    def set_informative_text(self, text: str | None) -> None:
        self._msg.setInformativeText(text or "")

    def set_detailed_text(self, text: str | None) -> None:
        self._msg.setDetailedText(text or "")

    def set_icon(self, icon: QMessageBox.Icon) -> None:
        self._msg.setIcon(icon)

    def set_icon_pixmap(self, pixmap: QPixmap) -> None:
        self._msg.setIconPixmap(pixmap)

    def add_button(self, spec: PopupButtonSpec) -> QPushButton:
        if spec.key in self._buttons:
            raise ValueError(f"Duplicate button key: {spec.key}")

        btn = self._msg.addButton(spec.text, spec.role)

        if spec.icon is not None:
            btn.setIcon(spec.icon)

        # NOTE: QMessageBox sẽ đóng sau click nếu exec().
        # Với open() non-block: ta tự quyết, bằng closes flag + accept/reject.
        btn.clicked.connect(lambda: self._handle_button_click(spec.key))

        self._buttons[spec.key] = btn
        self._specs[spec.key] = spec
        return btn

    def button(self, key: str) -> QPushButton | None:
        return self._buttons.get(key)

    def set_default_button(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn:
            self._msg.setDefaultButton(btn)

    def set_escape_button(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn:
            self._msg.setEscapeButton(btn)

    def exec_and_get(self) -> str | None:
        """
        Block UI (modal). Trả về key của button đã bấm.
        Nếu đóng bằng X và không map được -> None.
        """
        self._result_key = None
        self._msg.exec()
        return self._result_key

    def open(self) -> None:
        """
        Non-block. Khi bấm button sẽ emit finished(key).
        """
        self._result_key = None
        self._msg.open()

    def close(self) -> None:
        self._msg.close()

    # -------------------------
    # Internals
    # -------------------------
    def _handle_button_click(self, key: str) -> None:
        self._result_key = key
        spec = self._specs.get(key)

        # chạy logic trước
        if spec and spec.on_click:
            spec.on_click()

        # quyết định đóng hay giữ
        if spec is None or spec.closes:
            # role RejectRole => reject, còn lại accept
            if spec and spec.role == QMessageBox.ButtonRole.RejectRole:
                self._msg.reject()
            else:
                self._msg.accept()

        # với open(): emit signal
        self.finished.emit(key)

    def _on_rejected(self) -> None:
        # user đóng bằng X (hoặc Esc) mà không qua button click
        # Nếu có button "cancel" / "close" thì emit nó, không thì emit rỗng
        fallback_key = None
        for k, spec in self._specs.items():
            if spec.role == QMessageBox.ButtonRole.RejectRole:
                fallback_key = k
                break
        if fallback_key is not None:
            self._result_key = fallback_key
            self.finished.emit(fallback_key)
        else:
            self.finished.emit("")
