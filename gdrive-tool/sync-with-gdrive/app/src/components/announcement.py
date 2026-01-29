from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Dict

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget, QLabel, QApplication
from ..configs.configs import ThemeColors
from ..utils.helpers import get_svg_as_icon
from PySide6.QtCore import QTimer
from ..mixins.keyboard_shortcuts import KeyboardShortcutsAnnounceMixin


@dataclass(frozen=True)
class DialogButtonSpec:
    key: str
    text: str
    role: QMessageBox.ButtonRole = QMessageBox.ButtonRole.ActionRole
    icon: Optional[QIcon] = None
    on_click: Optional[Callable[[], None]] = None
    closes: bool = True  # True: auto close popup after click


class CustomAnnounce(KeyboardShortcutsAnnounceMixin):
    """
    Wrapper cho QMessageBox để:
    - Custom buttons (text/icon/role)
    - Gắn logic riêng khi nhấn
    - Hỗ trợ block (exec) và non-block (open)
    - Hỗ trợ nút Copy nội dung nhanh
    """

    finished = Signal(str)  # emit button key khi popup đóng bằng 1 button

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        title: str = "",
        message: str = "",
        informative_text: str | None = None,
        detailed_text: str | None = None,
        icon: QMessageBox.Icon = QMessageBox.Icon.NoIcon,
        icon_pixmap: QPixmap | None = None,
        stylesheet: str | None = None,
        with_copy_btn: bool = True,  # <--- Tham số mới
    ) -> None:
        super().__init__(parent)

        self._msg_box = QMessageBox(parent)
        self._msg_box.setWindowTitle(title)
        self._msg_box.setText(message)

        if informative_text:
            self._msg_box.setInformativeText(informative_text)
        if detailed_text:
            self._msg_box.setDetailedText(detailed_text)

        if icon_pixmap is not None:
            self._msg_box.setIconPixmap(icon_pixmap)
        else:
            self._msg_box.setIcon(icon)

        if stylesheet:
            self._msg_box.setStyleSheet(stylesheet)

        self._customize_layout()

        self._buttons: Dict[str, QPushButton] = {}
        self._specs: Dict[str, DialogButtonSpec] = {}
        self._result_key: Optional[str] = None

        # --- Logic thêm nút Copy ---
        if with_copy_btn:
            # Thêm lại nút OK (Để đóng popup)
            # Vì khi đã add 1 nút custom, Qt sẽ bỏ nút OK mặc định đi
            self.add_button(
                DialogButtonSpec(
                    key="default_ok_btn",
                    text="OK",
                    role=QMessageBox.ButtonRole.AcceptRole,
                    closes=True,  # Nút này sẽ đóng popup
                )
            )

            self.add_button(
                DialogButtonSpec(
                    key="internal_copy_btn",
                    text="Copy",
                    role=QMessageBox.ButtonRole.ActionRole,
                    on_click=self._copy_content,
                    closes=False,  # Không đóng popup khi nhấn Copy
                )
            )

        # Nếu user đóng bằng X, treat như cancel (nếu có)
        self._msg_box.rejected.connect(self._on_rejected)

    def _copy_content(self) -> None:
        """
        Copy nội dung thông báo vào clipboard theo định dạng:
        Message: ... , Informative Text: ... , Detailed Text: ...
        """
        parts = []

        # Lấy text và loại bỏ khoảng trắng thừa nếu cần
        msg = self._msg_box.text()
        info = self._msg_box.informativeText()
        detail = self._msg_box.detailedText()

        if msg:
            parts.append(f"Message: {msg}")
        if info:
            parts.append(f"Informative Text: {info}")
        if detail:
            parts.append(f"Detailed Text: {detail}")

        # Nối lại bằng dấu phẩy theo yêu cầu
        final_text = " , ".join(parts)

        # Set vào clipboard
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(final_text)

            # (Tùy chọn) Feedback nhẹ cho người dùng biết đã copy
            btn = self.button("internal_copy_btn")
            if btn:
                original_text = btn.text()
                btn.setText("Copied!")
                # Reset lại text sau 1s (dùng QTimer nếu muốn, ở đây để đơn giản giữ nguyên hoặc user tự đóng)
                QTimer.singleShot(1000, lambda: btn.setText(original_text))

    def _customize_layout(self) -> None:
        """
        Can thiệp vào layout lưới (GridLayout) của QMessageBox
        để đẩy cả Icon và Text lên sát lề trên cùng.
        """
        layout = self._msg_box.layout()
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
        self._msg_box.setWindowTitle(title)

    def set_message(self, text: str) -> None:
        self._msg_box.setText(text)

    def set_informative_text(self, text: str | None) -> None:
        self._msg_box.setInformativeText(text or "")

    def set_detailed_text(self, text: str | None) -> None:
        self._msg_box.setDetailedText(text or "")

    def set_icon(self, icon: QMessageBox.Icon) -> None:
        self._msg_box.setIcon(icon)

    def set_icon_pixmap(self, pixmap: QPixmap) -> None:
        self._msg_box.setIconPixmap(pixmap)

    def add_button(self, spec: DialogButtonSpec) -> QPushButton:
        if spec.key in self._buttons:
            raise ValueError(f"Duplicate button key: {spec.key}")

        btn = self._msg_box.addButton(spec.text, spec.role)

        if spec.icon is not None:
            btn.setIcon(spec.icon)

        # --- FIX QUAN TRỌNG ---
        # Nếu button được cấu hình không đóng popup (closes=False),
        # ta PHẢI ngắt signal clicked mặc định của QMessageBox (vốn luôn đóng popup).
        if not spec.closes:
            try:
                btn.clicked.disconnect()
            except Exception:
                pass

        # Sau đó mới connect logic của mình
        btn.clicked.connect(lambda: self._handle_button_click(spec.key))

        self._buttons[spec.key] = btn
        self._specs[spec.key] = spec
        return btn

    def button(self, key: str) -> QPushButton | None:
        return self._buttons.get(key)

    def set_default_button(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn:
            self._msg_box.setDefaultButton(btn)

    def set_escape_button(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn:
            self._msg_box.setEscapeButton(btn)

    def exec(self) -> None:
        """
        Block UI (modal). Trả về key của button đã bấm.
        Nếu đóng bằng X và không map được -> None.
        """
        self._result_key = None
        self._msg_box.exec()

    def open(self) -> None:
        """
        Non-block. Khi bấm button sẽ emit finished(key).
        """
        self._result_key = None
        self._msg_box.open()

    def close(self) -> None:
        self._msg_box.close()

    # -------------------------
    # Internals
    # -------------------------
    def _handle_button_click(self, key: str) -> None:
        self._result_key = key
        spec = self._specs.get(key)

        # 1. Chạy logic custom (ví dụ: copy)
        if spec and spec.on_click:
            spec.on_click()

        # 2. Quyết định đóng hay giữ
        if spec is None or spec.closes:
            # Nếu cần đóng, gọi accept/reject để thoát exec loop
            if spec and spec.role == QMessageBox.ButtonRole.RejectRole:
                self._msg_box.reject()
            else:
                self._msg_box.accept()

        # (Nếu closes=False, ta KHÔNG gọi accept/reject,
        # và do đã disconnect ở add_button nên popup sẽ giữ nguyên)

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

    # ------------------------- static helpers -------------------------
    @classmethod
    def show_msg_box(
        cls,
        parent: QWidget | None,
        title: str,
        message: str,
        informative_text: str | None = None,
        details_text: str | None = None,
        with_copy_btn: bool = True,  # <--- Update
    ) -> None:
        """
        Static method để hiển thị nhanh một thông báo cơ bản.
        """
        dialog = cls(
            parent,
            title=title,
            message=message,
            informative_text=informative_text,
            detailed_text=details_text,
            with_copy_btn=with_copy_btn,
        )
        dialog.exec()

    @classmethod
    def warn(
        cls,
        parent: QWidget | None,
        title: str,
        message: str,
        informative_text: str | None = None,
        details_text: str | None = None,
        with_copy_btn: bool = True,  # <--- Update
    ) -> None:
        """
        Static method hiển thị cảnh báo (Warning).
        """
        icon_pixmap = get_svg_as_icon(
            "warn_icon",
            35,
            None,
            ThemeColors.WARNING,
            margins=(0, 0, 8, 0),
        )

        dialog = cls(
            parent,
            title=title,
            message=message,
            informative_text=informative_text,
            detailed_text=details_text,
            icon_pixmap=icon_pixmap,
            with_copy_btn=with_copy_btn,
        )
        dialog.exec()

    @classmethod
    def info(
        cls,
        parent: QWidget | None,
        title: str,
        message: str,
        informative_text: str | None = None,
        details_text: str | None = None,
        with_copy_btn: bool = True,  # <--- Update
    ) -> None:
        """
        Static method hiển thị thông tin (Info).
        """
        icon_pixmap = get_svg_as_icon(
            "info_icon",
            35,
            None,
            ThemeColors.INFO,
            margins=(0, 0, 8, 0),
        )

        dialog = cls(
            parent,
            title=title,
            message=message,
            informative_text=informative_text,
            detailed_text=details_text,
            icon_pixmap=icon_pixmap,
            with_copy_btn=with_copy_btn,
        )
        dialog.exec()

    @classmethod
    def error(
        cls,
        parent: QWidget | None,
        title: str,
        message: str,
        informative_text: str | None = None,
        details_text: str | None = None,
        with_copy_btn: bool = True,  # <--- Update
    ) -> None:
        """
        Static method hiển thị lỗi (Error).
        """
        icon_pixmap = get_svg_as_icon(
            "error_icon",
            35,
            None,
            ThemeColors.ERROR,
            margins=(0, 0, 8, 0),
        )

        dialog = cls(
            parent,
            title=title,
            message=message,
            informative_text=informative_text,
            detailed_text=details_text,
            icon_pixmap=icon_pixmap,
            with_copy_btn=with_copy_btn,
        )
        dialog.exec()
