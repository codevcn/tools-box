import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFileDialog,
    QLabel,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import QProcess, QSize, Qt
from login_gdrive_screen import LoginGDriveScreen
from components.popup import CustomPopup
from components.divider import CustomDivider
from utils.helpers import (
    detect_content_type_by_file_extension,
    detect_file_extension,
    detect_path_type,
    extract_filename_with_ext,
    get_svg_file_path,
    svg_to_pixmap,
)
from components.flow_layout import CustomFlowLayout
from components.selected_file_box import FileInfoBox
from components.label import CustomLabel
from workers.sync_worker import RcloneSyncWorker
from data.data_manager import DataManager
from configs.configs import SyncError, ThemeColors
from components.button import CustomButton


class MainWindow(QWidget):
    """Main window cho ứng dụng sync folder."""

    def __init__(self, local_paths: list[str]):
        super().__init__()
        self.worker: RcloneSyncWorker
        self.dataManager: DataManager = DataManager()
        self.root_layout: QVBoxLayout
        self.top_menu_layout: QHBoxLayout
        self.local_paths_list = local_paths
        self.gdrive_path_input: QLineEdit
        self.selected_docs_preview: QWidget | None = None
        self.selected_docs_layout: QVBoxLayout
        self.sync_btn: CustomButton | None = None
        self.is_syncing: bool = False
        self.log_output: QLabel
        self._setup_ui()
        self._set_local_paths_list(local_paths)

    def _set_local_paths_list(self, paths: list[str]) -> None:
        self.local_paths_list = paths
        self._render_selected_docs_preview()

    def _setup_ui(self) -> None:
        """Thiết lập giao diện người dùng."""
        self.setWindowTitle("Đồng bộ với Google Drive")
        self.resize(900, 600)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 8, 12, 12)
        root_layout.setSpacing(4)
        self.root_layout = root_layout

        # Top menu section
        top_menu_frame = QFrame()
        self.top_menu_layout = QHBoxLayout(top_menu_frame)
        self.top_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._render_top_menu()

        # Divider
        divider = CustomDivider(Qt.Orientation.Horizontal)

        # Selected docs preview section
        self.selected_docs_layout = QVBoxLayout()
        self.selected_docs_layout.setSpacing(4)
        self.selected_docs_layout.setContentsMargins(0, 8, 0, 0)
        selected_docs_label = CustomLabel("Các tệp và thư mục được chọn:", is_bold=True)
        selected_docs_label.setContentsMargins(6, 0, 0, 0)
        self.selected_docs_layout.addWidget(selected_docs_label)

        # GDrive folder section
        gdrive_layout = self._create_path_input_section(
            "Đường dẫn thư mục đích trên Google Drive:",
            is_local=False,
            margins=(6, 16, 0, 0),
            default_base_dir=self.dataManager.get_saved_gdrive_root_dir(),
        )
        self.gdrive_path_input = gdrive_layout["input"]

        # Output log section

        # Main section layout
        main_layout_section = QVBoxLayout()
        main_layout_section.setContentsMargins(0, 0, 0, 0)
        main_layout_section.addWidget(top_menu_frame)
        main_layout_section.addWidget(divider)
        main_layout_section.addLayout(self.selected_docs_layout)
        main_layout_section.addLayout(gdrive_layout["layout"])
        # main_layout_section.addWidget(log_label)
        # main_layout_section.addWidget(self.log_output)
        main_layout_section.addStretch()

        root_layout.addLayout(main_layout_section)
        self._render_sync_button()

    def _render_top_menu(self) -> None:
        left_actions_layout = QHBoxLayout()

        # Nút Browse local folder (bên trái)
        browse_btn = CustomButton("Chọn thư mục/tệp...")
        browse_btn.setIcon(
            svg_to_pixmap(
                get_svg_file_path("browse_file_icon.svg")[0],
                26,
                None,
                "#000000",
                margins=(0, 0, 8, 0),
            )
        )
        browse_btn.setIconSize(QSize(26, 26))
        browse_btn.setStyleSheet(
            f"""
            CustomButton {{
                padding: 2px 12px 4px;
                background-color: {ThemeColors.MAIN};
                color: black;
            }}
            """
        )
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_local_folder)
        browse_btn_font = browse_btn.font()
        browse_btn_font.setBold(True)
        browse_btn_font.setPointSize(12)
        browse_btn.setFont(browse_btn_font)
        left_actions_layout.addWidget(browse_btn)
        left_actions_layout.addStretch()

        right_actions_layout = QHBoxLayout()

        # Nút Đăng nhập (bên phải)
        login_btn = CustomButton("Đăng nhập Google Drive")
        login_btn.setIcon(
            svg_to_pixmap(
                get_svg_file_path("login_icon.svg")[0],
                26,
                None,
                "#000000",
                margins=(0, 0, 8, 0),
            )
        )
        login_btn.setIconSize(QSize(26, 26))
        login_btn.setStyleSheet(
            f"""
            CustomButton {{
                padding: 2px 12px 4px;
                background-color: {ThemeColors.MAIN};
                color: black;
            }}
            """
        )
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(self._do_login_gdrive)
        login_btn_font = login_btn.font()
        login_btn_font.setBold(True)
        login_btn_font.setPointSize(12)
        login_btn.setFont(login_btn_font)
        right_actions_layout.addStretch()
        right_actions_layout.addWidget(login_btn)

        # Thêm left và right vào top menu
        self.top_menu_layout.addLayout(left_actions_layout)
        self.top_menu_layout.addLayout(right_actions_layout)

    def _render_sync_button(self) -> None:
        """Cập nhật trạng thái nút đồng bộ."""
        if self.sync_btn:
            if self.is_syncing:
                self.sync_btn.setEnabled(False)
                self.sync_btn.setText("Đang đồng bộ...")
            else:
                self.sync_btn.setEnabled(True)
                self.sync_btn.setText("Đồng bộ ngay")
        else:
            self.sync_btn = CustomButton("Đồng bộ ngay")
            self.sync_btn.setIcon(
                svg_to_pixmap(
                    get_svg_file_path("double_check_icon.svg")[0],
                    30,
                    None,
                    "#000000",
                    3,
                    (0, 0, 8, 0),
                )
            )
            self.sync_btn.setIconSize(QSize(30, 30))
            self.sync_btn.setStyleSheet(
                f"""
                CustomButton {{
                    background-color: {ThemeColors.MAIN};
                    color: black;
                }}
                """
            )
            self.sync_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            sync_btn_font = self.sync_btn.font()
            sync_btn_font.setBold(True)
            self.sync_btn.setFont(sync_btn_font)
            self.sync_btn.setFixedHeight(48)
            self.sync_btn.clicked.connect(self._on_sync_start)
            btn_layout = QVBoxLayout()
            btn_layout.setContentsMargins(0, 8, 0, 0)
            btn_layout.addWidget(self.sync_btn)
            self.root_layout.addLayout(btn_layout)

    def _render_selected_docs_preview(self) -> None:
        # Tạo CustomFlowLayout và lưu reference
        self.selected_docs_flow = CustomFlowLayout(
            margins=(0, 4, 0, 0), h_spacing=8, v_spacing=8
        )

        # Container để set layout
        preview = QWidget()
        preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        preview.setLayout(self.selected_docs_flow)

        # Thêm nhiều box để thấy wrap
        items: list[tuple[str, str]] = []
        for path in self.local_paths_list:
            svg, prefix_path = get_svg_file_path("file_icon.svg")
            path_type = detect_path_type(path)
            if path_type == "file":
                file_ext = detect_file_extension(path)
                content_type = detect_content_type_by_file_extension(file_ext or "")
                svg = f"{prefix_path}\\{content_type}_icon.svg"
            elif path_type == "folder":
                svg = f"{prefix_path}\\folder_icon.svg"
            items.append((svg, path))

        for svg, text in items:
            self.selected_docs_flow.addWidget(
                FileInfoBox(
                    svg_path=svg,
                    svg_fill_color=None,
                    svg_stroke_color="#ffffff",
                    text=extract_filename_with_ext(text),
                )
            )

        if self.selected_docs_preview:
            self.selected_docs_layout.removeWidget(self.selected_docs_preview)
            self.selected_docs_preview.setParent(None)
            self.selected_docs_preview.deleteLater()
            self.selected_docs_preview = None

        self.selected_docs_preview = preview
        self.selected_docs_layout.addWidget(self.selected_docs_preview)

    def _create_path_input_section(
        self,
        label_text: str,
        is_local: bool,
        default_base_dir: str | None = None,
        margins: tuple[int, int, int, int] | None = None,
    ) -> dict:
        """Tạo section cho input path với label và nút browse."""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        label = CustomLabel(label_text, is_bold=True)
        if margins is not None:
            label.setContentsMargins(*margins)

        input_layout = QHBoxLayout()
        input_field = QLineEdit()
        input_field.setStyleSheet(
            """
            QLineEdit {
                padding: 2px 6px 4px;
            }
            """
        )

        if default_base_dir:
            input_field.setText(default_base_dir)
        input_field.setPlaceholderText(
            "C:/Users/Nguyễn Văn A/Tài liệu"
            if is_local
            else "Thư mục 1/Thư mục 2/Thư mục 3/..."
        )

        result = {
            "layout": layout,
            "input": input_field,
        }

        if is_local:
            browse_btn = CustomButton("Browse...")
            browse_btn.setContentsMargins(0, 0, 0, 0)
            browse_btn.clicked.connect(self._browse_local_folder)
            input_layout.addWidget(input_field)
            input_layout.addWidget(browse_btn)
            result["browse_btn"] = browse_btn
        else:
            input_layout.addWidget(input_field)

        layout.addWidget(label)
        layout.addLayout(input_layout)

        return result

    def _browse_local_folder(self) -> None:
        """Mở dialog để chọn local folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn Local Folder", "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._set_local_paths_list([folder])

    def _do_login_gdrive(self) -> None:
        """Mở popup đăng nhập Google Drive."""
        login_gdrive_screen = LoginGDriveScreen(self)
        login_gdrive_screen.exec()

    def _validate_inputs(self) -> tuple[bool, str, SyncError]:
        """Validate input paths trước khi sync."""
        active_remote = self.dataManager.get_active_remote()
        if not active_remote:
            return (
                False,
                "Vui lòng đăng nhập vào Google Drive để cấp quyền cho ứng dụng thực hiện đồng bộ!",
                SyncError.NEED_LOGIN,
            )

        if not self.local_paths_list:
            return (
                False,
                "Trường thư mục trên máy không được bỏ trống!",
                SyncError.COMMON,
            )

        gdrive_path = self.gdrive_path_input.text().strip()
        if not gdrive_path:
            return (
                False,
                "Trường thư mục trên Google Drive không được bỏ trống!",
                SyncError.COMMON,
            )

        # Validate từng local path
        for local_path in self.local_paths_list:
            if not Path(local_path).exists():
                return (
                    False,
                    f"Thư mục không tồn tại trên máy: {local_path}",
                    SyncError.COMMON,
                )

        return True, "", SyncError.NONE

    def _do_sync(self) -> None:
        """Thực hiện đồng bộ."""
        # Start sync with worker
        gdrive_path = self.gdrive_path_input.text().strip()
        local_paths = self.local_paths_list

        self.worker = RcloneSyncWorker(local_paths, gdrive_path)

        # connect signals
        self.worker.log.connect(self._append_log)
        self.worker.done.connect(self._on_sync_finished)

        # chạy
        self.worker.sync_multi_entries()

    def _on_sync_start(self) -> None:
        """Xử lý khi người dùng nhấn nút Đồng bộ."""
        # Validate inputs
        is_valid, error_msg, err_type = self._validate_inputs()
        if err_type == SyncError.NEED_LOGIN:
            popup = CustomPopup(
                self,
                title="Yêu cầu đăng nhập",
                text=error_msg,
                icon_pixmap=svg_to_pixmap(
                    get_svg_file_path("info_icon.svg")[0],
                    35,
                    None,
                    "#00a0df",
                    margins=(0, 0, 8, 0),
                ),
            )
            popup.exec_and_get()
            return
        elif not is_valid:
            popup = CustomPopup(
                self,
                title="Lỗi",
                text=error_msg,
                icon_pixmap=svg_to_pixmap(
                    get_svg_file_path("warn_icon.svg")[0],
                    35,
                    None,
                    "#ff0000",
                    margins=(0, 0, 8, 0),
                ),
            )
            popup.exec_and_get()
            return

        # Start sync
        self.is_syncing = True
        self._render_sync_button()
        self.log_output.clear()

        self._do_sync()

    def _render_log_section(self) -> None:
        log_label = CustomLabel("Chi tiết đồng bộ:", is_bold=True)
        log_label.setContentsMargins(6, 16, 0, 0)
        self.log_output = QLabel()
        self.log_output.setFixedHeight(100)

    def _append_log(self, text: str) -> None:
        self.log_output.setText(f"{text}\n" + self.log_output.text())

    def _on_sync_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        pass


def init_app() -> None:
    """Hàm khởi tạo ứng dụng."""
    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(14)
    app.setFont(font)

    # Lấy danh sách paths từ command line arguments
    local_paths = []
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.exists():
            local_paths.append(str(path.absolute()))
        else:
            print(f"⚠️ Path không tồn tại: {arg}")

    window = MainWindow(local_paths)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    init_app()
