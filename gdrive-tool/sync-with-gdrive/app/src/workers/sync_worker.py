from __future__ import annotations

import os
import shutil
import tempfile
import json  # [NEW] Import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QProcess
from data.data_manager import DataManager


class SyncAction(str, Enum):
    ONLY_UPLOAD = "only_upload"  # rclone copy
    UPLOAD_AND_DELETE = "upload_and_delete"  # rclone sync (may delete in destination)


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

    # [NEW] Signal tiến trình: (percent 0-100, speed/status string)
    progress = Signal(float, str)

    def __init__(
        self,
        local_paths: list[str],
        gdrive_path: str,
        options: SyncOptions | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._data_manager: DataManager = DataManager()

        active_remote = self._data_manager.get_active_remote()
        if not active_remote:
            raise ValueError("No active remote found. Please login first.")

        self._local_paths = [str(p) for p in local_paths]
        self._active_remote = active_remote
        self._gdrive_path = gdrive_path.strip().strip("/")

        self._options = options or SyncOptions()

        self._process: QProcess | None = None
        self._staging_dir: str | None = None
        self._running: bool = False

    def start(self) -> None:
        if self._running:
            self.log.emit("> Sync already running.")
            return

        try:
            self._validate_inputs()
        except Exception as e:
            self.error.emit(str(e))
            self.done.emit(1, QProcess.ExitStatus.CrashExit)
            return

        self._running = True
        self.log.emit("> Starting rclone sync worker...")
        # Reset progress về 0 khi bắt đầu
        self.progress.emit(0.0, "Starting...")

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
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self.log.emit("> Cancelling rclone process...")
            self._process.kill()

    # -------- Internal helpers --------
    def _create_staging_dir(self) -> str:
        staging_dir = tempfile.mkdtemp(prefix="sync_with_gdrive_")
        return staging_dir

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
        self.log.emit(f"> Preparing staging directory at {staging_dir}...")
        used_names: set[str] = set()

        def unique_name(name: str) -> str:
            base = name
            i = 1
            while name in used_names:
                name = f"{base} ({i})"  # Fix: bỏ dấu \\ thừa ở code cũ
                i += 1
            used_names.add(name)
            return name

        for src in self._local_paths:
            src_path = Path(src)
            entry_name = unique_name(src_path.name)
            dst_path = Path(staging_dir) / entry_name

            try:
                # Try symlink
                if src_path.is_dir():
                    os.symlink(str(src_path), str(dst_path), target_is_directory=True)
                else:
                    os.symlink(str(src_path), str(dst_path), target_is_directory=False)
                continue
            except Exception:
                pass  # Fallback copy

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

        # [MODIFIED] Setup arguments cho JSON output
        # --use-json-log: output log dạng JSON
        # --stats 0.5s: Cập nhật status mỗi 0.5s
        # --verbose: Để hiện đủ thông tin
        args.extend(["--use-json-log", "--stats", "0.5s", "--verbose"])

        if self._options.extra_args:
            args.extend(self._options.extra_args)

        self.log.emit(f"> Executing: rclone {cmd}")

        proc = QProcess(self)
        self._process = proc
        proc.setProgram("rclone")
        proc.setArguments(args)

        # Rclone thường output log/stats qua Stderr
        proc.readyReadStandardError.connect(self._on_stderr)
        proc.readyReadStandardOutput.connect(self._on_stdout)
        proc.finished.connect(self._on_finished)

        proc.start()
        if not proc.waitForStarted(3000):
            raise RuntimeError("Failed to start rclone.")

    def _on_stdout(self) -> None:
        # Đôi khi rclone output ra stdout tùy version/config
        if not self._process:
            return
        data = self._process.readAllStandardOutput().data()
        self._parse_output(data)

    def _on_stderr(self) -> None:
        # JSON logs chủ yếu nằm ở đây
        if not self._process:
            return
        data = self._process.readAllStandardError().data()
        self._parse_output(data)

    def _parse_output(self, raw_bytes: bytes) -> None:
        """Parse raw bytes từ rclone process"""
        text_block = bytes(raw_bytes).decode(errors="replace")

        # Output có thể chứa nhiều dòng JSON
        for line in text_block.splitlines():
            line = line.strip()
            if not line:
                continue

            try:
                # Cố gắng parse JSON
                json_data = json.loads(line)

                # 1. Xử lý Progress (stats)
                if "stats" in json_data:
                    stats = json_data["stats"]
                    total_bytes = stats.get("totalBytes", 0)
                    transferred_bytes = stats.get("bytes", 0)
                    speed = stats.get("speed", 0)  # bytes/s

                    # Tính %
                    percent = 0.0
                    if total_bytes > 0:
                        percent = (transferred_bytes / total_bytes) * 100

                    # Format speed string (vd: 1.2 MB/s)
                    speed_str = self._format_size(speed) + "/s"

                    # Emit signal để UI update
                    self.progress.emit(percent, f"Uploading... {speed_str}")

                # 2. Xử lý Log message (để hiện lên UI log như cũ)
                # JSON log có field "msg" và "level"
                if "msg" in json_data:
                    level = json_data.get("level", "INFO")
                    msg = json_data.get("msg", "")
                    # Chỉ emit log nếu không phải là bản tin stats thuần túy
                    if "stats" not in json_data:
                        self.log.emit(f"[{level}] {msg}")

            except json.JSONDecodeError:
                # Nếu không phải JSON (trường hợp rclone lỗi fatal hoặc version cũ), cứ in raw
                self.log.emit(line)

    def _format_size(self, size_bytes: float) -> str:
        """Helper format bytes ra MB/GB"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self.progress.emit(100.0, "Finished")  # Đảm bảo về đích 100%
        self.log.emit(f"> Done. Exit code: {exit_code}")
        self._running = False
        self._cleanup_staging()
        self.done.emit(exit_code, exit_status)

    def _cleanup_staging(self) -> None:
        if not self._staging_dir:
            return
        try:
            shutil.rmtree(self._staging_dir, ignore_errors=True)
        finally:
            self._staging_dir = None
