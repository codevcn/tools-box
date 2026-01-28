from PySide6.QtWidgets import (
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QProgressBar,
    QFrame,
    QWidget,
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QCloseEvent
from .utils.helpers import get_svg_as_icon
from .configs.configs import ThemeColors
from .workers.sync_worker import SyncProgressData
from .components.label import CustomLabel
from .components.button import CustomButton
from .mixins.keyboard_shortcuts import KeyboardShortcutsDialogMixin
from .components.overlay import PositionedOverlay


class SyncProgressItem(QFrame):
    """
    Widget con đại diện cho 1 dòng trong danh sách.
    Gồm: Icon status | Tên file | Progress Bar | % text
    """

    def __init__(self, file_name: str, parent=None):
        super().__init__(parent)
        self._setup_ui(file_name)

    def _setup_ui(self, file_name):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)

        # 1. Status Icon (Dùng Label để hiện text unicode hoặc icon)
        self.label_icon = CustomLabel(font_size=14, is_bold=True)
        self.label_icon.setFixedSize(24, 24)
        self.label_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Mặc định là icon loading (hoặc dấu chấm tròn)
        self.label_icon.setStyleSheet(
            f"""
            CustomLabel {{
                border-radius: 12px;
            }}
        """
        )
        self.label_icon.setPixmap(
            get_svg_as_icon("info_icon", 22, "#555555", "#ffffff", 3)
        )
        layout.addWidget(self.label_icon)

        # 2. Thông tin file (Tên + Progress Bar)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.label_name = CustomLabel(file_name, is_bold=False, font_size=14)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)  # Thanh nhỏ gọn
        self.progress_bar.setTextVisible(False)  # Ẩn text trên thanh
        self.progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                background-color: #444;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.MAIN}; 
                border-radius: 3px;
            }}
        """
        )

        info_layout.addWidget(self.label_name)
        info_layout.addWidget(self.progress_bar)
        layout.addLayout(info_layout)

        # 3. Phần trăm text (bên phải cùng)
        self.label_percent = CustomLabel("0%", is_bold=True)
        self.label_percent.setFixedWidth(50)
        self.label_percent.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.label_percent.setStyleSheet("color: #aaa;")
        layout.addWidget(self.label_percent)

    def update_progress(self, percent: float):
        """Cập nhật tiến độ"""
        self.progress_bar.setValue(int(percent))
        self.label_percent.setText(f"{percent}%")

        if percent >= 100:
            self.set_finished()

    def set_finished(self):
        """Chuyển sang trạng thái hoàn thành (Tick xanh)"""
        self.progress_bar.setValue(100)
        self.label_percent.setText("Xong")
        self.label_percent.setStyleSheet(
            f"color: {ThemeColors.SUCCESS};"
        )  # Màu xanh lá

        # Đổi icon thành dấu tích V
        self.label_icon.setPixmap(
            get_svg_as_icon("check_icon", 14, ThemeColors.SUCCESS, "#ffffff", 3)
        )
        self.label_icon.setStyleSheet(
            f"""
            CustomLabel {{
                background-color: {ThemeColors.SUCCESS}; 
                border-radius: 12px;
            }}
        """
        )


class SyncProgressDialog(KeyboardShortcutsDialogMixin):
    cancel_requested = Signal()

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle("Danh sách đồng bộ")
        self.resize(500, 400)

        # Dictionary để map tên file -> Widget dòng tương ứng
        # Key: file_name, Value: SyncProgressItem
        self._items_map: dict[str, SyncProgressItem] = {}

        self._setup_ui()
        self._apply_styles()

    def closeEvent(self, event: QCloseEvent) -> None:
        # ví dụ: hỏi xác nhận
        self._on_cancel()
        super().closeEvent(event)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()
        self.label_title = CustomLabel(
            "Tiến trình chi tiết", font_size=14, is_bold=True
        )
        header_layout.addWidget(self.label_title)
        layout.addLayout(header_layout)

        # List Widget (Container chứa các dòng)
        self.list_widget = QListWidget()
        self.list_widget.setContentsMargins(0, 0, 6, 0)
        self.list_widget.setSelectionMode(
            QListWidget.SelectionMode.NoSelection
        )  # Không cho user chọn dòng
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        layout.addWidget(self.list_widget)

        empty_text = CustomLabel("Bắt đầu đồng bộ...", font_size=14)
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_text_overlay = PositionedOverlay(
            self.list_widget.viewport(), empty_text
        )

        # Footer Button
        self.btn_cancel = CustomButton("Hủy đồng bộ", is_bold=True, font_size=14)
        self.btn_cancel.setContentsMargins(0, 8, 0, 0)
        self.btn_cancel.setObjectName("BtnCancelSync")
        self.btn_cancel.on_clicked(self._on_cancel)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

    def _apply_styles(self):
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                color: white;
            }}
            QListWidget {{
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                outline: none;
            }}
            #BtnCancelSync {{
                background-color: {ThemeColors.STRONG_GRAY};
                color: black;
                border-radius: 4px;
                border: 1px solid #555;
                padding: 4px 18px 6px;
            }}
        """
        )

    def update_item_progress(self, data: SyncProgressData):
        file_name = data.file_name
        percent = data.current_file_percent

        # Bỏ qua các tin nhắn hệ thống
        if file_name in ["Starting...", "Calculating...", "Finished"]:
            return

        # Kiểm tra xem file này đã có trong list chưa
        if file_name not in self._items_map:
            self._add_new_row(file_name)

        # Lấy widget ra và update
        progress_item = self._items_map[file_name]
        progress_item.update_progress(percent)

    def _add_new_row(self, file_name: str):
        # 1. Tạo Custom Widget
        item_widget = SyncProgressItem(file_name)

        # 2. Tạo QListWidgetItem (Container trong list)
        list_item = QListWidgetItem(self.list_widget)
        # Set size hint để list biết chiều cao của dòng (quan trọng)
        list_item.setSizeHint(QSize(0, 50))

        # 3. Gắn widget vào item
        self.list_widget.setItemWidget(list_item, item_widget)

        # 4. Lưu vào map để lần sau tìm lại update tiếp
        self._items_map[file_name] = item_widget

        # 5. Auto scroll xuống dưới cùng
        self.list_widget.scrollToBottom()

        self.hide_overlay()

    def hide_overlay(self):
        """Ẩn overlay thông báo trống nếu nó đang hiện"""
        if self.empty_text_overlay:
            self.empty_text_overlay.hide()  # Gọi hàm hide() vừa thêm ở overlay.py

    def show_overlay(self):
        """Hiện lại overlay thông báo trống"""
        if self.empty_text_overlay:
            self.empty_text_overlay.show()

    def _on_cancel(self):
        self.cancel_requested.emit()

    def reset(self):
        """
        Reset dialog về trạng thái ban đầu.
        Xoá hết các dòng.
        Enable nút hủy.
        """
        self.list_widget.clear()
        self._items_map.clear()
        self.btn_cancel.setText("Hủy đồng bộ")
        self.btn_cancel.setEnabled(True)
        self.show_overlay()
