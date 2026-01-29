from . import resources_rc  # noqa: F401
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QFileDialog,
    QSizePolicy,
    QFrame,
    QScrollArea,
)
from PySide6.QtGui import QKeySequence, QShortcut, QIcon
from PySide6.QtCore import QProcess, QSize, Qt, QTimer
from .sync_progress import SyncProgressDialog
from .components.tooltip import CollisionConstraint, ToolTipBinder, ToolTipConfig
from .gdrive_folders_picker import GDriveFoldersPicker
from .components.scrollable_text import ScrollableText
from .login_gdrive_screen import LoginGDriveScreen, LoginResult
from .active_remote_info import ActiveRemoteScreen
from .components.announcement import CustomAnnounce
from .components.divider import CustomDivider
from .utils.helpers import (
    center_window_on_screen,
    detect_content_type_by_file_extension,
    detect_file_extension,
    detect_path_type,
    extract_filename_with_ext,
    get_svg_as_icon,
)
from .components.flow_layout import CustomFlowLayout
from .components.selected_file_box import FileInfoBox
from .components.label import CustomLabel
from .workers.sync_worker import (
    RcloneSyncWorker,
    SyncAction,
    SyncOptions,
    SyncProgressData,
    SyncProgressStatus,
)

# from testing.mock_sync_worker import MockRcloneSyncWorker
from .data.data_manager import UserDataConfigSchema, UserDataManager
from .configs.configs import SyncError, ThemeColors
from .components.button import CustomButton, LoadingButton
from .components.overlay import OverlayPosition, PositionedOverlay
from .settings_screen import SettingsScreen
import os
import subprocess
from .components.window_title_bar import CustomWindowTitleBar
from .mixins.main_window import MainWindowMixin
from .testing.performance_testing import PerformanceTestingMixin
from .data.rclone_configs_manager import RCloneConfigManager


class MainWindow(PerformanceTestingMixin, MainWindowMixin):
    """Main window cho ứng dụng sync folder."""

    def __init__(self, local_paths: list[str]):
        super().__init__()
        self._sync_worker: RcloneSyncWorker | None = None
        # self._sync_worker: MockRcloneSyncWorker | None = None
        self._sync_progress_dialog: SyncProgressDialog | None = None
        self._data_manager: UserDataManager = UserDataManager()
        self._root_layout: QVBoxLayout
        self._top_menu_layout: QHBoxLayout
        self._local_paths_list = local_paths
        self._gdrive_path_input: QLineEdit
        self._current_gdrive_path: str = ""
        self._active_remote: str
        self._selected_docs_preview: QVBoxLayout
        self._selected_docs_flow: CustomFlowLayout
        self._sync_btn: LoadingButton | None = None
        self._is_syncing: bool = False
        self._log_output: ScrollableText
        self._right_actions_layout: QHBoxLayout
        self._active_remote_label: CustomLabel
        self._copy_log_btn: CustomButton
        self._settings_dialog: SettingsScreen | None = None
        self._copy_log_btn_overlay: PositionedOverlay
        self._setup_ui()

    def _set_local_paths_list(self, paths: list[str]) -> None:
        self._local_paths_list = paths
        self._update_selected_docs_preview()

    def _add_keyboard_shortcuts(self) -> None:
        """Bắt sự kiện nhấn các tổ hợp phím."""
        super()._add_keyboard_shortcuts()

        # Ctrl + Enter (đồng bộ ngay)
        shortcut_ctrl_enter = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut_ctrl_enter.activated.connect(self._on_sync_start)

        # Ctrl + O (mở dialog chọn folder/tệp)
        shortcut_ctrl_o = QShortcut(QKeySequence("Ctrl+O"), self)
        shortcut_ctrl_o.activated.connect(self._browse_local_folder)

        # Ctrl + I (mở settings)
        shortcut_ctrl_i = QShortcut(QKeySequence("Ctrl+I"), self)
        shortcut_ctrl_i.activated.connect(self._open_settings_screen)

        # Ctrl + L (login Google Drive)
        shortcut_ctrl_l = QShortcut(QKeySequence("Ctrl+L"), self)
        shortcut_ctrl_l.activated.connect(self._do_login_gdrive)

        # Ctrl + F (mở dialog chọn thư mục Google Drive)
        shortcut_ctrl_f = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_ctrl_f.activated.connect(self._open_gdrive_folders_picker)

    def _setup_ui(self) -> None:
        """Thiết lập giao diện người dùng."""
        self.setWindowTitle("Đồng bộ với Google Drive")
        self.setWindowIcon(QIcon(":/icons/app.ico"))
        self.setMinimumWidth(800)

        # Ẩn thanh tiêu đề gốc của hệ điều hành
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True
        )  # Nền trong suốt để bo góc thật sự

        app_container = QVBoxLayout(self)
        app_container.setContentsMargins(0, 0, 0, 0)
        app_container.setSpacing(0)

        self._root_shell.setObjectName("RootShell")
        self._root_shell.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        root_layout = QVBoxLayout(self._root_shell)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(4)
        self._root_layout = root_layout

        # Custom title bar
        self._title_bar = CustomWindowTitleBar(
            root_shell=self._root_shell,
            close_app_handler=self.close_app_by_quit,
            parent=self,
        )
        self.set_animate_close_window(self._title_bar._animate_close_window)
        root_layout.addWidget(self._title_bar)

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
        self._tmp_frame = QFrame()
        self._selected_docs_preview = QVBoxLayout(self._tmp_frame)
        self._selected_docs_preview.setSpacing(4)
        self._selected_docs_preview.setContentsMargins(0, 16, 0, 0)
        self._render_selected_docs_preview()

        # Output log section
        log_layout = self._create_log_section()

        # Main section layout
        main_layout_section = QVBoxLayout()
        main_layout_section.setContentsMargins(12, 0, 12, 8)
        main_layout_section.addWidget(top_menu_frame)
        main_layout_section.addWidget(divider)
        main_layout_section.addLayout(active_remote_info_layout)
        main_layout_section.addLayout(gdrive_layout)
        main_layout_section.addWidget(self._tmp_frame)
        main_layout_section.addLayout(log_layout)

        root_layout.addLayout(main_layout_section)
        self._render_sync_button_section()

        app_container.addWidget(self._root_shell)

        self._root_shell.setStyleSheet(
            f"""
            #RootShell {{
                border-radius: 8px; /* Bo góc mặc định */
                background-color: {ThemeColors.BLACK_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
            }}
            #RootShell[is_focused="true"] {{
                border: 1px solid {ThemeColors.MAIN}; 
            }}
            /* Khi phóng to toàn màn hình -> Vuông góc và bỏ viền */
            #RootShell[is_maximized="true"] {{
                border-radius: 0px;
                border: none;
            }}
            #BrowseLocalButton {{
                padding: 2px 12px 4px;
                background-color: {ThemeColors.MAIN};
                color: black;
            }}
            #LoginGDriveButton {{
                padding: 2px 12px 4px;
                background-color: {ThemeColors.MAIN};
                color: black;
            }}
            #SettingsButton {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                color: black;
            }}
            #ActiveRemoteBar {{
                background-color: {ThemeColors.GRAY_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 8px;
            }}
            #ActiveRemoteBar:hover {{
                background-color: #3d3d3d;
            }}
            #GDrivePathInput {{
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-bottom: 2px solid {ThemeColors.STRONG_GRAY};
                border-radius: 8px;
                padding: 4px 8px 6px;
            }}
            #GDrivePathInput:hover {{
                border-color: {ThemeColors.MAIN};
            }}
            #GDrivePathInput:focus {{
                border-color: {ThemeColors.MAIN};
            }}
            #GDriveFolderPickerButton {{
                padding: 4px 8px 4px;
                background-color: {ThemeColors.MAIN};
                color: black;
            }}
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
            #CopyLogButton {{
                background-color: {ThemeColors.BLACK_BACKGROUND};
                border: 1px solid {ThemeColors.GRAY_BORDER};
                border-radius: 6px;
                padding: 2px 6px 4px;
            }}
            #SyncButton {{
                background-color: {ThemeColors.MAIN};
                color: black;
            }}
            #QuitAppButton {{
                background-color: {ThemeColors.STRONG_GRAY};
                color: black;
            }}
            """
        )

        # Chạy animation mở app ngay khi giao diện hiển thị
        QTimer.singleShot(0, self._animate_open_zoom)
        # Thêm các phím tắt
        QTimer.singleShot(0, self._add_keyboard_shortcuts)
        # Thiết lập danh sách local paths ban đầu
        QTimer.singleShot(
            500, lambda paths=self._local_paths_list: self._set_local_paths_list(paths)
        )
        # Load saved user data
        QTimer.singleShot(800, self._load_saved_user_data)

    def _render_top_menu(self) -> None:
        # Nút Browse local folder (bên trái)
        left_actions_layout = QHBoxLayout()

        browse_btn = CustomButton("Chọn thư mục/tệp...")
        browse_btn.setObjectName("BrowseLocalButton")
        browse_btn.setIcon(
            get_svg_as_icon(
                "browse_file_icon",
                26,
                None,
                "#000000",
                margins=(0, 0, 8, 0),
            )
        )
        browse_btn.setIconSize(QSize(26, 26))
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
        abs_path = os.path.abspath(path)
        if os.path.isfile(abs_path):
            QProcess.startDetached(
                "explorer",
                ["/select,", abs_path],
            )
        elif os.path.isdir(abs_path):
            QProcess.startDetached(
                "explorer",
                [abs_path],
            )
        else:
            raise FileNotFoundError(f"Path không tồn tại: {abs_path}")

    def _render_selected_docs_preview(self) -> None:
        """Khởi tạo preview các tệp/thư mục đã chọn."""
        selected_docs_label = CustomLabel(
            "Tệp và thư mục được chọn trên máy:", is_bold=True
        )
        selected_docs_label.setContentsMargins(6, 0, 0, 0)

        self._selected_docs_frame_inner_scroll = QFrame()
        self._selected_docs_flow = CustomFlowLayout(
            margins=(0, 4, 0, 0),
            h_spacing=8,
            v_spacing=8,
            parent=self._selected_docs_frame_inner_scroll,
        )

        selected_docs_empty_label = CustomLabel(
            "Chưa có tệp hoặc thư mục nào được chọn.", font_size=12
        )
        self._selected_docs_empty_overlay = PositionedOverlay(
            container=self._selected_docs_frame_inner_scroll,
            overlay=selected_docs_empty_label,
            position=OverlayPosition.TOP_LEFT,
            margin=0,
        )

        selected_docs_scroll = QScrollArea()
        selected_docs_scroll.setWidgetResizable(True)
        selected_docs_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        selected_docs_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        selected_docs_scroll.setMinimumHeight(100)
        selected_docs_scroll.setMaximumHeight(160)
        selected_docs_scroll.setWidget(self._selected_docs_frame_inner_scroll)

        self._selected_docs_preview.addWidget(selected_docs_label)
        self._selected_docs_preview.addWidget(selected_docs_scroll)

    def _update_selected_docs_preview(self) -> None:
        """Cập nhật lại preview các tệp/thư mục đã chọn."""
        # Xoá hết item cũ
        self._selected_docs_flow.clear_items()

        # Thêm nhiều box để thấy wrap
        if len(self._local_paths_list) > 0:
            self._selected_docs_empty_overlay.hide()
            for path in self._local_paths_list:
                path_type = detect_path_type(path)
                content_type = "folder"
                if path_type == "file":
                    file_ext = detect_file_extension(path)
                    content_type = detect_content_type_by_file_extension(file_ext or "")
                file_info_box = FileInfoBox(
                    svg_name=f"{content_type}_icon",
                    svg_fill_color=None,
                    svg_stroke_color="#ffffff",
                    text=extract_filename_with_ext(path),
                )
                file_info_box.on_clicked(
                    lambda p=path: self._reveal_path_in_file_explorer(p)
                )
                ToolTipBinder(
                    file_info_box,
                    ToolTipConfig(
                        text=f"<b>{'Thư mục' if path_type=='folder' else 'Tệp'}</b>: {path}",
                        show_delay_ms=100,
                        constrain_to=CollisionConstraint.WINDOW,
                    ),
                )
                self._selected_docs_flow.addWidget(file_info_box)
        else:
            self._selected_docs_empty_overlay.show()

    def _create_active_remote_info(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 8, 0, 0)
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

    def _open_gdrive_folders_picker(self) -> None:
        """Mở dialog chọn thư mục trên Google Drive."""
        # Hiện tại chưa hỗ trợ do rclone không có chức năng này
        folders_picker = GDriveFoldersPicker(self)
        folders_picker.exec()

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
        input_layout.setSpacing(8)
        self._gdrive_path_input = QLineEdit()
        self._gdrive_path_input.setObjectName("GDrivePathInput")
        self._gdrive_path_input.returnPressed.connect(
            self._on_gdrive_path_input_enter_pressed
        )
        open_gdrive_folders_preview = CustomButton(fixed_height=44)
        open_gdrive_folders_preview.setObjectName("GDriveFolderPickerButton")
        open_gdrive_folders_preview.setIcon(
            get_svg_as_icon(
                "browse_file_icon",
                26,
                None,
                "#000000",
                margins=(0, 0, 0, 0),
            )
        )
        open_gdrive_folders_preview.setIconSize(QSize(26, 26))
        open_gdrive_folders_preview.on_clicked(self._open_gdrive_folders_picker)

        if default_base_dir:
            self._gdrive_path_input.setText(default_base_dir)
        self._gdrive_path_input.setPlaceholderText("Thư mục 1/Thư mục 2/Thư mục 3/...")

        input_layout.addWidget(self._gdrive_path_input)
        input_layout.addWidget(open_gdrive_folders_preview)

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
        self._log_output.set_font_size(12)
        self._copy_log_btn = CustomButton("Sao chép", fixed_height=28, font_size=11)
        self._copy_log_btn.setObjectName("CopyLogButton")
        self._copy_log_btn.adjustSize()
        self._copy_log_btn.on_clicked(self._on_copy_log)
        self._copy_log_btn_overlay = PositionedOverlay(
            container=self._log_output,
            overlay=self._copy_log_btn,
            position=OverlayPosition.TOP_RIGHT,
            margin=2,
        )
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
            self._sync_btn = LoadingButton(
                "Đồng bộ ngay", is_bold=True, fixed_height=48
            )
            self._sync_btn.setObjectName("SyncButton")
            self._sync_btn.setIcon(
                get_svg_as_icon(
                    "double_check_icon",
                    30,
                    None,
                    "#000000",
                    3,
                    (0, 0, 8, 0),
                )
            )
            self._sync_btn.setIconSize(QSize(30, 30))
            self._sync_btn.on_clicked(self._on_sync_start)

            quit_btn = CustomButton("Thoát", is_bold=True, fixed_height=48)
            quit_btn.setObjectName("QuitAppButton")
            quit_btn.on_clicked(self.close_app)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)
            btn_layout.setContentsMargins(12, 8, 12, 8)
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
            CustomAnnounce.info(
                self,
                title="Yêu cầu đăng nhập",
                message=error_msg,
            )
            return
        elif not is_valid:
            CustomAnnounce.warn(
                self,
                title="Lỗi",
                message=error_msg,
            )
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
        CustomAnnounce.error(
            self,
            title="Lỗi đồng bộ",
            message=msg,
        )
        pass

    def _open_settings_screen(self) -> None:
        """Mở window Settings."""
        if not self._settings_dialog:
            self._settings_dialog = SettingsScreen(self)
        self._settings_dialog.exec()

    def _render_user_data(self, saved_user_data: UserDataConfigSchema) -> None:
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
                get_svg_as_icon(
                    "settings_icon",
                    24,
                    None,
                    "#ffffff",
                )
            )
            settings_btn.setIconSize(QSize(24, 24))
            settings_btn.setObjectName("SettingsButton")
            settings_btn.setFixedHeight(36)
            settings_btn.setFixedWidth(36)
            settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._right_actions_layout.addWidget(settings_btn)
        else:
            login_btn = CustomButton("Đăng nhập Google Drive")
            login_btn.setObjectName("LoginGDriveButton")
            login_btn.setIcon(
                get_svg_as_icon(
                    "login_icon",
                    26,
                    None,
                    "#000000",
                    margins=(0, 0, 8, 0),
                )
            )
            login_btn.setIconSize(QSize(26, 26))
            login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            login_btn.on_clicked(self._do_login_gdrive)
            login_btn_font = login_btn.font()
            login_btn_font.setBold(True)
            login_btn_font.setPointSize(12)
            login_btn.setFont(login_btn_font)
            self._right_actions_layout.addStretch()
            self._right_actions_layout.addWidget(login_btn)

    def _ensure_significant_data_initialized(self) -> None:
        """Đảm bảo dữ liệu quan trọng đã được khởi tạo."""
        if not self._data_manager.check_if_data_inited():
            self._data_manager.init_data_config_file()

    def _load_saved_user_data(self) -> None:
        """Tải dữ liệu người dùng đã lưu (nếu có)."""
        self._ensure_significant_data_initialized()
        self._render_user_data(self._data_manager.get_entire_config())


def santize_input_paths(local_paths: list[str]) -> list[str]:
    """
    Lấy danh sách path được truyền từ lệnh ngoài.
    - Bỏ argv[0] (script path)
    - Chuẩn hóa path
    - Loại bỏ trùng
    - Loại bỏ path không tồn tại
    - Giữ nguyên thứ tự
    """

    seen = set()
    result: list[str] = []

    for arg in local_paths:
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


def start_app(local_paths: list[str]) -> None:
    """Hàm khởi tạo ứng dụng."""
    print(">>> Starting application...")
    RCloneConfigManager.init_rclone_config_path()

    app = QApplication(sys.argv)
    font = app.font()
    font.setPointSize(14)
    app.setFont(font)

    # Lấy và sanitize input paths
    local_paths = santize_input_paths(local_paths)

    window = MainWindow(local_paths)
    center_window_on_screen(window)
    window.show()
    sys.exit(app.exec())
