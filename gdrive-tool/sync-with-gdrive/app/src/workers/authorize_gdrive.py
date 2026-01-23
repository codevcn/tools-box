from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QProcess


@dataclass
class RcloneRemote:
    name: str
    type: str = "drive"
    scope: str = "drive"
    token: dict | None = None


class RcloneAuth(QObject):
    log = Signal(str)
    success = Signal(dict)  # emit token dict
    error = Signal(str)

    def __init__(self, rclone_exe: str = "rclone", parent=None):
        super().__init__(parent)
        self.rclone_exe = rclone_exe
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)

        self.proc.readyReadStandardOutput.connect(self._on_ready_read)
        self.proc.finished.connect(self._on_finished)

        self._buffer = ""

    def start_authorize_drive(self) -> None:
        # rclone sẽ tự mở browser để login
        args = ["authorize", "drive"]
        self._buffer = ""
        self.log.emit(f">>> Running: {self.rclone_exe} {' '.join(args)}")
        self.proc.start(self.rclone_exe, args)

        if not self.proc.waitForStarted(3000):
            self.error.emit("Không chạy được rclone. Kiểm tra PATH hoặc rclone_exe.")
            return

    def _on_ready_read(self) -> None:
        text = bytes(self.proc.readAllStandardOutput().data()).decode(
            "utf-8", errors="replace"
        )
        self._buffer += text
        self.log.emit(text.rstrip())

    def _on_finished(self, exit_code: int, _status) -> None:
        if exit_code != 0:
            self.error.emit(f"Authorize thất bại (exit_code={exit_code}).")
            return

        token = self._extract_token_json(self._buffer)
        if not token:
            self.error.emit("Không tìm thấy token JSON trong output của rclone.")
            return

        self.success.emit(token)

    @staticmethod
    def _extract_token_json(output: str) -> dict | None:
        """
        rclone authorize drive thường in token JSON ra stdout.
        Ta cố gắng tìm đoạn {...} chứa access_token/refresh_token.
        """
        # tìm mọi object JSON dạng {...}
        candidates = re.findall(r"\{[\s\S]*?\}", output)
        for c in reversed(candidates):
            try:
                obj = json.loads(c)
                if isinstance(obj, dict) and (
                    "access_token" in obj or "refresh_token" in obj
                ):
                    return obj
            except Exception:
                pass
        return None

    def save_remote_to_json_file(
        self,
        json_path: Path,
        remote: RcloneRemote,
    ) -> None:
        json_path.parent.mkdir(parents=True, exist_ok=True)

        data = {"remotes": []}
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    data = {"remotes": []}
            except Exception:
                data = {"remotes": []}

        remotes: list[dict] = data.get("remotes", [])
        if not isinstance(remotes, list):
            remotes = []

        # upsert theo name
        new_item = {
            "name": remote.name,
            "type": remote.type,
            "scope": remote.scope,
            "token": remote.token,
        }

        replaced = False
        for i, item in enumerate(remotes):
            if isinstance(item, dict) and item.get("name") == remote.name:
                remotes[i] = new_item
                replaced = True
                break

        if not replaced:
            remotes.append(new_item)

        data["remotes"] = remotes
        json_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
