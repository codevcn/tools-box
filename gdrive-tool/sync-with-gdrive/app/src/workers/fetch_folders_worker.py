# src/workers/fetch_folders_worker.py
from PySide6.QtCore import QThread, Signal
import subprocess
import os
from ..utils.helpers import rclone_executable_path, rclone_config_path


class FetchFoldersWorker(QThread):
    """
    Worker chạy ngầm để lấy danh sách thư mục từ rclone.
    Sử dụng: rclone lsf remote:path --dirs-only
    """

    # Signal gửi dữ liệu về UI: (danh sách folder, thông báo lỗi nếu có)
    data_ready = Signal(list, str)

    def __init__(self, remote_name: str, path: str = ""):
        super().__init__()
        self.remote_name = remote_name
        self.path = path  # Mặc định là root ("")

    def run(self):
        rclone_exe = rclone_executable_path()
        config_path = rclone_config_path()

        # Đường dẫn remote: VD: "gdrive:Photos/"
        full_remote_path = f"{self.remote_name}:{self.path}"

        cmd = [
            rclone_exe,
            "lsf",
            full_remote_path,
            "--dirs-only",  # Chỉ lấy thư mục
            "--config",
            str(config_path),
        ]

        try:
            # Dùng subprocess.run để bắt output gọn gàng
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
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

        except Exception as e:
            self.data_ready.emit([], str(e))
