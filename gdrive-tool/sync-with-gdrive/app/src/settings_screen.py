from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
)
from PySide6.QtCore import Qt
from mixins.keyboard_shortcuts import KeyboardShortcutsDialogMixin
from components.label import CustomLabel
from components.button import CustomButton
from configs.configs import ThemeColors


class KeyboardShortcutsWidget(QWidget):
    """Widget hiển thị danh sách phím tắt theo sections"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = CustomLabel("Các phím tắt khả dụng", is_bold=True, font_size=18)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Scroll area cho nội dung
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4d4d4d;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5d5d5d;
            }
        """
        )

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 10, 0)
        content_layout.setSpacing(24)

        # Section 1: Màn hình chính
        content_layout.addWidget(
            self._create_section(
                "Màn hình chính",
                [
                    ("Ctrl+Q hoặc Alt+Q", "Thoát ứng dụng"),
                    ("Ctrl+Enter", "Bắt đầu đồng bộ ngay"),
                    ("Ctrl+O", "Mở dialog chọn thư mục/tệp"),
                    ("Ctrl+I", "Mở cửa sổ cài đặt"),
                ],
            )
        )

        # Section 2: Chọn kho lưu trữ
        content_layout.addWidget(
            self._create_section(
                "Cửa sổ chọn kho lưu trữ",
                [
                    ("Ctrl+Q hoặc Alt+Q", "Đóng cửa sổ"),
                ],
            )
        )

        # Section 3: Tiến trình đồng bộ
        content_layout.addWidget(
            self._create_section(
                "Cửa sổ tiến trình đồng bộ",
                [
                    ("Ctrl+Q hoặc Alt+Q", "Đóng cửa sổ"),
                ],
            )
        )

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def _create_section(self, title: str, shortcuts: list[tuple[str, str]]) -> QFrame:
        """Tạo một section hiển thị phím tắt"""
        section = QFrame()
        section.setObjectName("ShortcutSection")
        section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(section)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Section title
        title_label = CustomLabel(title, is_bold=True, font_size=14)
        title_label.setStyleSheet(f"color: {ThemeColors.MAIN};")
        layout.addWidget(title_label)

        # Shortcuts list
        for key, description in shortcuts:
            shortcut_item = self._create_shortcut_item(key, description)
            layout.addWidget(shortcut_item)

        section.setStyleSheet(
            f"""
            QFrame#ShortcutSection {{
                background-color: rgba(255, 255, 255, 8);
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 8px;
            }}
        """
        )

        return section

    def _create_shortcut_item(self, key: str, description: str) -> QWidget:
        """Tạo một dòng hiển thị phím tắt"""
        item = QWidget()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)

        # Key label (phím tắt)
        key_label = CustomLabel(key, is_bold=True, font_size=12)
        key_label.setStyleSheet(
            f"""
            CustomLabel {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                color: {ThemeColors.MAIN};
                padding: 4px 12px 6px;
                border-radius: 4px;
                border: 1px solid {ThemeColors.GRAY_BORDER};
            }}
        """
        )
        key_label.setFixedWidth(180)
        layout.addWidget(key_label)

        # Description label
        desc_label = CustomLabel(description, font_size=12)
        desc_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(desc_label, 1)

        return item


class MenuButton(CustomButton):
    """Nút menu trong sidebar"""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent, is_bold=False, font_size=13)
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_active = False
        self._update_style()

    def set_active(self, active: bool):
        """Đánh dấu nút đang được chọn"""
        self._is_active = active
        self._update_style()

    def _update_style(self):
        if self._is_active:
            self.setStyleSheet(
                f"""
                MenuButton {{
                    background-color: {ThemeColors.MAIN};
                    color: black;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 16px;
                    font-weight: bold;
                }}
            """
            )
        else:
            self.setStyleSheet(
                f"""
                MenuButton {{
                    background-color: transparent;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 16px;
                }}
                MenuButton:hover {{
                    background-color: rgba(255, 255, 255, 10);
                }}
            """
            )


class SettingsScreen(KeyboardShortcutsDialogMixin):
    """Cửa sổ thiết lập cho ứng dụng."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt")
        self.resize(800, 600)
        self._menu_buttons: list[MenuButton] = []
        self._setup_ui()

    def _setup_ui(self):
        """Thiết lập giao diện"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar (menu bên trái)
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Main content area (bên phải)
        self._content_stack = QStackedWidget()
        self._content_stack.setStyleSheet(
            f"QStackedWidget {{ background-color: {ThemeColors.GRAY_BACKGROUND}; }}"
        )

        # Thêm các page vào stack
        self._content_stack.addWidget(KeyboardShortcutsWidget())  # Index 0: Phím tắt

        main_layout.addWidget(self._content_stack, 1)

        # Set page đầu tiên
        self._switch_page(0)

        # Style tổng thể
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
            }}
        """
        )

    def _create_sidebar(self) -> QFrame:
        """Tạo sidebar menu"""
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(200)
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title
        title = CustomLabel("Cài đặt", is_bold=True, font_size=16)
        title.setStyleSheet("color: white; padding: 8px 0px;")
        layout.addWidget(title)

        # Menu items
        keyboard_btn = MenuButton("⌨️  Phím tắt")
        keyboard_btn.on_clicked(lambda: self._switch_page(0))
        self._menu_buttons.append(keyboard_btn)
        layout.addWidget(keyboard_btn)

        # Spacer để đẩy menu lên trên
        layout.addStretch()

        sidebar.setStyleSheet(
            f"""
            QFrame#Sidebar {{
                background-color: #252525;
                border-right: 1px solid {ThemeColors.GRAY_BORDER};
            }}
        """
        )

        return sidebar

    def _switch_page(self, index: int):
        """Chuyển đổi giữa các page"""
        self._content_stack.setCurrentIndex(index)

        # Update active state của buttons
        for i, btn in enumerate(self._menu_buttons):
            btn.set_active(i == index)
