import subprocess
from PySide6.QtCore import QThread, Signal


class RcloneSyncWorker(QThread):
    """Worker thread để chạy rclone sync không block UI."""

    output_received = Signal(str)
    sync_finished = Signal(bool, str)  # success, message

    def __init__(
        self,
        local_path: str,
        gdrive_path: str,
    ):
        super().__init__()
        self.local_path = local_path
        self.gdrive_path = gdrive_path
        self.rclone_exe = (
            r"D:\Programs-ver-Later\rclone-v1.72.1-windows-amd64\rclone.exe"
        )

    def run(self) -> None:
        """Chạy rclone sync command."""
        try:
            cmd = [
                self.rclone_exe,
                "sync",
                self.local_path,
                self.gdrive_path,
                "-v",  # verbose output
                "--progress",
            ]

            self.output_received.emit(f"Executing: {' '.join(cmd)}\n")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Đọc output real-time
            if process.stdout:
                for line in process.stdout:
                    self.output_received.emit(line)

            process.wait()

            if process.returncode == 0:
                self.sync_finished.emit(True, "Đồng bộ thành công!")
            else:
                self.sync_finished.emit(
                    False, f"Lỗi: rclone exit code {process.returncode}"
                )

        except Exception as e:
            self.sync_finished.emit(False, f"Lỗi: {str(e)}")
