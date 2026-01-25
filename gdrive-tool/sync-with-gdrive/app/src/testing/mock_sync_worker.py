import random
import json
from PySide6.QtCore import QTimer, QObject, Signal, QProcess
from workers.sync_worker import SyncProgressData, SyncProgressStatus, LOG_SPEED_INTERVAL


class MockRcloneSyncWorker(QObject):
    """
    Mock Worker giả lập hành vi của RcloneSyncWorker để test UI.
    Giả lập upload từng file với tiến độ thực tế (file lớn chạy lâu, file nhỏ chạy nhanh).
    """

    log = Signal(str)
    error = Signal(str)
    done = Signal(int, QProcess.ExitStatus)
    progress = Signal(SyncProgressStatus, SyncProgressData)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)

        # Parse interval từ string "0.5s" -> 500ms
        interval_ms = int(float(LOG_SPEED_INTERVAL.replace("s", "")) * 1000)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._on_timeout)

        # 1. Định nghĩa danh sách file giả với dung lượng cụ thể (để tính % cho chuẩn)
        self._fake_files = [
            {"name": "video_intro_4k.mp4", "size": 1024 * 1024 * 150},  # 150 MB
            {"name": "backup_data_2023.zip", "size": 1024 * 1024 * 80},  # 80 MB
            {"name": "vacation_photos/img_001.jpg", "size": 1024 * 1024 * 5},  # 5 MB
            {"name": "vacation_photos/img_002.jpg", "size": 1024 * 1024 * 8},  # 8 MB
            {"name": "project_docs/report.pdf", "size": 1024 * 1024 * 25},  # 25 MB
            {"name": "installer_setup.exe", "size": 1024 * 1024 * 60},  # 60 MB
            {"name": "music/song_01.mp3", "size": 1024 * 1024 * 12},  # 12 MB
            {"name": "music/song_02.mp3", "size": 1024 * 1024 * 10},  # 10 MB
            {"name": "documents/presentation.pptx", "size": 1024 * 1024 * 35},  # 35 MB
            {"name": "archive/old_project.tar.gz", "size": 1024 * 1024 * 120},  # 120 MB
            {"name": "images/banner.png", "size": 1024 * 1024 * 3},  # 3 MB
            {"name": "database/export.sql", "size": 1024 * 1024 * 45},  # 45 MB
        ]

        # Tính tổng dung lượng từ list file
        self._total_bytes = sum(f["size"] for f in self._fake_files)

        # Các biến theo dõi trạng thái
        self._current_global_bytes = 0  # Tổng bytes đã chạy
        self._current_file_idx = 0  # Index file đang chạy
        self._current_file_bytes = 0  # Bytes đã chạy của file hiện tại

        self._base_speed = (
            1024 * 1024 * 25
        )  # Tốc độ cơ bản 25 MB/s (tăng lên chút cho nhanh test)
        self._is_running = False

    def start(self):
        if self._is_running:
            return

        self._is_running = True
        self.log.emit("> [MOCK] Đang khởi động công cụ đồng bộ...")

        # Emit signal bắt đầu
        self.progress.emit(
            SyncProgressStatus.STARTING,
            SyncProgressData(
                0.0, "Đang khởi động...", 0, 0.0
            ),  # Thêm tham số 0 cho current_file_percent
        )

        # Reset counters
        self._current_global_bytes = 0
        self._current_file_idx = 0
        self._current_file_bytes = 0
        self._timer.start()

    def cancel(self):
        if self._is_running:
            self.log.emit("> [MOCK] Đang hủy quá trình...")
            self._timer.stop()
            self._is_running = False

    def _on_timeout(self):
        # 1. Tính toán tốc độ giả lập (dao động +/- 20%)
        variance = random.uniform(0.8, 1.2)
        current_speed = self._base_speed * variance  # Bytes/s

        # Lượng bytes tăng thêm trong interval này (0.5s)
        bytes_inc = current_speed * 0.5

        # 2. Xử lý logic cộng dồn bytes vào file hiện tại
        if self._current_file_idx < len(self._fake_files):
            current_file_info = self._fake_files[self._current_file_idx]
            file_size = current_file_info["size"]
            file_name = current_file_info["name"]

            # Tính lượng bytes còn thiếu của file này
            remaining_file_bytes = file_size - self._current_file_bytes

            # Nếu tốc độ quá nhanh, chỉ cộng vừa đủ để xong file này (tránh vượt lố)
            actual_inc = min(bytes_inc, remaining_file_bytes)

            self._current_file_bytes += actual_inc
            self._current_global_bytes += actual_inc

            # Tính % của file hiện tại
            current_file_percent = int((self._current_file_bytes / file_size) * 100)

            # Check xem file này xong chưa
            is_file_finished = self._current_file_bytes >= file_size
        else:
            # Trường hợp hiếm hoi index vượt quá (đã xong hết)
            self._finish()
            return

        # 3. Tính % tổng thể (Global)
        global_percent = (self._current_global_bytes / self._total_bytes) * 100
        if global_percent > 100.0:
            global_percent = 100.0

        # 4. Tạo Mock JSON Log (để in ra log box giống hệt Rclone thật)
        # Lưu ý: Thêm field 'percentage' vào transferring array
        mock_json_log = json.dumps(
            {
                "level": "info",
                "msg": f"Đang truyền: {file_name}",
                "stats": {
                    "bytes": int(self._current_global_bytes),
                    "totalBytes": int(self._total_bytes),
                    "speed": current_speed,
                    "transferring": [
                        {
                            "name": file_name,
                            "size": file_size,
                            "bytes": int(self._current_file_bytes),
                            "percentage": current_file_percent,  # Field quan trọng để UI hiển thị
                        }
                    ],
                },
            }
        )
        self.log.emit(mock_json_log)

        # 5. Emit Progress Data (Object chuẩn)
        progress_data = SyncProgressData(
            percent=global_percent,
            file_name=file_name,
            current_file_percent=current_file_percent,  # Có % file lẻ
            speed=current_speed,
        )
        self.progress.emit(SyncProgressStatus.IN_PROGRESS, progress_data)

        # 6. Chuyển sang file tiếp theo nếu file hiện tại đã xong
        if is_file_finished:
            # Log báo xong file (giống rclone)
            self.log.emit(
                json.dumps(
                    {
                        "level": "info",
                        "msg": f"Đã sao chép (mới): {file_name}",
                        "size": file_size,
                    }
                )
            )

            self._current_file_idx += 1
            self._current_file_bytes = 0  # Reset cho file mới

            # Nếu đã hết file trong list -> Finish
            if self._current_file_idx >= len(self._fake_files):
                self._finish()

    def _finish(self):
        self._timer.stop()
        self._is_running = False

        # Emit 100%
        self.progress.emit(
            SyncProgressStatus.FINISHED, SyncProgressData(100.0, "Hoàn tất", 100, 0.0)
        )
        self.log.emit("> [MOCK] Hoàn tất. Mã thoát: 0")
        self.done.emit(0, QProcess.ExitStatus.NormalExit)
