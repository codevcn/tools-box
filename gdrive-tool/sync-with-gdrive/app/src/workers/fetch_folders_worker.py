from PySide6.QtCore import QThread, Signal
import subprocess
import os
from ..data.rclone_configs_manager import RCloneConfigManager


class FetchFoldersWorker(QThread):
    """
    Worker chạy ngầm để lấy danh sách thư mục từ rclone.
    Sử dụng: rclone lsf remote:path --dirs-only
    """

    # Signal gửi dữ liệu về UI: (danh sách folder, thông báo lỗi nếu có)
    data_ready = Signal(list, str)

    def __init__(self, remote_name: str, gdrive_root_path: str = ""):
        super().__init__()
        self.remote_name = remote_name
        self.gdrive_root_path = gdrive_root_path  # Mặc định là root ("")

    def run(self):
        rclone_exe = RCloneConfigManager.rclone_executable_path()

        # Đường dẫn remote: VD: "gdrive:Photos/"
        full_remote_path = f"{self.remote_name}:{self.gdrive_root_path}"

        cmd = [
            rclone_exe,
            "lsf",
            full_remote_path,
            "--dirs-only",  # Chỉ lấy thư mục
            "--connect-timeout",
            "10s",  # [OPTIMIZED] Timeout kết nối cho rclone
        ]

        # [OPTIMIZED] Cấu hình ẩn console window triệt để trên Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            # Dùng subprocess.run để bắt output gọn gàng
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
                startupinfo=startupinfo,  # [OPTIMIZED] Áp dụng startupinfo
                timeout=30,  # [OPTIMIZED] Timeout tổng 30s để tránh treo app
            )

            if result.returncode == 0:
                raw_output = result.stdout.strip()
                if not raw_output:
                    folders = []
                else:
                    # rclone lsf trả về "folder/", ta bỏ dấu "/" ở cuối
                    folders = [line.rstrip("/") for line in raw_output.split("\n")]

                self.data_ready.emit(folders, "")
            else:
                self.data_ready.emit([], f"Rclone error: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.data_ready.emit(
                [], "Quá thời gian chờ phản hồi từ Google Drive (Timeout)."
            )
        except Exception as e:
            self.data_ready.emit([], str(e))
