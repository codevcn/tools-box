from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget


class CustomFlowLayout(QLayout):
    def __init__(
        self,
        parent: QWidget | None = None,
        margins=(0, 0, 0, 0),
        h_spacing=8,
        v_spacing=8,
    ):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._h = h_spacing
        self._v = v_spacing
        self.setContentsMargins(*margins)

    def addItem(self, item):
        self._items.append(item)
        self.invalidate()  # <--- QUAN TRỌNG: Báo hiệu layout cần tính lại

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if (0 <= index < len(self._items)) else None

    def takeAt(self, index: int) -> QLayoutItem | None:  # type: ignore
        if 0 <= index < len(self._items):
            item = self._items.pop(index)
            self.invalidate()  # <--- QUAN TRỌNG
            return item
        return None

    def clear_items(self):
        """Xóa toàn bộ item và widget con ra khỏi layout và bộ nhớ."""
        # Lặp liên tục cho đến khi không còn item nào trong list
        while self.count() > 0:
            item = self.takeAt(0)  # Lấy item đầu tiên ra
            if item:
                widget = item.widget()
                if widget:
                    # Quan trọng: Lệnh này mới thực sự xóa widget khỏi giao diện và bộ nhớ
                    widget.deleteLater()

        # Báo hiệu layout đã thay đổi (dù takeAt đã có, gọi lại cho chắc chắn sạch sẽ)
        self.invalidate()

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
        return self.minimumSize()

    # FILE: flow_layout.py

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()

        # --- SỬA ĐOẠN TÍNH WIDTH ---
        # Ưu tiên lấy width từ vùng khả dụng của widget cha (contentsRect)
        # thay vì geometry() để chính xác hơn khi có border/margin.
        available_width = 0
        parent = self.parentWidget()
        if parent:
            # contentsRect() trả về kích thước bên trong (đã trừ border của parent)
            available_width = parent.contentsRect().width()

        # Nếu vẫn bằng 0 (lúc chưa hiện lên), dùng fallback
        if available_width <= 0:
            available_width = 400

        height = self.heightForWidth(available_width)
        size.setHeight(height)

        return size + QSize(
            margins.left() + margins.right(), margins.top() + margins.bottom()
        )

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing_h = self._h
        spacing_v = self._v

        margins = self.contentsMargins()
        # Tính rect khả dụng (trừ margin)
        effective_rect = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )

        x = effective_rect.x()
        y = effective_rect.y()
        max_x = effective_rect.right()  # Giới hạn bên phải

        for item in self._items:
            # --- SỬA LỖI QUAN TRỌNG Ở ĐÂY ---
            # Không dùng w.isVisible() vì nó trả về False khi parent chưa hiện.
            # Dùng item.isEmpty() chuẩn hơn cho Layout.
            if item.isEmpty():
                continue

            wid = item.widget()
            # Nếu widget bị ẩn chủ động (hide()) thì mới bỏ qua
            if wid and wid.isHidden():
                continue
            # --------------------------------

            hint = item.sizeHint()
            next_x = x + hint.width()

            # Nếu item tràn ra ngoài biên phải -> Xuống dòng
            if next_x > max_x and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + spacing_v
                next_x = x + hint.width()
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x + spacing_h
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y()  # Trả về chiều cao nội dung thực tế
