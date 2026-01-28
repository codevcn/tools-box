from __future__ import annotations

import os
import shutil
import tempfile
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QProcess
from ..utils.helpers import rclone_executable_path
from ..data.data_manager import UserDataManager

LOG_SPEED_INTERVAL: str = "0.5s"  # Tốc độ lấy log


@dataclass
class SyncProgressData:
    percent: float  # % Tổng thể (Global progress)
    file_name: str  # Tên file đang xử lý
    current_file_percent: float  # % Của file hiện tại (NEW)
    speed: float  # Tốc độ bytes/giây


class SyncAction(str, Enum):
    ONLY_UPLOAD = "only_upload"
    UPLOAD_AND_DELETE = "upload_and_delete"


class SyncProgressStatus(str, Enum):
    STARTING = "starting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"


@dataclass(frozen=True)
class SyncOptions:
    action: SyncAction = SyncAction.ONLY_UPLOAD
    copy_links: bool = True
    show_progress: bool = True
    extra_args: list[str] | None = None


class RcloneSyncWorker(QObject):
    log = Signal(str)
    error = Signal(str)
    done = Signal(int, QProcess.ExitStatus)

    # [MODIFIED] Signal giờ sẽ emit một object SyncProgressData
    # (Bắt đầu progress, Sync progress data)
    progress = Signal(SyncProgressStatus, SyncProgressData)

    def __init__(
        self,
        local_paths: list[str],
        gdrive_path: str,
        options: SyncOptions | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._data_manager: UserDataManager = UserDataManager()

        active_remote = self._data_manager.get_active_remote()
        if not active_remote:
            raise ValueError(
                "Không tìm thấy kho lưu trữ đang hoạt động. Vui lòng đăng nhập trước."
            )

        self._local_paths = [str(p) for p in local_paths]
        self._active_remote = active_remote
        self._gdrive_path = gdrive_path.strip().strip("/")

        self._options = options or SyncOptions()

        self._process: QProcess | None = None
        self._staging_dir: str | None = None
        self._running: bool = False
        self._is_cancelled: bool = False  # [NEW] Thêm cờ này

    def start(self) -> None:
        if self._running:
            self.log.emit("> Đồng bộ đang chạy rồi.")
            return

        try:
            self._validate_inputs()
        except Exception as e:
            self.error.emit(str(e))
            self.done.emit(1, QProcess.ExitStatus.CrashExit)
            return

        self._running = True
        self._is_cancelled = False  # [NEW] Reset cờ khi bắt đầu
        self.log.emit("> Đang khởi động công cụ đồng bộ...")

        # Emit trạng thái khởi tạo
        self.progress.emit(
            SyncProgressStatus.STARTING,
            SyncProgressData(0.0, "Đang khởi động...", 0.0, 0.0),
        )

        try:
            self._staging_dir = self._create_staging_dir()
            self._prepare_staging(self._staging_dir)
            self._run_rclone(self._staging_dir)
        except Exception as e:
            self._running = False
            self._cleanup_staging()
            self.error.emit(str(e))
            self.done.emit(1, QProcess.ExitStatus.CrashExit)

    def cancel(self) -> None:
        """Hủy quá trình đồng bộ ngay lập tức."""
        if not self._running:
            return

        self._is_cancelled = True
        self.log.emit("> [Người dùng] Đã yêu cầu hủy. Đang dừng quá trình...")

        # Nếu process đang chạy thì kill
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            # Lưu ý: kill() sẽ trigger signal finished, nên logic dọn dẹp để ở _on_finished
        else:
            # Nếu process chưa kịp chạy (đang ở giai đoạn prepare staging),
            # ta phải tự gọi dọn dẹp
            self._on_finished(1, QProcess.ExitStatus.CrashExit)

    # ... (Các hàm _create_staging_dir, _validate_inputs, _prepare_staging giữ nguyên) ...
    def _create_staging_dir(self) -> str:
        return tempfile.mkdtemp(prefix="sync_with_gdrive_")

    def _validate_inputs(self) -> None:
        if not self._active_remote:
            raise ValueError(
                "Tên remote trống. Vui lòng đăng nhập hoặc chọn remote đang hoạt động."
            )
        if not self._gdrive_path:
            raise ValueError("Đường dẫn đích trên Google Drive trống.")
        if not self._local_paths:
            raise ValueError("Không có đường dẫn cục bộ để đồng bộ.")
        for p in self._local_paths:
            if not Path(p).exists():
                raise FileNotFoundError(f"Đường dẫn cục bộ không tồn tại: {p}")

    def _prepare_staging(self, staging_dir: str) -> None:
        used_names: set[str] = set()

        def unique_name(name: str) -> str:
            base = name
            i = 1
            while name in used_names:
                name = f"{base} ({i})"
                i += 1
            used_names.add(name)
            return name

        for src in self._local_paths:
            src_path = Path(src)
            entry_name = unique_name(src_path.name)
            dst_path = Path(staging_dir) / entry_name
            try:
                if src_path.is_dir():
                    os.symlink(str(src_path), str(dst_path), target_is_directory=True)
                else:
                    os.symlink(str(src_path), str(dst_path), target_is_directory=False)
                continue
            except Exception:
                if src_path.is_dir():
                    shutil.copytree(src_path, dst_path)
                else:
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)

    def _run_rclone(self, staging_dir: str) -> None:
        cmd = "copy" if self._options.action == SyncAction.ONLY_UPLOAD else "sync"
        dest = f"{self._active_remote}:{self._gdrive_path}"
        args: list[str] = [cmd, staging_dir, dest]
        if self._options.copy_links:
            args.append("--copy-links")
        args.extend(["--use-json-log", "--stats", LOG_SPEED_INTERVAL, "--verbose"])
        if self._options.extra_args:
            args.extend(self._options.extra_args)

        self.log.emit(f"> Đang thực thi: rclone {cmd}")
        proc = QProcess(self)
        self._process = proc
        rclone_path = rclone_executable_path()
        if not Path(rclone_path).exists():
            raise RuntimeError(f"Không tìm thấy rclone.exe: {rclone_path}")
        proc.setProgram(rclone_path)
        proc.setArguments(args)
        proc.readyReadStandardError.connect(self._on_stderr)
        proc.readyReadStandardOutput.connect(self._on_stdout)
        proc.finished.connect(self._on_finished)
        proc.start()
        if not proc.waitForStarted(3000):
            raise RuntimeError("Không thể khởi động rclone.")

    def _on_stdout(self) -> None:
        if not self._process:
            return
        self._parse_output(self._process.readAllStandardOutput().data())

    def _on_stderr(self) -> None:
        if not self._process:
            return
        self._parse_output(self._process.readAllStandardError().data())

    def _parse_output(self, raw_bytes: bytes) -> None:
        text_block = bytes(raw_bytes).decode(errors="replace")

        for line in text_block.splitlines():
            line = line.strip()
            if not line:
                continue

            try:
                json_data = json.loads(line)
                # print(f">>> Parsed JSON: {json_data}") # Uncomment để debug

                # 1. Xử lý Progress (stats)
                if "stats" in json_data:
                    stats = json_data["stats"]
                    total_bytes = stats.get("totalBytes", 0)
                    transferred_bytes = stats.get("bytes", 0)
                    speed = float(stats.get("speed", 0))

                    # Tính % Tổng thể
                    percent = 0.0
                    if total_bytes > 0:
                        percent = (transferred_bytes / total_bytes) * 100

                    # Chặn spam 100%
                    if percent >= 100.0 or (
                        total_bytes > 0 and transferred_bytes >= total_bytes
                    ):
                        return

                    # --- [LOGIC MỚI] Xử lý từng file ---
                    transferring_list = stats.get("transferring", [])
                    current_file_name = "Đang tính toán..."
                    current_file_percent = 0  # Mặc định 0%

                    if transferring_list:
                        # Lấy file đầu tiên đang chạy
                        current_item = transferring_list[0]
                        current_file_name = current_item.get("name", "Không rõ")

                        # Rclone thường trả về field 'percentage' sẵn
                        if "percentage" in current_item:
                            current_file_percent = int(current_item["percentage"])
                        else:
                            # Fallback: tự tính nếu không có field percentage
                            c_bytes = current_item.get("bytes", 0)
                            c_size = current_item.get("size", 0)
                            if c_size > 0:
                                current_file_percent = int((c_bytes / c_size) * 100)

                    # Emit dữ liệu bao gồm cả % file lẻ
                    progress_data = SyncProgressData(
                        percent=percent,
                        file_name=current_file_name,
                        current_file_percent=current_file_percent,  # Field mới
                        speed=speed,
                    )
                    self.progress.emit(SyncProgressStatus.IN_PROGRESS, progress_data)

                # 2. Xử lý Log (Giữ nguyên)
                if "msg" in json_data and "stats" not in json_data:
                    level = json_data.get("level", "INFO")
                    msg = json_data.get("msg", "")
                    self.log.emit(f"[{level}] {msg}")

            except json.JSONDecodeError:
                self.log.emit(line)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._running = False
        self._cleanup_staging()

        # [MODIFIED] Kiểm tra xem có phải người dùng bấm hủy không
        if self._is_cancelled:
            # Emit trạng thái Cancelled (Percent giữ nguyên hoặc set về 0)
            self.progress.emit(
                SyncProgressStatus.FINISHED,
                SyncProgressData(0.0, "Được hủy bởi người dùng.", 0.0, 0.0),
            )
            self.log.emit(f"> Quá trình đồng bộ đã bị hủy bởi người dùng.")
            # Emit done với mã lỗi đặc biệt (ví dụ -1) để UI biết
            self.done.emit(-1, QProcess.ExitStatus.CrashExit)

        elif exit_status == QProcess.ExitStatus.NormalExit and exit_code == 0:
            # Trường hợp thành công thực sự
            self.progress.emit(
                SyncProgressStatus.FINISHED,
                SyncProgressData(100.0, "Đã đồng bộ xong.", 100.0, 0.0),
            )
            self.log.emit(f"> Đã đồng bộ xong. Mã thoát: {exit_code}.")
            self.done.emit(exit_code, exit_status)

        else:
            # Trường hợp lỗi (Rclone trả về lỗi)
            self.progress.emit(
                SyncProgressStatus.FINISHED,
                SyncProgressData(0.0, "Đã xảy ra lỗi", 0.0, 0.0),
            )
            self.log.emit(f"> Thất bại với mã thoát: {exit_code}")
            self.done.emit(exit_code, exit_status)

    def _cleanup_staging(self) -> None:
        if not self._staging_dir:
            return
        try:
            shutil.rmtree(self._staging_dir, ignore_errors=True)
        finally:
            self._staging_dir = None
