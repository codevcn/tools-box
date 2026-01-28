from PySide6.QtWidgets import QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from typing import Callable
from ..components.loading import LoadingDots


class CustomButton(QPushButton):
    def __init__(
        self,
        text="",
        parent=None,
        default_enabled=True,
        is_bold: bool = True,
        font_size: int | None = None,
        fixed_height: int | None = None,
        fixed_width: int | None = None,
    ):
        super().__init__(text, parent)

        self.setEnabled(bool(default_enabled))

        font = self.font()
        if is_bold:
            font.setBold(True)
        if font_size is not None:
            font.setPointSize(font_size)
        self.setFont(font)

        if fixed_height:
            self.setFixedHeight(fixed_height)
        if fixed_width:
            self.setFixedWidth(fixed_width)

    # --- Các method cũ ---
    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        if enabled:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ForbiddenCursor)

    def on_clicked(self, func: Callable) -> None:
        self.clicked.connect(func)

    def set_text_force_adjust_size(self, text: str) -> None:
        """Cập nhật text của nút và điều chỉnh kích thước."""
        super().setText(text)
        self.adjustSize()  # Điều chỉnh kích thước nút theo text mới

    def switch_text_and_icon(
        self,
        text: str | None = None,
        icon: QPixmap | None = None,
        icon_size: int | None = None,
    ) -> None:
        """Thay thế text của nút bằng một icon."""
        if text:
            self.clear_icon()
            self.setText(text)
        elif icon:
            self.setText("")
            self.setIcon(icon)
            size = icon_size if icon_size else 14
            self.setIconSize(QSize(size, size))

    def clear_icon(self) -> None:
        """Remove icon hiện tại khỏi button."""
        self.setIcon(QIcon())
        self.setIconSize(self.iconSize())  # optional, để giữ size không đổi

    def update_icon_color(self, color: str, size: int | None = None) -> None:
        """
        Đổi màu icon hiện tại.
        Fix lỗi: Tự động giữ nguyên độ phân giải gốc của ảnh thay vì co về size mặc định.
        """
        current_icon = super().icon()
        if current_icon.isNull():
            return

        # --- FIX 1: Xác định kích thước vẽ (Render Size) ---
        if size is not None:
            # Nếu user chỉ định size cụ thể -> Dùng size đó
            render_size = QSize(size, size)
        else:
            # Nếu không chỉ định -> Lấy kích thước THỰC TẾ lớn nhất của ảnh gốc
            # QSize(1024, 1024) là giới hạn trên để Qt tìm size ảnh gốc to nhất có thể
            actual_size = current_icon.actualSize(QSize(1024, 1024))

            # Phòng trường hợp actualSize trả về quá bé (ví dụ icon rỗng),
            # ta lấy max giữa nó và iconSize hiện tại của nút
            current_btn_size = self.iconSize()
            render_size = QSize(
                max(actual_size.width(), current_btn_size.width()),
                max(actual_size.height(), current_btn_size.height()),
            )

        # 3. Trích xuất Pixmap từ Icon ở kích thước đã tính
        src_pixmap = current_icon.pixmap(render_size)

        if src_pixmap.isNull():
            return

        # 4. Tạo canvas vẽ
        dest_pixmap = QPixmap(render_size)
        dest_pixmap.fill(Qt.GlobalColor.transparent)

        # 5. Tô màu (Masking)
        painter = QPainter(dest_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        painter.drawPixmap(0, 0, src_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(dest_pixmap.rect(), QColor(color))
        painter.end()

        # 6. Cập nhật Icon mới
        new_icon = QIcon(dest_pixmap)

        super().setIcon(new_icon)

        # --- FIX 2: Chỉ đổi kích thước hiển thị của nút NẾU user truyền tham số size ---
        # Nếu size=None, ta chỉ đổi màu ảnh, còn kích thước hiển thị giữ nguyên như cũ
        if size is not None:
            self.setIconSize(render_size)


class LoadingButton(CustomButton):
    def __init__(
        self,
        text="",
        parent=None,
        default_enabled=True,
        is_bold: bool = True,
        font_size: int | None = None,
        fixed_height: int | None = None,
        fixed_width: int | None = None,
        # --- Tham số mới cho Loading ---
        loader_color: str = "#000000",  # Màu mặc định của dots (trắng cho nút màu đậm)
        loader_size: int = 10,  # Kích thước dot nhỏ gọn cho nút
    ):
        super().__init__(
            text, parent, default_enabled, is_bold, font_size, fixed_height, fixed_width
        )

        # Khởi tạo state trước (để tránh lỗi khi setEnabled gọi) ---
        self._is_loading = False
        self._original_text = text
        self._original_icon = self.icon()

        # Tạo layout để căn giữa loader
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Khởi tạo LoadingDots (ẩn mặc định)
        self._loader = LoadingDots(
            parent=self,
            dot_count=3,
            dot_size=loader_size,
            color=loader_color,
            spacing=4,  # Khoảng cách nhỏ lại cho vừa nút
        )
        self._loader.hide()  # Quan trọng: Phải ẩn lúc đầu

        # Thêm vào layout
        self._layout.addWidget(self._loader)

    # --- Các method cũ ---
    def setEnabled(self, enabled: bool) -> None:
        # Nếu đang loading thì không cho phép enable lại (tránh logic sai)
        if getattr(self, "_is_loading", False) and enabled:
            return

        super().setEnabled(enabled)

    def setIcon(self, icon: QIcon | QPixmap) -> None:
        if not self._is_loading:
            self._original_icon = icon
        return super().setIcon(icon)

    # --- 3. Method mới để điều khiển Loading ---
    def start_loading(self):
        """Bắt đầu hiệu ứng loading: Ẩn text, hiện dots, disable nút."""
        if self._is_loading:
            return

        self._is_loading = True
        self._original_text = self.text()  # Lưu text hiện tại (ví dụ "Login")
        self._original_icon = self.icon()

        self.setText("")  # Xóa text để chỗ cho loader
        self.clear_icon()  # Xóa icon nếu có
        super().setEnabled(
            False
        )  # Disable nút (dùng super để tránh logic setEnabled ở trên chặn)

        self._loader.show()  # Hiện widget
        self._loader.start()  # Chạy animation

    def stop_loading(self):
        """Kết thúc loading: Ẩn dots, trả lại text, enable nút."""
        if not self._is_loading:
            return

        self._is_loading = False

        self._loader.stop()  # Dừng animation
        self._loader.hide()  # Ẩn widget

        self.setText(self._original_text)  # Trả lại text cũ
        self.setIcon(
            self._original_icon if not self._original_icon.isNull() else QIcon()
        )
        self.setEnabled(True)  # Enable lại nút

    def configure_loader(
        self,
        color: str | None = None,
        size: int | None = None,
        speed: float | None = None,
        stagger_delay: int | None = None,
    ):
        """
        Cho phép sửa đổi giao diện loading sau khi button đã tạo.
        """
        # Gọi hàm update_properties của LoadingDots v2.0
        self._loader.update_properties(
            color=color, dot_size=size, speed_factor=speed, stagger_delay=stagger_delay
        )

    def update_icon_color(self, color: str, size: int | None = None) -> None:
        """
        Đổi màu icon hiện tại.
        Fix lỗi: Tự động giữ nguyên độ phân giải gốc của ảnh thay vì co về size mặc định.
        """
        current_icon = super().icon()
        if current_icon.isNull():
            return

        # --- FIX 1: Xác định kích thước vẽ (Render Size) ---
        if size is not None:
            # Nếu user chỉ định size cụ thể -> Dùng size đó
            render_size = QSize(size, size)
        else:
            # Nếu không chỉ định -> Lấy kích thước THỰC TẾ lớn nhất của ảnh gốc
            # QSize(1024, 1024) là giới hạn trên để Qt tìm size ảnh gốc to nhất có thể
            actual_size = current_icon.actualSize(QSize(1024, 1024))

            # Phòng trường hợp actualSize trả về quá bé (ví dụ icon rỗng),
            # ta lấy max giữa nó và iconSize hiện tại của nút
            current_btn_size = self.iconSize()
            render_size = QSize(
                max(actual_size.width(), current_btn_size.width()),
                max(actual_size.height(), current_btn_size.height()),
            )

        # 3. Trích xuất Pixmap từ Icon ở kích thước đã tính
        src_pixmap = current_icon.pixmap(render_size)

        if src_pixmap.isNull():
            return

        # 4. Tạo canvas vẽ
        dest_pixmap = QPixmap(render_size)
        dest_pixmap.fill(Qt.GlobalColor.transparent)

        # 5. Tô màu (Masking)
        painter = QPainter(dest_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        painter.drawPixmap(0, 0, src_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(dest_pixmap.rect(), QColor(color))
        painter.end()

        # 6. Cập nhật Icon mới
        new_icon = QIcon(dest_pixmap)

        if not self._is_loading:
            self._original_icon = new_icon

        super().setIcon(new_icon)

        # --- FIX 2: Chỉ đổi kích thước hiển thị của nút NẾU user truyền tham số size ---
        # Nếu size=None, ta chỉ đổi màu ảnh, còn kích thước hiển thị giữ nguyên như cũ
        if size is not None:
            self.setIconSize(render_size)
