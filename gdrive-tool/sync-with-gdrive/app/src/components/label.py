from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import Qt


class CustomLabel(QLabel):
    def __init__(
        self,
        text: str = "",
        parent=None,
        is_bold: bool = False,
        is_word_wrap: bool = False,
        align: Qt.AlignmentFlag | None = None,
        font_size: int | None = None,
    ):
        super().__init__("", parent)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setText(text)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if is_bold:
            font = self.font()
            font.setBold(True)
            self.setFont(font)
        if is_word_wrap:
            self.setWordWrap(True)
        if align:
            self.setAlignment(align)
        if font_size:
            self.set_font_size(font_size)

    def set_font_size(self, font_size: int):
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)


class AutoHeightLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        # Để Vertical là Minimum hoặc Preferred để nó linh hoạt hơn Fixed
        # Nhưng nếu bạn muốn fix cứng height sau khi tính toán thì dùng Fixed cũng được
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def resizeEvent(self, event):
        # Gọi xử lý mặc định trước
        super().resizeEvent(event)
        # Chỉ cập nhật chiều cao, không set ngay để tránh loop
        self._update_height()

    def setText(self, text):
        super().setText(text)
        self._update_height()

    def _update_height(self):
        # Lấy chiều rộng khả dụng cho text (trừ đi margin trái/phải)
        margins = self.contentsMargins()
        available_width = self.width() - margins.left() - margins.right()

        if available_width <= 0:
            return

        text = self.text()
        if not text:
            self.setFixedHeight(
                margins.top() + margins.bottom()
            )  # Giữ lại margin nếu rỗng
            return

        fm = QFontMetrics(self.font())

        # Tính toán hình chữ nhật bao quanh text
        rect = fm.boundingRect(
            0,
            0,
            available_width,
            10_000,  # Chiều cao ảo tối đa
            Qt.TextFlag.TextWordWrap,
            text,
        )

        # Chiều cao mới = chiều cao text + margin trên + margin dưới
        new_height = rect.height() + margins.top() + margins.bottom()

        # QUAN TRỌNG: Chỉ set lại nếu chiều cao thực sự thay đổi
        # để tránh vòng lặp resizeEvent vô tận
        if self.height() != new_height:
            self.setFixedHeight(new_height)
