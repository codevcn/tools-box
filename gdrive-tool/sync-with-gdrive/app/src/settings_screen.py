from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap
from mixins.keyboard_shortcuts import KeyboardShortcutsDialogMixin
from components.label import CustomLabel
from components.button import CustomButton
from configs.configs import ThemeColors
from utils.helpers import get_svg_as_icon


class KeyboardShortcuts(QFrame):
    """Widget hiển thị danh sách phím tắt theo sections"""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Title
        title = CustomLabel("Các phím tắt khả dụng", is_bold=True, font_size=17)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Scroll area cho nội dung
        scroll = QScrollArea()
        scroll.setObjectName("ShortcutsScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content_widget = QFrame()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 10, 0)
        content_layout.setSpacing(14)

        # Section 1: Màn hình chính
        content_layout.addWidget(
            self._create_section(
                "Màn hình chính",
                [
                    ("Ctrl + Q hoặc Alt + Q", "Thoát ứng dụng"),
                    ("Ctrl + Enter", "Bắt đầu đồng bộ ngay"),
                    ("Ctrl + O", "Mở dialog chọn thư mục/tệp"),
                    ("Ctrl + I", "Mở cửa sổ cài đặt"),
                ],
            )
        )

        # Section 2: Chọn kho lưu trữ
        content_layout.addWidget(
            self._create_section(
                "Cửa sổ chọn kho lưu trữ",
                [
                    ("Ctrl + Q hoặc Alt + Q", "Đóng cửa sổ"),
                ],
            )
        )

        # Section 3: Tiến trình đồng bộ
        content_layout.addWidget(
            self._create_section(
                "Cửa sổ tiến trình đồng bộ",
                [
                    ("Ctrl + Q hoặc Alt + Q", "Đóng cửa sổ"),
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
        layout.setSpacing(6)

        # Section title
        title_label = CustomLabel(title, is_bold=True, font_size=14)
        layout.addWidget(title_label)

        # Shortcuts list
        for key, description in shortcuts:
            shortcut_item = self._create_shortcut_item(key, description)
            layout.addWidget(shortcut_item)

        return section

    def _create_shortcut_item(self, key: str, description: str) -> QFrame:
        """Tạo một dòng hiển thị phím tắt"""
        item = QFrame()
        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        # Key label (phím tắt)
        key_label = CustomLabel(key, is_bold=True, font_size=12)
        key_label.setObjectName("ShortcutKeyLabel")
        layout.addWidget(key_label)

        # Description label
        desc_label = CustomLabel(description, font_size=12)
        desc_label.setStyleSheet("color: #cccccc;")
        layout.addWidget(desc_label, 1)

        return item


class MenuButton(CustomButton):
    """Nút menu trong sidebar"""

    def __init__(
        self,
        text: str,
        icon: QPixmap | None = None,
        is_bold: bool = False,
        font_size: int = 13,
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent, is_bold=is_bold, font_size=font_size)
        self.setObjectName("MenuButtonRoot")
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._is_active = False
        if icon:
            self.setIcon(icon)
        self._update_style()

    def set_active(self, active: bool):
        """Đánh dấu nút đang được chọn"""
        self._is_active = active
        self._update_style()

    def _update_style(self):
        if self._is_active:
            self.setStyleSheet(
                f"""
                #MenuButtonRoot {{
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
                #MenuButtonRoot {{
                    background-color: transparent;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 16px;
                }}
                #MenuButtonRoot:hover {{
                    background-color: rgba(255, 255, 255, 10);
                }}
            """
            )


class SettingsScreen(KeyboardShortcutsDialogMixin):
    """Cửa sổ thiết lập cho ứng dụng."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Cài đặt")
        self.resize(800, 500)
        self._menu_buttons: list[MenuButton] = []
        self._setup_ui()

    def _setup_ui(self):
        """Thiết lập giao diện"""
        self.setObjectName("SettingsScreenRoot")
        self.setStyleSheet(
            f"""
            #MenuSideBarRoot {{
                background-color: #252525;
                border-right: 1px solid {ThemeColors.GRAY_BORDER};
            }}
            #ShortcutKeyLabel {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                color: {ThemeColors.MAIN};
                padding: 4px 8px 6px;
                border-radius: 4px;
                border: 1px solid {ThemeColors.GRAY_BORDER};
            }}
            #ShortcutSection {{
                background-color: rgba(255, 255, 255, 8);
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 8px;
            }}
            #ShortcutsScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: #4d4d4d;
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #4d4d4d;
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #323232;
            }}
            #CloseSettingsButton {{
                background-color: {ThemeColors.STRONG_GRAY};
                color: black;
            }}
            """
        )
        "#323232"

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar (menu bên trái)
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)

        # Main content area (bên phải)
        self._content_stack = QStackedWidget()

        # Thêm các page vào stack
        self._content_stack.addWidget(KeyboardShortcuts())  # Index 0: Phím tắt

        main_layout.addWidget(self._content_stack, 1)

        # Set page đầu tiên
        QTimer.singleShot(0, lambda: self._switch_page(0))

    def _create_sidebar(self) -> QFrame:
        """Tạo sidebar menu"""
        sidebar = QFrame()
        sidebar.setObjectName("MenuSideBarRoot")
        sidebar.setFixedWidth(200)
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title
        title = CustomLabel("Cài đặt", is_bold=True, font_size=15)
        title.setStyleSheet("color: white; padding: 8px 0px;")
        layout.addWidget(title)

        # Menu buttons
        menu_buttons = self._create_menu_buttons()
        for btn in menu_buttons:
            layout.addWidget(btn)

        # Spacer để đẩy menu lên trên
        layout.addStretch()

        close_settings_btn = MenuButton(
            "Đóng cài đặt",
            is_bold=True,
        )
        close_settings_btn.setContentsMargins(0, 0, 0, 12)
        close_settings_btn.setObjectName("CloseSettingsButton")
        close_settings_btn.setIconSize(QSize(26, 26))
        close_settings_btn.on_clicked(self.accept)
        layout.addWidget(close_settings_btn)

        return sidebar

    def _create_menu_buttons(self) -> list[MenuButton]:
        """Render lại trạng thái của các nút menu"""
        # Phím tắt keyboard shortcuts
        keyboard_btn = MenuButton(
            "Phím tắt",
            get_svg_as_icon("keyboard_icon", 26, None, "#000000", 3, (0, 0, 8, 0)),
        )
        keyboard_btn.setIconSize(QSize(26, 26))
        keyboard_btn.on_clicked(lambda: self._switch_page(0))
        self._menu_buttons.append(keyboard_btn)

        return [keyboard_btn]

    def _switch_page(self, index: int):
        """Chuyển đổi giữa các page"""
        self._content_stack.setCurrentIndex(index)

        # Update active state của buttons
        for i, btn in enumerate(self._menu_buttons):
            btn.set_active(i == index)
