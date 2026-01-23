from __future__ import annotations
import os
import shutil
import tempfile
from pathlib import Path
from PySide6.QtCore import QThread, Signal, QProcess


class RcloneSyncWorker(QThread):
    """Worker thread để chạy rclone (copy/sync) không block UI."""

    log = Signal(str)
    done = Signal(int, QProcess.ExitStatus)

    def __init__(self, local_paths: list[str], gdrive_path: str):
        super().__init__()
        self.local_paths = local_paths
        self.gdrive_path = gdrive_path
        self.rclone_exe = (
            r"D:\Programs-ver-Later\rclone-v1.72.1-windows-amd64\rclone.exe"
        )
        self.remote_name = "gdrive"
        self.prefer_symlink = True
        self._proc: QProcess | None = None
        self._staging_dir: Path | None = None

    # -----------------------------
    # Public API
    # -----------------------------
    def sync_multi_entries(self) -> None:
        """Only upload (không xóa gì ở đích): gom staging rồi rclone copy 1 lần."""
        try:
            self._start_copy_with_staging()
        except Exception as e:
            self.log.emit(f"ERROR: {e}")
            self.done.emit(1, QProcess.ExitStatus.CrashExit)

    # -----------------------------
    # Internal helpers
    # -----------------------------
    def _start_copy_with_staging(self) -> None:
        srcs = self._normalize_existing_paths(self.local_paths)
        if not srcs:
            self.log.emit("No valid local paths to upload.")
            self.done.emit(0, QProcess.ExitStatus.NormalExit)
            return

        staging_dir = Path(tempfile.mkdtemp(prefix="rclone_staging_"))
        self._staging_dir = staging_dir

        try:
            for src in srcs:
                self._stage_entry(src, staging_dir, prefer_symlink=self.prefer_symlink)
        except Exception:
            shutil.rmtree(staging_dir, ignore_errors=True)
            self._staging_dir = None
            raise

        dest_remote = self._build_dest_remote(self.remote_name, self.gdrive_path)

        args = [
            "copy",
            str(staging_dir),
            dest_remote,
            "--copy-links",  # dereference symlink (nếu staging dùng symlink)
            "--progress",
        ]

        proc = QProcess(self)
        self._proc = proc
        proc.setProgram(self.rclone_exe)
        proc.setArguments(args)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        self.log.emit(f">>> STAGING: {staging_dir}")
        self.log.emit(">>> CMD: " + self._format_cmd(self.rclone_exe, args))

        proc.readyReadStandardOutput.connect(self._on_ready_read)
        proc.finished.connect(self._on_finished_cleanup)

        proc.start()

    def _normalize_existing_paths(self, local_paths: list[str]) -> list[Path]:
        srcs: list[Path] = []
        for p in local_paths:
            if not p:
                continue
            pp = Path(p).expanduser()
            if pp.exists():
                srcs.append(pp)
        return srcs

    def _stage_entry(
        self, src: Path, staging_dir: Path, *, prefer_symlink: bool
    ) -> None:
        dest = self._unique_dest_path(staging_dir, src.name)

        if prefer_symlink:
            try:
                if src.is_dir():
                    os.symlink(src, dest, target_is_directory=True)
                else:
                    os.symlink(src, dest)
                return
            except OSError as e:
                self.log.emit(f"Symlink failed for {src} -> fallback copy. ({e})")

        # fallback copy
        if src.is_dir():
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)

    def _unique_dest_path(self, staging_dir: Path, name: str) -> Path:
        dest = staging_dir / name
        if not dest.exists():
            return dest

        # tránh trùng tên: name_2, name_3...
        stem = Path(name).stem
        suffix = Path(name).suffix
        i = 2
        while (staging_dir / f"{stem}_{i}{suffix}").exists():
            i += 1
        return staging_dir / f"{stem}_{i}{suffix}"

    def _build_dest_remote(self, remote_name: str, gdrive_path: str) -> str:
        gdrive_path_norm = gdrive_path.strip().strip("/").strip("\\")
        return (
            f"{remote_name}:{gdrive_path_norm}"
            if gdrive_path_norm
            else f"{remote_name}:"
        )

    def _format_cmd(self, exe: str, args: list[str]) -> str:
        def q(a: str) -> str:
            return f'"{a}"' if " " in a else a

        return q(exe) + " " + " ".join(q(a) for a in args)

    # -----------------------------
    # QProcess slots
    # -----------------------------
    def _on_ready_read(self) -> None:
        if not self._proc:
            return

        raw = self._proc.readAllStandardOutput()  # QByteArray
        text = raw.toStdString()  # ✅ Qt-native, no typing drama

        if text:
            self.log.emit(text.rstrip())

    def _on_finished_cleanup(self, code: int, status: QProcess.ExitStatus) -> None:
        if self._staging_dir:
            shutil.rmtree(self._staging_dir, ignore_errors=True)
            self.log.emit(f">>> Cleaned staging: {self._staging_dir}")
            self._staging_dir = None

        self.done.emit(code, status)
        self._proc = None
