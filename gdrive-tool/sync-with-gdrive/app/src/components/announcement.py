from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Dict, cast, Tuple

from PySide6.QtCore import Signal, QObject, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QWidget,
    QLabel,
    QApplication,
    QScrollArea,
    QVBoxLayout,
    QGridLayout,
    QSizePolicy,
)
from ..configs.configs import ThemeColors
from ..utils.helpers import get_svg_as_icon


@dataclass(frozen=True)
class DialogButtonSpec:
    key: str
    text: str
    role: QMessageBox.ButtonRole = QMessageBox.ButtonRole.ActionRole
    icon: Optional[QIcon] = None
    on_click: Optional[Callable[[], None]] = None
    closes: bool = True  # True: auto close popup after click


class CustomAnnounce(QObject):
    """
    Wrapper cho QMessageBox để:
    - Custom buttons (text/icon/role)
    - Gắn logic riêng khi nhấn
    - Hỗ trợ block (exec) và non-block (open)
    - Hỗ trợ nút Copy nội dung nhanh
    - Hỗ trợ cuộn nội dung với kích thước cố định (500x400)
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
        with_copy_btn: bool = True,
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

        # Custom layout sau khi đã set text
        self._customize_layout()

        self._buttons: Dict[str, QPushButton] = {}
        self._specs: Dict[str, DialogButtonSpec] = {}
        self._result_key: Optional[str] = None

        # --- Logic thêm nút Copy ---
        if with_copy_btn:
            self.add_button(
                DialogButtonSpec(
                    key="default_ok_btn",
                    text="OK",
                    role=QMessageBox.ButtonRole.AcceptRole,
                    closes=True,
                )
            )

            self.add_button(
                DialogButtonSpec(
                    key="internal_copy_btn",
                    text="Copy",
                    role=QMessageBox.ButtonRole.ActionRole,
                    on_click=self._copy_content,
                    closes=False,
                )
            )

        self._msg_box.rejected.connect(self._on_rejected)
        self._add_keyboard_shortcuts()

    def _add_keyboard_shortcuts(self):
        for seq in ["Ctrl+Q", "Alt+Q"]:
            shortcut = QShortcut(QKeySequence(seq), self._msg_box)
            shortcut.activated.connect(self._msg_box.close)

    def _copy_content(self) -> None:
        parts = []
        msg = self._msg_box.text()
        info = self._msg_box.informativeText()
        detail = self._msg_box.detailedText()

        if msg:
            parts.append(f"Message: {msg}")
        if info:
            parts.append(f"Informative Text: {info}")
        if detail:
            parts.append(f"Detailed Text: {detail}")

        final_text = " , ".join(parts)

        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(final_text)
            btn = self.button("internal_copy_btn")
            if btn:
                original_text = btn.text()
                btn.setText("Copied!")
                QTimer.singleShot(1000, lambda: btn.setText(original_text))

    def _customize_layout(self) -> None:
        """
        Tìm label chứa nội dung chính và bọc nó vào QScrollArea
        với kích thước cố định: Rộng 500px, Cao 400px.
        """
        layout = self._msg_box.layout()

        if not isinstance(layout, QGridLayout):
            return

        # 1. Tìm Label chứa text chính
        content_label = None
        index = -1
        current_text = self._msg_box.text()

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QLabel):
                    if w.text() == current_text:
                        content_label = w
                        index = i
                        break

        if not content_label:
            return

        # 2. Lấy thông tin vị trí cũ trong Grid
        position_data = layout.getItemPosition(index)
        row, col, rowspan, colspan = cast(Tuple[int, int, int, int], position_data)

        # 3. Remove label cũ khỏi layout
        layout.removeWidget(content_label)

        # 4. Tạo ScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        # --- CẤU HÌNH KÍCH THƯỚC CỐ ĐỊNH ---
        # Tắt thanh cuộn ngang
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Thiết lập kích thước cố định cho vùng nội dung
        # Popup sẽ tự động to ra để bao bọc vùng này
        scroll.setFixedWidth(500)
        scroll.setFixedHeight(400)

        # Policy cố định để tránh bị resize tự động
        scroll.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # 5. Tạo Container widget
        content_container = QWidget()
        content_container.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(content_container)
        vbox.setContentsMargins(0, 0, 0, 0)

        # Cấu hình label
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        content_label.setOpenExternalLinks(True)
        # Label mở rộng chiều dọc theo nội dung (để scroll hoạt động)
        content_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        vbox.addWidget(content_label)

        # Thêm spacer ở dưới để đẩy text lên trên nếu nội dung ngắn (tùy chọn thẩm mỹ)
        vbox.addStretch()

        scroll.setWidget(content_container)

        # 6. Add ScrollArea vào đúng vị trí cũ
        layout.addWidget(scroll, row, col, rowspan, colspan)

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

        if not spec.closes:
            try:
                btn.clicked.disconnect()
            except Exception:
                pass

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
        self._result_key = None
        self._msg_box.exec()

    def open(self) -> None:
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

        if spec and spec.on_click:
            spec.on_click()

        if spec is None or spec.closes:
            if spec and spec.role == QMessageBox.ButtonRole.RejectRole:
                self._msg_box.reject()
            else:
                self._msg_box.accept()

        self.finished.emit(key)

    def _on_rejected(self) -> None:
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
        icon_pixmap: QPixmap | None = None,
        with_copy_btn: bool = True,
    ) -> None:
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
    def warn(
        cls,
        parent: QWidget | None,
        title: str,
        message: str,
        informative_text: str | None = None,
        details_text: str | None = None,
        with_copy_btn: bool = True,
    ) -> None:
        cls.show_msg_box(
            parent,
            title=title,
            message=message,
            informative_text=informative_text,
            details_text=details_text,
            icon_pixmap=get_svg_as_icon(
                "warn_icon",
                35,
                None,
                ThemeColors.WARNING,
                margins=(0, 0, 0, 0),
            ),
            with_copy_btn=with_copy_btn,
        )

    @classmethod
    def info(
        cls,
        parent: QWidget | None,
        title: str,
        message: str,
        informative_text: str | None = None,
        details_text: str | None = None,
        with_copy_btn: bool = True,
    ) -> None:
        cls.show_msg_box(
            parent,
            title=title,
            message=message,
            informative_text=informative_text,
            details_text=details_text,
            icon_pixmap=get_svg_as_icon(
                "info_icon",
                35,
                None,
                ThemeColors.INFO,
                margins=(0, 0, 0, 0),
            ),
            with_copy_btn=with_copy_btn,
        )

    @classmethod
    def error(
        cls,
        parent: QWidget | None,
        title: str,
        message: str,
        informative_text: str | None = None,
        details_text: str | None = None,
        with_copy_btn: bool = True,
    ) -> None:
        cls.show_msg_box(
            parent,
            title=title,
            message=message,
            informative_text=informative_text,
            details_text=details_text,
            with_copy_btn=with_copy_btn,
            icon_pixmap=get_svg_as_icon(
                "error_icon",
                35,
                None,
                ThemeColors.ERROR,
                margins=(0, 0, 0, 0),
            ),
        )
