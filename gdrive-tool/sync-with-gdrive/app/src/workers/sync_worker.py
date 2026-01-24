from __future__ import annotations

import os
import shutil
import tempfile
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
    copy_links: bool = True  # staging may use symlink -> rclone should follow
    show_progress: bool = True  # adds --progress
    extra_args: list[str] | None = None  # for advanced flags if needed


class RcloneSyncWorker(QObject):
    """
    Worker chạy rclone bằng QProcess (async, không block UI).

    - local_paths: list file/folder (mix được)
    - remote_name: tên remote rclone (vd: "mydrive")
    - gdrive_path: path folder đích trên drive (vd: "MyFolder/SubFolder")
    """

    log = Signal(str)
    error = Signal(str)
    done = Signal(int, QProcess.ExitStatus)

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

    # -------- Public API --------
    def start(self) -> None:
        """Bắt đầu sync/copy."""
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

        print("> Starting rclone sync worker...")
        print(f"> Local paths: {self._local_paths}")
        print(f"> Active remote: {self._active_remote}")
        print(f"> Google Drive path: {self._gdrive_path}")

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
        """Hủy tiến trình rclone nếu đang chạy."""
        if self._process and self._process.state() != QProcess.ProcessState.NotRunning:
            self.log.emit("> Cancelling rclone process...")
            self._process.kill()

    # -------- Internal helpers --------
    def _create_staging_dir(self) -> str:
        staging_dir = tempfile.mkdtemp(prefix="sync_with_gdrive_")
        self.log.emit(f"> staging: {staging_dir}")
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
        """
        Tạo 1 thư mục staging chứa "nhiều entry" (file/folder) ở root.
        Ưu tiên symlink để nhanh; nếu fail (Windows policy/permission) thì fallback copy.
        """
        used_names: set[str] = set()

        def unique_name(name: str) -> str:
            base = name
            i = 1
            while name in used_names:
                name = f"{base} ({i})\\"
                i += 1
            used_names.add(name)
            return name

        for src in self._local_paths:
            src_path = Path(src)
            entry_name = unique_name(src_path.name)
            dst_path = Path(staging_dir) / entry_name

            # Try symlink first
            try:
                if src_path.is_dir():
                    os.symlink(str(src_path), str(dst_path), target_is_directory=True)
                else:
                    os.symlink(str(src_path), str(dst_path), target_is_directory=False)

                self.log.emit(f"> link: {src_path} -> {dst_path}")
                continue
            except Exception:
                # Fallback copy
                pass

            if src_path.is_dir():
                self.log.emit(f"> copy dir: {src_path} -> {dst_path}")
                shutil.copytree(src_path, dst_path)
            else:
                self.log.emit(f"> copy file: {src_path} -> {dst_path}")
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)

    def _run_rclone(self, staging_dir: str) -> None:
        # Choose command by action
        cmd = "copy" if self._options.action == SyncAction.ONLY_UPLOAD else "sync"

        dest = f"{self._active_remote}:{self._gdrive_path}"

        args: list[str] = [cmd, staging_dir, dest]

        if self._options.copy_links:
            # follow symlinks
            args.append("--copy-links")

        if self._options.show_progress:
            args.append("--progress")

        if self._options.extra_args:
            args.extend(self._options.extra_args)

        self.log.emit(f"> rclone {cmd}: {staging_dir} -> {dest}")

        proc = QProcess(self)
        self._process = proc

        proc.setProgram("rclone")
        proc.setArguments(args)

        proc.readyReadStandardOutput.connect(self._on_stdout)
        proc.readyReadStandardError.connect(self._on_stderr)
        proc.finished.connect(self._on_finished)

        proc.start()

        if not proc.waitForStarted(3000):
            raise RuntimeError(
                "Failed to start rclone process. Is rclone installed and in PATH?"
            )

    def _on_stdout(self) -> None:
        if not self._process:
            return
        text = bytes(self._process.readAllStandardOutput().data()).decode(
            errors="replace"
        )
        if text.strip():
            self.log.emit(text.rstrip())

    def _on_stderr(self) -> None:
        if not self._process:
            return
        text = bytes(self._process.readAllStandardError().data()).decode(
            errors="replace"
        )
        if text.strip():
            # rclone often prints progress/info to stderr too
            self.log.emit(text.rstrip())

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self.log.emit(f"> rclone finished: exit_code={exit_code}, status={exit_status}")
        self._running = False
        self._cleanup_staging()
        self.done.emit(exit_code, exit_status)

    def _cleanup_staging(self) -> None:
        if not self._staging_dir:
            return
        try:
            shutil.rmtree(self._staging_dir, ignore_errors=True)
            self.log.emit(f"> cleanup staging: {self._staging_dir}")
        finally:
            self._staging_dir = None
