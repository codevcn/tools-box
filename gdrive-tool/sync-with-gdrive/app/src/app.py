import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFileDialog,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import QProcess, QSize, Qt, QTimer
from components.scrollable_text import ScrollableText
from login_gdrive_screen import LoginGDriveScreen, LoginResult
from components.popup import CustomPopup
from components.divider import CustomDivider
from utils.helpers import (
    detect_content_type_by_file_extension,
    detect_file_extension,
    detect_path_type,
    extract_filename_with_ext,
    get_svg_as_icon,
    get_svg_file_path,
    svg_to_pixmap,
)
from components.flow_layout import CustomFlowLayout
from components.selected_file_box import FileInfoBox
from components.label import CustomLabel
from components.select_box import CustomSelectBox, SelectOption
from workers.sync_worker import RcloneSyncWorker, SyncAction, SyncOptions
from data.data_manager import ConfigSchema, DataManager
from configs.configs import SyncError, ThemeColors
from components.button import CustomButton


class MainWindow(QWidget):
    """Main window cho ứng dụng sync folder."""

    def __init__(self, local_paths: list[str]):
        super().__init__()
        self._sync_worker: RcloneSyncWorker
        self._data_manager: DataManager = DataManager()
        self._root_layout: QVBoxLayout
        self._top_menu_layout: QHBoxLayout
        self._local_paths_list = local_paths
        self._active_remote_select_box: CustomSelectBox
        self._gdrive_path_input: QLineEdit
        self._current_gdrive_path: str = ""
        self._active_remote: str
        self._selected_docs_preview: QWidget | None = None
        self._selected_docs_layout: QVBoxLayout
        self._sync_btn: CustomButton | None = None
        self._is_syncing: bool = False
        self._log_output: ScrollableText
        self._right_actions_layout: QHBoxLayout
        self._setup_ui()
        self._set_local_paths_list(local_paths)

    def _set_local_paths_list(self, paths: list[str]) -> None:
        self._local_paths_list = paths
        self._render_selected_docs_preview()

    def _close_app(self) -> None:
        """Đóng ứng dụng."""
        QApplication.quit()
        sys.exit(0)

    def _setup_ui(self) -> None:
        """Thiết lập giao diện người dùng."""
        self.setWindowTitle("Đồng bộ với Google Drive")
        self.setMinimumWidth(800)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root_layout = QVBoxLayout(self)
        root_layout.setSizeConstraints(
            QVBoxLayout.SizeConstraint.SetMaximumSize,
            QVBoxLayout.SizeConstraint.SetFixedSize,
        )
        root_layout.setContentsMargins(12, 8, 12, 12)
        root_layout.setSpacing(4)
        self._root_layout = root_layout

        # Top menu section
        top_menu_frame = QFrame()
        top_menu_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._top_menu_layout = QHBoxLayout(top_menu_frame)
        self._top_menu_layout.setContentsMargins(0, 0, 0, 0)
        self._render_top_menu()

        # Divider
        divider = CustomDivider(Qt.Orientation.Horizontal)

        # Active remote info section
        active_remote_info_layout = self._create_active_remote_info()

        # GDrive folder section
        gdrive_layout = self._create_gdrive_path_section(
            "Đường dẫn thư mục đích trên Google Drive:",
            margins=(6, 8, 0, 0),
        )

        # Selected docs preview section
        self._selected_docs_layout = QVBoxLayout()
        self._selected_docs_layout.setSpacing(4)
        self._selected_docs_layout.setContentsMargins(0, 16, 0, 0)
        selected_docs_label = CustomLabel(
            "Tệp và thư mục được chọn trên máy:", is_bold=True
        )
        selected_docs_label.setContentsMargins(6, 0, 0, 0)
        self._selected_docs_layout.addWidget(selected_docs_label)

        # Output log section
        log_layout = self._create_log_section()

        # Main section layout
        main_layout_section = QVBoxLayout()
        main_layout_section.setContentsMargins(0, 0, 0, 0)
        main_layout_section.addWidget(top_menu_frame)
        main_layout_section.addWidget(divider)
        main_layout_section.addLayout(active_remote_info_layout)
        main_layout_section.addLayout(gdrive_layout)
        main_layout_section.addLayout(self._selected_docs_layout)
        main_layout_section.addLayout(log_layout)

        root_layout.addLayout(main_layout_section)
        self._render_sync_button_section()

        # Load saved user data
        self._load_saved_user_data()

    def _render_top_menu(self) -> None:
        # Nút Browse local folder (bên trái)
        left_actions_layout = QHBoxLayout()

        browse_btn = CustomButton("Chọn thư mục/tệp...")
        browse_btn.setIcon(
            svg_to_pixmap(
                get_svg_file_path("browse_file_icon")[0],
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

        # Nút Đăng nhập và Settings (bên phải)
        self._right_actions_layout = QHBoxLayout()

        # Thêm left và right vào top menu
        self._top_menu_layout.addLayout(left_actions_layout)
        self._top_menu_layout.addLayout(self._right_actions_layout)

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
        for path in self._local_paths_list:
            svg, prefix_path = get_svg_file_path("file_icon")
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

        if self._selected_docs_preview:
            self._selected_docs_layout.removeWidget(self._selected_docs_preview)
            self._selected_docs_preview.setParent(None)
            self._selected_docs_preview.deleteLater()
            self._selected_docs_preview = None

        self._selected_docs_preview = preview
        self._selected_docs_layout.addWidget(self._selected_docs_preview)

    def _create_active_remote_info(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)

        label = CustomLabel("Bạn đang đồng bộ lên kho lưu trữ:", is_bold=True)
        label.setContentsMargins(6, 0, 0, 0)

        # Lấy danh sách remotes từ data manager
        remotes = self._data_manager.get_remotes_list()

        # Tạo options cho select box
        options = [
            SelectOption(
                label=remote,
                value=remote,
                icon=get_svg_as_icon("gdrive_logo_icon", 18, None, "#ffffff", 2),
            )
            for remote in remotes
        ]

        # Tạo select box với active remote làm default
        default_value = self._active_remote if hasattr(self, "_active_remote") else None
        self._active_remote_select_box = CustomSelectBox(
            options=options,
            default_value=default_value,
            placeholder="Chọn kho lưu trữ...",
        )

        # Set margin cho select box
        self._active_remote_select_box.setContentsMargins(0, 0, 0, 0)
        self._active_remote_select_box.on_value_change(self._on_active_remote_change)

        layout.addWidget(label)
        layout.addWidget(self._active_remote_select_box)

        return layout

    # Callback khi value thay đổi
    def _on_active_remote_change(self, value: str | None, option: SelectOption | None):
        if value:
            self._active_remote = value
            # Lưu active remote vào data manager
            self._data_manager.save_active_remote(value)

    def _on_gdrive_path_input_enter_pressed(self) -> None:
        """Xử lý khi người dùng nhấn Enter trong input path."""
        self._on_sync_start()

    def _create_gdrive_path_section(
        self,
        label_text: str,
        default_base_dir: str | None = None,
        margins: tuple[int, int, int, int] | None = None,
    ) -> QVBoxLayout:
        """Tạo section cho input path với label và nút browse."""
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        label = CustomLabel(label_text, is_bold=True)
        if margins is not None:
            label.setContentsMargins(*margins)

        input_layout = QHBoxLayout()
        self._gdrive_path_input = QLineEdit()
        self._gdrive_path_input.returnPressed.connect(
            self._on_gdrive_path_input_enter_pressed
        )
        self._gdrive_path_input.setStyleSheet(
            f"""
            QLineEdit {{
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-bottom: 2px solid {ThemeColors.STRONG_GRAY};
                border-radius: 8px;
                padding: 4px 6px 6px;
            }}
            """
        )

        if default_base_dir:
            self._gdrive_path_input.setText(default_base_dir)
        self._gdrive_path_input.setPlaceholderText("Thư mục 1/Thư mục 2/Thư mục 3/...")

        input_layout.addWidget(self._gdrive_path_input)

        layout.addWidget(label)
        layout.addLayout(input_layout)

        return layout

    def _browse_local_folder(self) -> None:
        """Mở dialog để chọn local folder."""
        folder = QFileDialog.getExistingDirectory(
            self, "Chọn Local Folder", "", QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._set_local_paths_list([folder])

    def _on_login_gdrive_successful(
        self, login_result: LoginResult, remote_name: str, err_msg: str
    ) -> None:
        """Xử lý khi đăng nhập Google Drive thành công."""
        print(
            f">>> Login result: {login_result}, remote_name={remote_name}, err_msg={err_msg}"
        )
        self._load_saved_user_data()

    def _do_login_gdrive(self) -> None:
        """Mở popup đăng nhập Google Drive."""
        login_gdrive_screen = LoginGDriveScreen(self)
        login_gdrive_screen.login_result.connect(self._on_login_gdrive_successful)
        login_gdrive_screen.exec()

    def _create_log_section(self) -> QVBoxLayout:
        log_layout = QVBoxLayout()
        log_label = CustomLabel("Chi tiết đồng bộ:", is_bold=True)
        log_label.setContentsMargins(6, 16, 0, 0)
        self._log_output = ScrollableText(
            fixed_height=150,
            default_text="Đồng bộ ngay để xem chi tiết...",
        )
        self._log_output.set_contents_margins(6, 0, 6, 0)
        self._log_output.setStyleSheet(
            f"""
            #ScrollableTextScroll {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border-radius: 12px;
            }}
            #ScrollableTextLabel {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 12px;
                color: white;
            }}
            """
        )
        self._log_output.set_font_size(12)
        log_layout.addWidget(log_label)
        log_layout.addWidget(self._log_output)
        return log_layout

    def _append_log(self, text: str) -> None:
        self._log_output.setText(f"{text}\n" + self._log_output.get_text())

    def _render_sync_button_section(self) -> None:
        """Render nút đồng bộ và nút thoát."""
        if self._sync_btn:
            if self._is_syncing:
                self._sync_btn.setEnabled(False)
                self._sync_btn.setText("Đang đồng bộ...")
            else:
                self._sync_btn.setEnabled(True)
                self._sync_btn.setText("Đồng bộ ngay")
        else:
            self._sync_btn = CustomButton("Đồng bộ ngay", is_bold=True, fixed_height=48)
            self._sync_btn.setIcon(
                svg_to_pixmap(
                    get_svg_file_path("double_check_icon")[0],
                    30,
                    None,
                    "#000000",
                    3,
                    (0, 0, 8, 0),
                )
            )
            self._sync_btn.setIconSize(QSize(30, 30))
            self._sync_btn.setStyleSheet(
                f"""
                CustomButton {{
                    background-color: {ThemeColors.MAIN};
                    color: black;
                }}
                """
            )
            self._sync_btn.on_clicked(self._on_sync_start)

            quit_btn = CustomButton("Thoát", is_bold=True, fixed_height=48)
            quit_btn.setStyleSheet(
                f"""
                CustomButton {{
                    background-color: {ThemeColors.STRONG_GRAY};
                    color: black;
                }}
                """
            )
            quit_btn.on_clicked(self._close_app)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)
            btn_layout.setContentsMargins(0, 8, 0, 0)
            btn_layout.addWidget(quit_btn, 4)
            btn_layout.addWidget(self._sync_btn, 6)
            self._root_layout.addLayout(btn_layout)

    def _validate_inputs(self) -> tuple[bool, str, SyncError]:
        """Validate input paths trước khi sync."""
        if not self._local_paths_list:
            return (
                False,
                "Lỗi ứng dụng, vui lòng liên hệ với bộ phận hỗ trợ!",
                SyncError.INTERNAL,
            )

        active_remote = self._data_manager.get_active_remote()
        if not active_remote:
            return (
                False,
                "Vui lòng đăng nhập vào Google Drive để cấp quyền cho ứng dụng thực hiện đồng bộ!",
                SyncError.NEED_LOGIN,
            )

        gdrive_path = self._gdrive_path_input.text().strip()
        if not gdrive_path:
            return (
                False,
                '"Đường dẫn thư mục đích trên Google Drive" không được bỏ trống!',
                SyncError.COMMON,
            )

        return True, "", SyncError.NONE

    def _do_sync(self) -> None:
        """Thực hiện đồng bộ."""
        try:
            # Start sync with worker
            options = SyncOptions(action=SyncAction.ONLY_UPLOAD)

            self._current_gdrive_path = self._gdrive_path_input.text().strip()

            print(f">>> Creating sync worker with paths: {self._local_paths_list}")
            print(f">>> GDrive path: {self._current_gdrive_path}")

            self._sync_worker = RcloneSyncWorker(
                local_paths=self._local_paths_list,
                gdrive_path=self._current_gdrive_path,
                options=options,
            )

            self._sync_worker.log.connect(self._append_log)
            self._sync_worker.error.connect(self._on_sync_error)
            self._sync_worker.done.connect(self._on_sync_finished)

            print(">>> Starting sync worker...")
            self._sync_worker.start()
        except Exception as e:
            print(f">>> Exception in _do_sync: {e}")
            import traceback

            traceback.print_exc()
            self._on_sync_error(f"Lỗi khi khởi tạo đồng bộ: {str(e)}")

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
                    get_svg_file_path("info_icon")[0],
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
                    get_svg_file_path("warn_icon")[0],
                    35,
                    None,
                    "#ff0000",
                    margins=(0, 0, 8, 0),
                ),
            )
            popup.exec_and_get()
            return

        # Start sync
        self._is_syncing = True
        self._render_sync_button_section()
        self._log_output.clear_text()

        QTimer.singleShot(0, self._do_sync)

    def _on_sync_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        print(f">>> Sync finished with code={code}, status={status}")
        self._is_syncing = False
        self._render_sync_button_section()
        self._data_manager.save_last_gdrive_entered_dir(self._current_gdrive_path)
        pass

    def _on_sync_error(self, msg: str) -> None:
        print(f">>> Sync error: {msg}")
        self._is_syncing = False
        self._render_sync_button_section()
        popup = CustomPopup(
            self,
            title="Lỗi đồng bộ",
            text=msg,
            icon_pixmap=get_svg_as_icon(
                "error_icon",
                35,
                None,
                "#ff0000",
                margins=(0, 0, 8, 0),
            ),
        )
        popup.exec_and_get()
        pass

    def _render_sync_data(self, saved_user_data: ConfigSchema) -> None:
        """Hiển thị dữ liệu sync đã lưu."""
        active_remote = saved_user_data.get("active_remote")
        if saved_user_data.get("remotes") and active_remote:
            self._active_remote_select_box.set_active_value(active_remote)
            # Hiển thị nút Settings và gdrive root dir đã lưu (nếu có)
            last_gdrive_entered_dir = saved_user_data.get("last_gdrive_entered_dir")
            if last_gdrive_entered_dir:
                self._gdrive_path_input.setText(last_gdrive_entered_dir)
            settings_btn = CustomButton()
            settings_btn.setIcon(
                svg_to_pixmap(
                    get_svg_file_path("settings_icon")[0],
                    24,
                    None,
                    "#ffffff",
                )
            )
            settings_btn.setIconSize(QSize(24, 24))
            settings_btn.setStyleSheet(
                f"""
                CustomButton {{
                    background-color: {ThemeColors.GRAY_BACKGROUND};
                    color: black;
                }}
                """
            )
            settings_btn.setFixedHeight(36)
            settings_btn.setFixedWidth(36)
            settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._right_actions_layout.addWidget(settings_btn)
        else:
            login_btn = CustomButton("Đăng nhập Google Drive")
            login_btn.setIcon(
                svg_to_pixmap(
                    get_svg_file_path("login_icon")[0],
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
            self._right_actions_layout.addStretch()
            self._right_actions_layout.addWidget(login_btn)

    def _load_saved_user_data(self) -> None:
        """Tải dữ liệu người dùng đã lưu (nếu có)."""
        self._render_sync_data(self._data_manager.get_entire_config())


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
