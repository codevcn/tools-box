from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtWidgets import QLayout, QLayoutItem


class CustomFlowLayout(QLayout):
    def __init__(self, parent=None, margins=(0, 0, 0, 0), h_spacing=8, v_spacing=8):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._h = h_spacing
        self._v = v_spacing
        self.setContentsMargins(*margins)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if (0 <= index < len(self._items)) else None

    def takeAt(self, index: int) -> QLayoutItem | None:  # type: ignore
        return self._items.pop(index) if (0 <= index < len(self._items)) else None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        # Tính toán size hint dựa trên width hiện tại
        if self.geometry().width() > 0:
            width = self.geometry().width()
        else:
            # Fallback: dùng một width mặc định để tính
            width = 400

        height = self.heightForWidth(width)
        return QSize(width, height)

    def minimumSize(self) -> QSize:
        # Tính minimum width dựa trên item rộng nhất
        margins = self.contentsMargins()
        l = margins.left()
        t = margins.top()
        r = margins.right()
        b = margins.bottom()

        min_width = 0
        for item in self._items:
            min_width = max(min_width, item.minimumSize().width())

        # Minimum height cho 1 item (khi chỉ có 1 dòng)
        min_height = 0
        if self._items:
            min_height = self._items[0].sizeHint().height()

        return QSize(min_width + l + r, min_height + t + b)

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0

        margins = self.contentsMargins()
        l = margins.left()
        t = margins.top()
        r = margins.right()
        b = margins.bottom()

        effective_rect = rect.adjusted(l, t, -r, -b)

        x = effective_rect.x()
        y = effective_rect.y()
        max_x = effective_rect.right()

        for item in self._items:
            w = item.widget()
            if w is not None and not w.isVisible():
                continue

            hint = item.sizeHint()
            next_x = x + hint.width()

            # nếu vượt quá width => xuống dòng
            if next_x - 1 > max_x and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + self._v
                next_x = x + hint.width()
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x + self._h
            line_height = max(line_height, hint.height())

        total_height = (y - effective_rect.y()) + line_height
        return total_height + t + b
