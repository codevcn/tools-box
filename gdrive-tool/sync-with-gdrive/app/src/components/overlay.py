from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QEvent, QObject
from enum import Enum


class OverlayPosition(int, Enum):
    TOP_LEFT = 1
    TOP_CENTER = 2
    TOP_RIGHT = 3
    CENTER_LEFT = 4
    CENTER = 5
    CENTER_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_CENTER = 8
    BOTTOM_RIGHT = 9


class PositionedOverlay(QObject):
    """
    Component quản lý overlay widget tại 9 vị trí khác nhau trong container.
    Mặc định: Central (Giữa màn hình).
    """

    def __init__(
        self,
        container: QWidget,
        overlay: QWidget,
        position: OverlayPosition = OverlayPosition.CENTER,
        margin: int = 10,
    ):
        super().__init__(container)  # QObject cha là container để tự hủy
        self.container = container
        self.overlay = overlay
        self.position = position
        self.margin = margin

        # Đưa overlay vào container
        self.overlay.setParent(container)
        self.overlay.raise_()

        # Cài đặt filter
        self.container.installEventFilter(self)

        # Cập nhật vị trí lần đầu
        self.update_position()

        # Mặc định hiển thị overlay
        self.overlay.show()

    def eventFilter(self, watched, event):
        if watched is self.container and event.type() == QEvent.Type.Resize:
            self.update_position()
        return super().eventFilter(watched, event)

    def set_position(self, position: OverlayPosition):
        """Thay đổi vị trí động"""
        self.position = position
        self.update_position()

    def update_position(self):
        # 1. Lấy vùng hiển thị của container
        rect = self.container.contentsRect()

        # 2. Lấy kích thước hiện tại của overlay
        child_size = self.overlay.size()

        # Fallback sizeHint nếu widget chưa hiển thị hoặc size = 0
        if child_size.width() == 0:
            child_size = self.overlay.sizeHint()
            self.overlay.resize(child_size)

        w = child_size.width()
        h = child_size.height()

        # 3. Tính toán X (Ngang)
        if (
            self.position == OverlayPosition.TOP_LEFT
            or self.position == OverlayPosition.CENTER_LEFT
            or self.position == OverlayPosition.BOTTOM_LEFT
        ):
            x = rect.x() + self.margin
        elif (
            self.position == OverlayPosition.TOP_RIGHT
            or self.position == OverlayPosition.CENTER_RIGHT
            or self.position == OverlayPosition.BOTTOM_RIGHT
        ):
            x = rect.x() + rect.width() - w - self.margin
        else:
            # Mặc định là Center Horizontal nếu không có cờ Left/Right
            x = rect.x() + (rect.width() - w) // 2

        # 4. Tính toán Y (Dọc)
        if (
            self.position == OverlayPosition.TOP_LEFT
            or self.position == OverlayPosition.TOP_CENTER
            or self.position == OverlayPosition.TOP_RIGHT
        ):
            y = rect.y() + self.margin
        elif (
            self.position == OverlayPosition.BOTTOM_LEFT
            or self.position == OverlayPosition.BOTTOM_CENTER
            or self.position == OverlayPosition.BOTTOM_RIGHT
        ):
            y = rect.y() + rect.height() - h - self.margin
        else:
            # Mặc định là Center Vertical nếu không có cờ Top/Bottom
            y = rect.y() + (rect.height() - h) // 2

        # 5. Di chuyển widget
        self.overlay.move(int(x), int(y))
        self.overlay.raise_()

    def hide(self):
        self.overlay.hide()

    def show(self):
        self.overlay.show()
        self.overlay.raise_()
        self.update_position()
