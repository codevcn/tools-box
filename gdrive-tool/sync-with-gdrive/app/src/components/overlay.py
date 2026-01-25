from PySide6.QtWidgets import QFrame, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QColor


class CustomOverlay(QFrame):
    def __init__(
        self,
        parent_widget: QFrame,
        align=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        margin=10,
    ):
        super().__init__(
            parent_widget
        )  # QUAN TRỌNG: Gán parent là widget cụ thể cần đè lên

        self.align = align
        self.margin = margin
        self.parent_widget = parent_widget

        # 1. Cài đặt Event Filter để theo dõi kích thước cha
        self.parent_widget.installEventFilter(self)

        # 2. Setup giao diện cơ bản cho Frame này
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # 3. Thêm đổ bóng (Shadow) để tạo cảm giác nổi 3D
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

        # 4. Layout bên trong chính nó (để bạn nhét button, label vào)
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Tính vị trí ban đầu
        self.update_position()

        self.setStyleSheet("")

    def eventFilter(self, obj, event):
        if obj == self.parent_widget and event.type() == QEvent.Type.Resize:
            self.update_position()
        return super().eventFilter(obj, event)

    def update_position(self):
        # Logic tính toán y hệt như button
        p_rect = self.parent_widget.rect()

        # Resize lại frame này theo nội dung bên trong (fit content)
        self.adjustSize()

        my_w = self.width()
        my_h = self.height()

        x = self.margin
        y = self.margin

        if self.align & Qt.AlignmentFlag.AlignRight:
            x = p_rect.width() - my_w - self.margin
        elif self.align & Qt.AlignmentFlag.AlignHCenter:
            x = (p_rect.width() - my_w) // 2

        if self.align & Qt.AlignmentFlag.AlignBottom:
            y = p_rect.height() - my_h - self.margin
        elif self.align & Qt.AlignmentFlag.AlignVCenter:
            y = (p_rect.height() - my_h) // 2

        self.move(x, y)
        self.raise_()  # Đảm bảo luôn nằm trên
