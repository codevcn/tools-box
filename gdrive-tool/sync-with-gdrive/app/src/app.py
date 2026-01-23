import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QSizePolicy,
)
from utils.helpers import (
    detect_content_type_by_file_extension,
    detect_file_extension,
    detect_path_type,
    extract_common_folder_str,
    extract_filename_with_ext,
)
from components.flow_layout import CustomFlowLayout
from components.selected_file_box import FileInfoBox
from components.label import CustomLabel
from sync_worker import RcloneSyncWorker
from data.data_manager import DataManager
from configs.configs import SyncError


class MainWindow(QWidget):
    """Main window cho ứng dụng sync folder."""

    def __init__(self, local_paths: list[str]):
        super().__init__()
        self.worker: RcloneSyncWorker
        self.dataManager: DataManager = DataManager()
        self.root_layout: QVBoxLayout
        self.local_paths_list = local_paths
        self.local_dir_textfield: QLineEdit
        self.gdrive_path_input: QLineEdit
        self.selected_docs_preview: QWidget | None = None
        self.selected_docs_layout: QVBoxLayout
        self.sync_btn: QPushButton | None = None
        self.is_syncing: bool = False
        self._setup_ui()
        self._set_local_paths_list(local_paths)

    def _set_local_paths_list(self, paths: list[str]) -> None:
        self.local_paths_list = paths
        self.local_dir_textfield.setText(extract_common_folder_str(paths))
        self._render_selected_docs_preview()

    def _setup_ui(self) -> None:
        """Thiết lập giao diện người dùng."""
        self.setWindowTitle("Đồng bộ với Google Drive")
        self.resize(900, 600)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(4)
        self.root_layout = root_layout

        # Local paths section (hiển thị danh sách paths đã truyền vào)
        local_dir_section = self._create_path_input_section(
            "Đường dẫn thư mục trên máy:",
            is_local=True,
            margins=(6, 0, 0, 0),
        )
        self.local_dir_textfield = local_dir_section["input"]

        # Selected docs preview section
        self.selected_docs_layout = QVBoxLayout()
        self.selected_docs_layout.setSpacing(4)
        selected_docs_label = CustomLabel("Các tệp và thư mục được chọn:", is_bold=True)
        selected_docs_label.setContentsMargins(6, 8, 0, 0)
        self.selected_docs_layout.addWidget(selected_docs_label)

        # GDrive folder section
        gdrive_layout = self._create_path_input_section(
            "Đường dẫn thư mục trên Google Drive:",
            is_local=False,
            margins=(6, 16, 0, 0),
            default_base_dir=self.dataManager.get_saved_gdrive_root_dir(),
        )
        self.gdrive_path_input = gdrive_layout["input"]

        # Output log section
        log_label = CustomLabel("Chi tiết đồng bộ:", is_bold=True)
        log_label.setContentsMargins(6, 16, 0, 0)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(100)

        # Main section layout
        main_layout_section = QVBoxLayout()
        main_layout_section.addLayout(local_dir_section["layout"])
        main_layout_section.addLayout(self.selected_docs_layout)
        main_layout_section.addLayout(gdrive_layout["layout"])
        # main_layout_section.addWidget(log_label)
        # main_layout_section.addWidget(self.log_output)
        main_layout_section.addStretch()

        root_layout.addLayout(main_layout_section)
        self._render_sync_button()

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
            self.sync_btn = QPushButton("Đồng bộ ngay")
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
            script_dir = Path(__file__).resolve().parent
            prefix_path = f"{script_dir}\\assets\\images\\svg"
            svg = f"{prefix_path}\\file_icon.svg"
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

        if default_base_dir is not None:
            input_field.setText(default_base_dir)
        input_field.setPlaceholderText(
            "VD: C:\\Users\\Your Name\\Documents"
            if is_local
            else "VD: Thư mục 1/Thư mục 2/..."
        )

        result = {
            "layout": layout,
            "input": input_field,
        }

        if is_local:
            browse_btn = QPushButton("Browse...")
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
        self.is_syncing = True
        self._render_sync_button()
        self.log_output.clear()

        # Start sync worker cho từng path
        gdrive_path = self.gdrive_path_input.text().strip()

        # Sync path đầu tiên
        self._append_log(f"Đồng bộ {len(self.local_paths_list)} path(s)...\n")
        self._sync_next_path(0, gdrive_path)

    def _on_sync_start(self) -> None:
        """Xử lý khi người dùng nhấn nút Đồng bộ."""
        # Validate inputs
        is_valid, error_msg, err_type = self._validate_inputs()
        if err_type == SyncError.NEED_LOGIN:
            QMessageBox.information(self, "Yêu cầu đăng nhập", error_msg)
            return
        elif not is_valid:
            QMessageBox.warning(self, "Lỗi", error_msg)
            return
        self._do_sync()

    def _append_log(self, text: str) -> None:
        cursor = self.log_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        cursor.insertText(text.rstrip() + "\n")

    def _sync_next_path(self, index: int, gdrive_path: str) -> None:
        """Sync path tiếp theo trong danh sách."""
        if index >= len(self.local_paths_list):
            # Đã sync hết
            self._on_all_sync_finished()
            return

        local_path = self.local_paths_list[index]
        path_name = Path(local_path).name

        # Tạo gdrive destination path với tên folder/file
        gdrive_dest = f"{gdrive_path}/{path_name}"

        self._append_log(f"\n{'='*50}")
        self._append_log(
            f"[{index + 1}/{len(self.local_paths_list)}] Đồng bộ: {local_path}"
        )
        self._append_log(f"Đích: {gdrive_dest}")
        self._append_log(f"{'='*50}\n")

        self.worker = RcloneSyncWorker(local_path, gdrive_dest)
        self.worker.output_received.connect(self._append_log)
        self.worker.sync_finished.connect(
            lambda success, msg: self._on_single_sync_finished(
                success, msg, index, gdrive_path
            )
        )
        self.worker.start()

    def _on_single_sync_finished(
        self, success: bool, message: str, index: int, gdrive_path: str
    ) -> None:
        """Xử lý khi sync 1 path hoàn thành."""
        self._append_log(f"\n{message}\n")

        if not success:
            # Nếu có lỗi, dừng lại
            self._on_all_sync_finished(False, f"Lỗi khi đồng bộ path thứ {index + 1}")
            return

        # Sync path tiếp theo
        self._sync_next_path(index + 1, gdrive_path)

    def _on_all_sync_finished(self, success: bool = True, error_msg: str = "") -> None:
        """Xử lý khi tất cả paths đã sync xong."""
        if self.sync_btn:
            self.sync_btn.setEnabled(True)
            self.sync_btn.setText("Đồng bộ ngay")

        if success:
            message = f"Đã đồng bộ thành công {len(self.local_paths_list)} path(s)!"
            self._append_log(f"\n{'='*50}\n✅ {message}\n{'='*50}")
            QMessageBox.information(self, "Thành công", message)
        else:
            self._append_log(f"\n{'='*50}\n❌ {error_msg}\n{'='*50}")
            QMessageBox.critical(self, "Lỗi", error_msg)


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
