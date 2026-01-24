from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QFrame,
    QWidgetAction,
)
from utils.helpers import get_svg_as_icon
from configs.configs import ThemeColors


@dataclass(frozen=True)
class SelectOption:
    label: str
    value: str
    icon: QPixmap | None = None
    checked: bool = False


class _SelectBar(QFrame):
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SelectBar")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 8)
        root.setSpacing(8)

        label_layout = QHBoxLayout()
        self.label_icon = QLabel()
        self.label_icon.setFixedSize(18, 18)
        self.label_text = QLabel("")
        self.label_text.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.label_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        label_layout.addWidget(self.label_icon)
        label_layout.addWidget(self.label_text)

        self.arrow = QLabel("▾")
        self.arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.arrow.setFixedWidth(18)

        root.addLayout(label_layout)
        root.addWidget(self.arrow)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class _OptionRow(QWidget):
    """UI cho 1 option: [icon]  label   [✓]"""

    clicked = Signal()

    def __init__(
        self,
        opt: SelectOption,
        check_icon: QPixmap | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SelectOptionRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(10)

        check_icon_size = 20
        self._check_icon = (
            get_svg_as_icon("check_icon", check_icon_size, None, "#ffffff", 3)
            if not check_icon
            else check_icon
        )

        self._icon = QLabel()
        self._icon.setFixedSize(18, 18)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if opt.icon is not None:
            self._icon.setPixmap(opt.icon.scaled(*self.create_icon_scaled_params()))
        root.addWidget(self._icon)

        self._label = QLabel(opt.label)
        self._label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        root.addWidget(self._label, 1)

        self._check = QLabel()
        self._check.setFixedSize(check_icon_size, check_icon_size)
        self._check.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if opt.checked:
            self._check.setPixmap(
                self._check_icon.scaled(*self.create_icon_scaled_params())
            )
        root.addWidget(self._check)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self.clicked.emit()
        super().mousePressEvent(event)

    @staticmethod
    def create_icon_scaled_params() -> (
        tuple[int, int, Qt.AspectRatioMode, Qt.TransformationMode]
    ):
        return (
            18,
            18,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )


class CustomSelectBox(QWidget):
    """
    Custom select box (dropdown) dùng QMenu.

    Public API:
      - get_active_value() -> str | None
      - on_value_change(callback: (value, option) -> None) -> None
      - set_active_value(value: str) -> None
    """

    value_changed = Signal(SelectOption)

    def __init__(
        self,
        options: Sequence[SelectOption],
        default_value: str | None = None,
        placeholder: str = "Select...",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._options = list(options)
        self._placeholder = placeholder
        self._active_value: str | None = None
        self._callback: Optional[Callable[[str | None, SelectOption | None], None]] = (
            None
        )

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._bar = _SelectBar(self)
        self._bar.clicked.connect(self._open_menu)
        root.addWidget(self._bar)

        if default_value:
            self.set_active_value(default_value)
        else:
            self._sync_label()

        self.setStyleSheet(
            f"""
            #SelectBar {{
                background-color: #2d2d2d;
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 8px;
                color: white;
            }}
        """
        )

    # -------------------------
    # Public methods
    # -------------------------
    def get_active_value(self) -> str | None:
        return self._active_value

    def on_value_change(
        self,
        callback: Callable[[str | None, SelectOption | None], None],
    ) -> None:
        self._callback = callback

    def set_active_value(self, value: str) -> None:
        # chỉ set nếu value tồn tại trong options
        if any(o.value == value for o in self._options):
            self._active_value = value
        else:
            self._active_value = None
        self._sync_label()

    # -------------------------
    # Internal
    # -------------------------
    def _open_menu(self) -> None:
        if not self._options:
            return

        menu = QMenu(self)
        menu.setMinimumWidth(self._bar.width())

        for base_opt in self._options:
            # checked theo active hiện tại
            opt = SelectOption(
                label=base_opt.label,
                value=base_opt.value,
                icon=base_opt.icon,
                checked=(base_opt.value == self._active_value),
            )

            row = _OptionRow(opt, parent=menu)

            action = QWidgetAction(menu)
            action.setDefaultWidget(row)

            row.clicked.connect(lambda o=base_opt: self._set_active_option(o))
            menu.addAction(action)

        pos = self._bar.mapToGlobal(self._bar.rect().bottomLeft())
        menu.exec(pos)

    def _set_active_option(self, opt: SelectOption) -> None:
        if self._active_value == opt.value:
            return

        self._active_value = opt.value
        self._sync_label()

        self.value_changed.emit(opt)

        if self._callback:
            self._callback(opt.value, opt)

    def _sync_label(self) -> None:
        if self._active_value is None:
            self._bar.label_text.setText(self._placeholder)
            self._bar.label_icon.clear()
            return

        for opt in self._options:
            if opt.value == self._active_value:
                self._bar.label_text.setText(opt.label)
                if opt.icon:
                    self._bar.label_icon.setPixmap(
                        opt.icon.scaled(
                            *(_OptionRow.create_icon_scaled_params()),
                        )
                    )
                return

        self._bar.label_text.setText(self._placeholder)
