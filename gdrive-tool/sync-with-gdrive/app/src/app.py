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
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtCore import QProcess, QSize, Qt, QTimer
from sync_progress import SyncProgressDialog
from components.tooltip import CollisionConstraint, ToolTipBinder, ToolTipConfig
from components.scrollable_text import ScrollableText
from login_gdrive_screen import LoginGDriveScreen, LoginResult
from active_remote_info import ActiveRemoteScreen
from components.announcement import CustomAnnounce
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
from workers.sync_worker import (
    RcloneSyncWorker,
    SyncAction,
    SyncOptions,
    SyncProgressData,
    SyncProgressStatus,
)

# from testing.mock_sync_worker import MockRcloneSyncWorker
from data.data_manager import ConfigSchema, DataManager
from configs.configs import PATH_TYPE, SyncError, ThemeColors
from components.button import CustomButton
from components.overlay import CustomOverlay
from settings_screen import SettingsScreen
import os
import subprocess


class MainWindow(QWidget):
    """Main window cho ứng dụng sync folder."""

    def __init__(self, local_paths: list[str]):
        super().__init__()
        self._sync_worker: RcloneSyncWorker | None = None
        # self._sync_worker: MockRcloneSyncWorker | None = None
        self._sync_progress_dialog: SyncProgressDialog | None = None
        self._data_manager: DataManager = DataManager()
        self._root_layout: QVBoxLayout
        self._top_menu_layout: QHBoxLayout
        self._local_paths_list = local_paths
        self._gdrive_path_input: QLineEdit
        self._current_gdrive_path: str = ""
        self._active_remote: str
        self._selected_docs_preview: QWidget | None = None
        self._selected_docs_layout: QVBoxLayout
        self._sync_btn: CustomButton | None = None
        self._is_syncing: bool = False
        self._log_output: ScrollableText
        self._right_actions_layout: QHBoxLayout
        self._active_remote_label: CustomLabel
        self._copy_log_btn: CustomButton
        self._settings_dialog: SettingsScreen | None = None
        self._setup_ui()
        self._set_local_paths_list(local_paths)
        self._add_catch_keyboard_shortcuts()

    def _set_local_paths_list(self, paths: list[str]) -> None:
        self._local_paths_list = paths
        self._render_selected_docs_preview()

    def _close_app(self) -> None:
        """Đóng ứng dụng."""
        QApplication.quit()
        sys.exit(0)

    def _add_catch_keyboard_shortcuts(self) -> None:
        """Bắt sự kiện nhấn các tổ hợp phím."""
        # Ctrl + Q (thoát ứng dụng)
        shortcut_ctrl_q = QShortcut(QKeySequence("Ctrl+Q"), self)
        shortcut_ctrl_q.activated.connect(self._close_app)

        # Alt + Q (thoát ứng dụng)
        shortcut_alt_q = QShortcut(QKeySequence("Alt+Q"), self)
        shortcut_alt_q.activated.connect(self._close_app)

        # Ctrl + Enter (đồng bộ ngay)
        shortcut_ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut_ctrl_enter.activated.connect(self._on_sync_start)

        # Ctrl + O (mở dialog chọn folder/tệp)
        shortcut_ctrl_o = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_ctrl_o.activated.connect(self._browse_local_folder)

        # Ctrl + I (mở settings)
        shortcut_ctrl_i = QShortcut(QKeySequence("Ctrl+I"), self)
        shortcut_ctrl_i.activated.connect(self._open_settings_screen)

    def _setup_ui(self) -> None:
        """Thiết lập giao diện người dùng."""
        self.setWindowTitle("Đồng bộ với Google Drive")
        self.setWindowIcon(QIcon("app/src/assets/app.ico"))
        self.setMinimumWidth(800)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        root_layout = QVBoxLayout(self)
        root_layout.setSizeConstraints(
            QVBoxLayout.SizeConstraint.SetMaximumSize,
            QVBoxLayout.SizeConstraint.SetFixedSize,
        )
        root_layout.setContentsMargins(12, 8, 12, 8)
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
            "Đường dẫn thư mục đích trên kho lưu trữ:",
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

    def _reveal_path_in_file_explorer(self, path: str) -> None:
        """Mở file explorer và chọn tệp/thư mục đã đồng bộ."""
        path = os.path.abspath(path)
        if os.path.isfile(path):
            # Mở explorer và select file
            subprocess.run(["explorer", "/select,", path])
        elif os.path.isdir(path):
            # Mở explorer tại folder
            subprocess.run(["explorer", path])
        else:
            raise FileNotFoundError(f"Path không tồn tại: {path}")

    def _render_selected_docs_preview(self) -> None:
        # Tạo CustomFlowLayout và lưu reference
        self.selected_docs_flow = CustomFlowLayout(
            margins=(0, 4, 0, 0), h_spacing=8, v_spacing=8
        )

        # Container để set layout
        preview = QFrame()
        preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        preview.setLayout(self.selected_docs_flow)

        # Thêm nhiều box để thấy wrap
        path_objects: list[tuple[str, str, PATH_TYPE]] = []
        for path in self._local_paths_list:
            svg, prefix_path = get_svg_file_path("file_icon")
            path_type = detect_path_type(path)
            if path_type == "file":
                file_ext = detect_file_extension(path)
                content_type = detect_content_type_by_file_extension(file_ext or "")
                svg = f"{prefix_path}\\{content_type}_icon.svg"
            elif path_type == "folder":
                svg = f"{prefix_path}\\folder_icon.svg"
            path_objects.append((svg, path, path_type))

        for svg, path_str, path_type in path_objects:
            file_info_box = FileInfoBox(
                svg_path=svg,
                svg_fill_color=None,
                svg_stroke_color="#ffffff",
                text=extract_filename_with_ext(path_str),
            )
            file_info_box.on_clicked(
                lambda path=path_str: self._reveal_path_in_file_explorer(path)
            )
            ToolTipBinder(
                file_info_box,
                ToolTipConfig(
                    text=f"<b>{'Thư mục' if path_type=='folder' else 'Tệp'}</b>: {path_str}",
                    show_delay_ms=100,
                    constrain_to=CollisionConstraint.SCREEN,
                ),
            )
            self.selected_docs_flow.addWidget(file_info_box)

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

        # Tạo bar để hiển thị active remote
        active_remote_bar = QFrame()
        active_remote_bar.setCursor(Qt.CursorShape.PointingHandCursor)
        active_remote_bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        active_remote_layout = QHBoxLayout(active_remote_bar)
        active_remote_layout.setContentsMargins(8, 4, 8, 6)
        active_remote_layout.setSizeConstraints(
            QHBoxLayout.SizeConstraint.SetMaximumSize,
            QHBoxLayout.SizeConstraint.SetFixedSize,
        )

        # Icon
        icon_label = CustomLabel()
        icon_label.setPixmap(get_svg_as_icon("gdrive_logo_icon", 20, None, None, 3))
        icon_label.setFixedSize(20, 20)
        active_remote_layout.addWidget(icon_label)

        # Text label
        self._active_remote_label = CustomLabel("Chọn kho lưu trữ...")
        self._active_remote_label.setStyleSheet("color: white;")
        self._active_remote_label.set_font_size(16)
        active_remote_layout.addWidget(self._active_remote_label, 1)

        # Expand icon
        expand_label = CustomLabel()
        expand_label.setPixmap(
            get_svg_as_icon("expand_icon", 20, "#ffffff", "#ffffff", 3)
        )
        expand_label.setFixedSize(20, 20)
        expand_label.setStyleSheet("color: white;")
        active_remote_layout.addWidget(expand_label)

        # Style cho bar
        active_remote_bar.setObjectName("ActiveRemoteBar")
        active_remote_bar.setStyleSheet(
            f"""
            #ActiveRemoteBar {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 8px;
            }}
            #ActiveRemoteBar:hover {{
                background-color: #3d3d3d;
            }}
        """
        )

        # Connect click event
        active_remote_bar.mousePressEvent = lambda e: self._open_active_remote_screen()

        layout.addWidget(label)
        layout.addWidget(active_remote_bar)

        return layout

    def _open_active_remote_screen(self):
        """Mở window để chọn active remote"""
        active_remote_screen = ActiveRemoteScreen(self)
        active_remote_screen.remote_selected.connect(self._on_remote_selected)
        active_remote_screen.exec()

    def _on_remote_selected(self, remote_name: str):
        """Callback khi user chọn remote từ window"""
        self._active_remote = remote_name
        self._active_remote_label.setText(remote_name)

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
                padding: 4px 8px 6px;
            }}
            QLineEdit:hover {{
                border-color: {ThemeColors.MAIN};
            }}
            QLineEdit:focus {{
                border-color: {ThemeColors.MAIN};
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
        self._load_saved_user_data()

    def _do_login_gdrive(self) -> None:
        """Mở popup đăng nhập Google Drive."""
        login_gdrive_screen = LoginGDriveScreen(self)
        login_gdrive_screen.login_result.connect(self._on_login_gdrive_successful)
        login_gdrive_screen.exec()

    def _on_copy_log(self) -> None:
        """Xử lý khi người dùng nhấn nút sao chép log."""
        QApplication.clipboard().setText(self._log_output.get_text())
        self._copy_log_btn.switch_text_and_icon(
            icon=get_svg_as_icon("double_check_icon", 20, None, "#ffffff", 2),
            icon_size=20,
        )
        QTimer.singleShot(
            2000, lambda: self._copy_log_btn.switch_text_and_icon(text="Sao chép")
        )

    def _create_log_section(self) -> QVBoxLayout:
        log_layout = QVBoxLayout()
        log_label = CustomLabel("Chi tiết đồng bộ:", is_bold=True)
        log_label.setContentsMargins(6, 16, 0, 0)
        self._log_output = ScrollableText(
            fixed_height=150,
            default_text="Đồng bộ ngay để xem chi tiết...",
        )
        self._log_output.set_contents_margins(10, 6, 10, 6)
        self._log_output.setStyleSheet(
            f"""
            #ScrollableTextScroll {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 12px;
            }}
            #ScrollableTextLabel {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border-radius: 12px;
                color: white;
            }}
            """
        )
        self._log_output.set_font_size(12)
        self.copy_log_btn_overlay = CustomOverlay(
            parent_widget=self._log_output,
            align=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
            margin=2,
        )
        self._copy_log_btn = CustomButton("Sao chép", fixed_height=28, font_size=11)
        self._copy_log_btn.setObjectName("CopyLogButton")
        self._copy_log_btn.setStyleSheet(
            f"""
            #CopyLogButton {{
                background-color: transparent;
                border: none;
                padding: 2px 6px 4px;
            }}
        """
        )
        self._copy_log_btn.on_clicked(self._on_copy_log)
        self.copy_log_btn_overlay.content_layout.addWidget(self._copy_log_btn)
        log_layout.addWidget(log_label)
        log_layout.addWidget(self._log_output)
        return log_layout

    def _write_log(self, text: str) -> None:
        self._log_output.setText(f"{text}")

    def _render_sync_button_section(self) -> None:
        """Render nút đồng bộ và nút thoát."""
        if self._sync_btn:
            if self._is_syncing:
                self._sync_btn.setEnabled(False)
                self._sync_btn.start_loading()
            else:
                self._sync_btn.setEnabled(True)
                self._sync_btn.stop_loading()
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
        # Start sync with worker
        options = SyncOptions(action=SyncAction.ONLY_UPLOAD)

        self._current_gdrive_path = self._gdrive_path_input.text().strip()
        self._sync_worker = RcloneSyncWorker(
            local_paths=self._local_paths_list,
            gdrive_path=self._current_gdrive_path,
            options=options,
            parent=self,
        )
        # self._sync_worker = MockRcloneSyncWorker(
        #     parent=self,
        # )

        self._sync_worker.log.connect(self._write_log)
        self._sync_worker.error.connect(self._on_sync_error)
        self._sync_worker.done.connect(self._on_sync_finished)
        self._sync_worker.progress.connect(self._on_sync_progress)

        self._sync_worker.start()

    def _on_sync_start(self) -> None:
        """Xử lý khi người dùng nhấn nút Đồng bộ."""
        # Validate inputs
        is_valid, error_msg, err_type = self._validate_inputs()
        if err_type == SyncError.NEED_LOGIN:
            popup = CustomAnnounce(
                self,
                title="Yêu cầu đăng nhập",
                text=error_msg,
                icon_pixmap=svg_to_pixmap(
                    get_svg_file_path("info_icon")[0],
                    35,
                    None,
                    ThemeColors.INFO,
                    margins=(0, 0, 8, 0),
                ),
            )
            popup.exec_and_get()
            return
        elif not is_valid:
            popup = CustomAnnounce(
                self,
                title="Lỗi",
                text=error_msg,
                icon_pixmap=svg_to_pixmap(
                    get_svg_file_path("warn_icon")[0],
                    35,
                    None,
                    ThemeColors.WARNING,
                    margins=(0, 0, 8, 0),
                ),
            )
            popup.exec_and_get()
            return

        # Start sync
        self._is_syncing = True
        self._render_sync_button_section()
        self._log_output.clear_text()

        self._do_sync()

        # Hiện dialog tiến trình đồng bộ (sync progress dialog)
        self._sync_progress_dialog = SyncProgressDialog(parent=self)
        self._sync_progress_dialog.reset()
        self._sync_progress_dialog.cancel_requested.connect(self._on_cancel_sync)
        self._sync_progress_dialog.exec()

    def _reset_sync_indicators(self) -> None:
        """Reset các chỉ báo sync về trạng thái ban đầu."""
        self._is_syncing = False
        self._render_sync_button_section()

    def _on_sync_progress(
        self, status: SyncProgressStatus, data: SyncProgressData
    ) -> None:
        # Update dữ liệu vào list
        if self._sync_progress_dialog:
            self._sync_progress_dialog.update_item_progress(data)
            if status == SyncProgressStatus.FINISHED:
                self._sync_progress_dialog.btn_cancel.setText("Đóng")
                # Ngắt connect cũ và nối vào hàm đóng dialog
                try:
                    self._sync_progress_dialog.btn_cancel.clicked.disconnect()
                except:
                    pass
                self._sync_progress_dialog.btn_cancel.clicked.connect(
                    self._sync_progress_dialog.accept
                )

    def _on_cancel_sync(self):
        if self._sync_worker and self._sync_progress_dialog:
            self._sync_worker.cancel()
            self._sync_progress_dialog.reject()
            self._reset_sync_indicators()

    def _on_sync_finished(self, code: int, status: QProcess.ExitStatus) -> None:
        self._reset_sync_indicators()
        self._data_manager.save_last_gdrive_entered_dir(self._current_gdrive_path)
        if self._sync_progress_dialog:
            self._sync_progress_dialog.accept()
            self._sync_progress_dialog = None

    def _on_sync_error(self, msg: str) -> None:
        self._is_syncing = False
        self._render_sync_button_section()
        popup = CustomAnnounce(
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

    def _open_settings_screen(self) -> None:
        """Mở window Settings."""
        if not self._settings_dialog:
            self._settings_dialog = SettingsScreen(self)
        self._settings_dialog.exec()

    def _render_user_data(self, saved_user_data: ConfigSchema) -> None:
        """Hiển thị dữ liệu sync đã lưu."""
        active_remote = saved_user_data.get("active_remote")
        if saved_user_data.get("remotes") and active_remote:
            # Update active remote bar với remote name
            self._active_remote = active_remote
            self._active_remote_label.setText(active_remote)

            # Hiển thị nút Settings và gdrive root dir đã lưu (nếu có)
            last_gdrive_entered_dir = saved_user_data.get("last_gdrive_entered_dir")
            if last_gdrive_entered_dir:
                self._gdrive_path_input.setText(last_gdrive_entered_dir)
            settings_btn = CustomButton()
            settings_btn.on_clicked(self._open_settings_screen)
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
            login_btn.on_clicked(self._do_login_gdrive)
            login_btn_font = login_btn.font()
            login_btn_font.setBold(True)
            login_btn_font.setPointSize(12)
            login_btn.setFont(login_btn_font)
            self._right_actions_layout.addStretch()
            self._right_actions_layout.addWidget(login_btn)

    def _load_saved_user_data(self) -> None:
        """Tải dữ liệu người dùng đã lưu (nếu có)."""
        self._render_user_data(self._data_manager.get_entire_config())


def santize_input_paths() -> list[str]:
    """
    Lấy danh sách path được truyền từ lệnh ngoài.
    - Bỏ argv[0] (script path)
    - Chuẩn hóa path
    - Loại bỏ trùng
    - Loại bỏ path không tồn tại
    - Giữ nguyên thứ tự
    """

    raw_args = sys.argv[1:]

    seen = set()
    result: list[str] = []

    for arg in raw_args:
        if not arg:
            continue

        try:
            path = Path(arg).resolve()
        except (OSError, RuntimeError) as e:
            # resolve() có thể raise exception với path không hợp lệ
            continue

        # Bỏ qua path không tồn tại
        if not path.exists():
            continue

        abs_path = str(path.absolute())
        if abs_path in seen:
            continue

        seen.add(abs_path)
        result.append(abs_path)

    return result


def init_app() -> None:
    """Hàm khởi tạo ứng dụng."""
    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(14)
    app.setFont(font)

    # Lấy và sanitize input paths
    local_paths = santize_input_paths()

    window = MainWindow(local_paths)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    init_app()
