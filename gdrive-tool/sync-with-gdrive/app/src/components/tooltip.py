from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtCore import Qt, QObject, QEvent, QPoint, QTimer
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QWidget, QFrame, QHBoxLayout, QVBoxLayout

# Giả định các import này từ project của bạn vẫn giữ nguyên
from components.label import CustomLabel
from configs.configs import ThemeColors


class CustomToolTip(QFrame):
    """Tooltip widget custom (chỉ text)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(
            parent,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.BypassWindowManagerHint,
        )
        self.setObjectName("MyCustomToolTip")

        # 1. Giữ nền cửa sổ cha trong suốt
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # 2. Tạo Layout chính cho cửa sổ cha
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)

        # 3. Tạo Container
        self._container = QFrame()
        self._container.setObjectName("TooltipContainer")

        self._container.setStyleSheet(
            f"""
            #TooltipContainer {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 8px;
            }}
            """
        )

        self._main_layout.addWidget(self._container)

        # 4. Setup nội dung bên trong Container
        self._root = QHBoxLayout(self._container)
        self._root.setContentsMargins(10, 4, 10, 8)
        self._root.setSpacing(0)
        self._root.setSizeConstraint(QHBoxLayout.SizeConstraint.SetFixedSize)

        self._text = CustomLabel(is_word_wrap=True)
        self._text.setStyleSheet("color: white; border: none;")
        self._root.addWidget(self._text)

    def set_content(self, text: str, max_width: int = 320, font_size: int = 12) -> None:
        self._text.setText(text)
        self._text.setMaximumWidth(max_width)
        self._text.set_font_size(font_size)
        self.adjustSize()

    def show_at_cursor(
        self,
        offset: QPoint = QPoint(12, 16),
        margin: int = 8,
        constrain_to: str = "screen",
        owner_window: QWidget | None = None,
    ) -> None:
        self._text.adjustSize()
        self.adjustSize()

        cursor_pos = QCursor.pos()
        pos = cursor_pos + offset

        w = self.width()
        h = self.height()

        if constrain_to == "window" and owner_window is not None:
            rect = owner_window.frameGeometry()
            left = rect.left() + margin
            top = rect.top() + margin
            right = rect.right() - margin
            bottom = rect.bottom() - margin
        else:
            screen = (
                QGuiApplication.screenAt(cursor_pos) or QGuiApplication.primaryScreen()
            )
            geo = screen.availableGeometry()
            left = geo.left() + margin
            top = geo.top() + margin
            right = geo.right() - margin
            bottom = geo.bottom() - margin

        max_w = max(1, right - left)
        max_h = max(1, bottom - top)
        w = min(w, max_w)
        h = min(h, max_h)

        x = pos.x()
        y = pos.y()

        if x + w > right:
            x = right - w
        if x < left:
            x = left

        if y + h > bottom:
            y = cursor_pos.y() - h - max(6, offset.y() // 2)
        if y < top:
            y = top

        self.resize(w, h)
        self.move(x, y)
        self.show()
        self.raise_()


class CollisionConstraint(str, Enum):
    SCREEN = "screen"
    WINDOW = "window"


@dataclass
class ToolTipConfig:
    text: str
    font_size: int = 10
    max_width: int = 320
    show_delay_ms: int = 200  # Set mặc định 150ms như yêu cầu
    constrain_to: CollisionConstraint = CollisionConstraint.SCREEN
    follow_mouse: bool = False  # Flag mới: False = đứng im, True = chạy theo chuột


class ToolTipBinder(QObject):
    """Gắn tooltip text vào widget."""

    def __init__(self, target: QWidget, config: ToolTipConfig):
        super().__init__(target)
        self._target = target
        self._cfg = config
        self._tip = CustomToolTip(parent=None)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._show_now)

        # Biến lưu vị trí chuột để check khoảng cách di chuyển
        self._last_mouse_pos = QPoint()
        # Ngưỡng di chuyển (pixel). Di chuyển nhỏ hơn số này coi như đứng yên.
        self._move_threshold = 5

        target.setMouseTracking(True)
        target.installEventFilter(self)

        self._is_inside = False

    def set_config(self, config: ToolTipConfig) -> None:
        self._cfg = config
        if self._tip.isVisible():
            self._apply_content()
            # Nếu đang hiện thì update vị trí nếu cần (tùy logic app, ở đây giữ nguyên)
            if self._cfg.follow_mouse:
                self._reposition()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is not self._target:
            return super().eventFilter(watched, event)

        et = event.type()

        if et == QEvent.Type.Enter:
            self._is_inside = True
            self._last_mouse_pos = QCursor.pos()  # Lưu vị trí lúc bắt đầu vào

            # Bắt đầu đếm ngược thời gian show
            if self._cfg.show_delay_ms > 0:
                self._timer.start(self._cfg.show_delay_ms)
            else:
                self._show_now()
            return False

        if et == QEvent.Type.MouseMove:
            if not self._is_inside:
                return False

            curr_pos = QCursor.pos()

            # --- TRƯỜNG HỢP 1: Tooltip chưa hiện (đang chờ timer) ---
            if not self._tip.isVisible():
                # Tính khoảng cách đã di chuyển so với lần cuối check
                dist = (curr_pos - self._last_mouse_pos).manhattanLength()

                # Nếu di chuyển quá ngưỡng (tức là người dùng đang rê chuột liên tục)
                # -> Reset timer lại từ đầu (ngừng show tooltip tạm thời)
                if dist > self._move_threshold:
                    if self._cfg.show_delay_ms > 0:
                        self._timer.stop()
                        self._timer.start(self._cfg.show_delay_ms)
                    self._last_mouse_pos = curr_pos  # Cập nhật mốc vị trí mới

            # --- TRƯỜNG HỢP 2: Tooltip đã hiện ---
            else:
                # Chỉ di chuyển tooltip nếu flag follow_mouse được bật
                if self._cfg.follow_mouse:
                    self._reposition()

            return False

        if et in (QEvent.Type.Leave, QEvent.Type.Hide, QEvent.Type.FocusOut):
            self._is_inside = False
            self._timer.stop()
            self._tip.hide()
            return False

        return super().eventFilter(watched, event)

    def _apply_content(self) -> None:
        cfg = self._cfg
        self._tip.set_content(
            cfg.text, max_width=cfg.max_width, font_size=cfg.font_size
        )

    def _show_now(self) -> None:
        if not self._is_inside:
            return
        self._apply_content()
        self._reposition()

    def _reposition(self) -> None:
        cfg = self._cfg
        owner = (
            self._target.window()
            if cfg.constrain_to == CollisionConstraint.WINDOW
            else None
        )
        self._tip.show_at_cursor(
            offset=QPoint(12, 16),
            margin=8,
            constrain_to=str(cfg.constrain_to),
            owner_window=owner,
        )
