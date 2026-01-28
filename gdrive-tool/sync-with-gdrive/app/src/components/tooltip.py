from dataclasses import dataclass
from enum import Enum, auto
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QVBoxLayout,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QObject, QEvent, QTimer, QPoint, QRect
from PySide6.QtGui import QColor, QCursor
from configs.configs import ThemeColors
from components.label import CustomLabel


# --- 1. Enum Constraints ---
class CollisionConstraint(Enum):
    SCREEN = auto()
    WINDOW = auto()


# --- 2. Configuration ---
@dataclass
class ToolTipConfig:
    text: str
    font_size: int = 10
    max_width: int = 320
    show_delay_ms: int = 200
    constrain_to: CollisionConstraint = CollisionConstraint.WINDOW
    follow_mouse: bool = False
    background_color: str = ThemeColors.GRAY_BACKGROUND
    text_color: str = "#ffffff"


# --- 3. The Visual Tooltip Widget ---
from PySide6.QtWidgets import QFrame, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class CustomToolTip(QFrame):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomToolTipRoot")
        self.config = config

        self.setWindowFlags(
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.NoDropShadowWindowHint
        )

        # Root window: trong suốt hoàn toàn (KHÔNG style background lên đây)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

        # Root layout: chừa mép để shadow không bị cắt
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)  # quan trọng
        root.setSpacing(0)

        # Bubble: nơi thật sự được vẽ bằng stylesheet
        self.bubble = QFrame(self)
        self.bubble.setObjectName("ToolTipBubble")
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(8, 8, 8, 8)
        bubble_layout.setSpacing(0)

        self.label = CustomLabel(config.text)
        self.label.setObjectName("ToolTipLabel")
        self.label.setWordWrap(True)
        self.label.setMaximumWidth(config.max_width)

        bubble_layout.addWidget(self.label)
        root.addWidget(self.bubble)

        # Style apply lên bubble + label
        self.setStyleSheet(
            f"""
            #ToolTipLabel {{
                color: {config.text_color};
                font-size: {config.font_size}pt;
            }}
            #ToolTipBubble {{
                background-color: {config.background_color};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 8px;
            }}
            """
        )

        # Shadow apply lên bubble (ổn hơn apply lên root translucent)
        shadow = QGraphicsDropShadowEffect(self.bubble)
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 4)
        self.bubble.setGraphicsEffect(shadow)


# --- 4. The Logic Binder ---
class ToolTipBinder(QObject):
    def __init__(self, widget: QWidget, config: ToolTipConfig):
        super().__init__(widget)
        self.widget = widget
        self.config = config
        self.tooltip_window: CustomToolTip | None = None

        # Timer cho delay hiển thị
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.show_tooltip)

        # Cài đặt Event Filter
        self.widget.installEventFilter(self)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched == self.widget:
            if event.type() == QEvent.Type.Enter:
                self.timer.start(self.config.show_delay_ms)

            elif event.type() == QEvent.Type.Leave:
                self.timer.stop()
                self.hide_tooltip()

            elif event.type() == QEvent.Type.MouseButtonPress:
                self.timer.stop()
                self.hide_tooltip()

            elif event.type() == QEvent.Type.MouseMove:
                if (
                    self.config.follow_mouse
                    and self.tooltip_window
                    and self.tooltip_window.isVisible()
                ):
                    self.update_position(QCursor.pos())

        return super().eventFilter(watched, event)

    def show_tooltip(self):
        if not self.tooltip_window:
            self.tooltip_window = CustomToolTip(self.config)

        # Cập nhật nội dung (nếu config thay đổi động)
        self.tooltip_window.label.setText(self.config.text)
        self.tooltip_window.adjustSize()

        self.update_position(QCursor.pos())
        self.tooltip_window.show()

    def hide_tooltip(self):
        if self.tooltip_window:
            self.tooltip_window.hide()
            self.tooltip_window.deleteLater()
            self.tooltip_window = None

    def update_position(self, cursor_pos: QPoint):
        if not self.tooltip_window:
            return

        # Khoảng cách từ chuột đến tooltip
        offset_y = 20
        pos = cursor_pos + QPoint(0, offset_y)

        tip_w = self.tooltip_window.width()
        tip_h = self.tooltip_window.height()

        # Xác định vùng giới hạn (Screen hoặc Window cha)
        boundary: QRect
        if self.config.constrain_to == CollisionConstraint.WINDOW:
            window = self.widget.window()
            boundary = window.geometry()
        else:
            # Mặc định lấy màn hình chứa con chuột
            screen = QApplication.screenAt(cursor_pos)
            if not screen:
                screen = QApplication.primaryScreen()
            boundary = screen.availableGeometry()

        # Logic chống tràn (Collision Logic)

        # 1. Tràn bên phải
        if pos.x() + tip_w > boundary.right():
            pos.setX(boundary.right() - tip_w)

        # 2. Tràn bên dưới -> Đẩy lên trên chuột
        if pos.y() + tip_h > boundary.bottom():
            pos.setY(cursor_pos.y() - tip_h - 5)

        # 3. Tràn bên trái (ít gặp nhưng vẫn check)
        if pos.x() < boundary.left():
            pos.setX(boundary.left())

        # 4. Tràn bên trên
        if pos.y() < boundary.top():
            pos.setY(boundary.top())

        self.tooltip_window.move(pos)
