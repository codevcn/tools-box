from pathlib import Path
from typing import TypedDict
from flask import json
from utils.helpers import get_json_field_value


class ConfigSchema(TypedDict):
    remotes: list[str]
    active_remote: str | None
    last_sync: str | None
    last_gdrive_entered_dir: str | None


class DataManager:
    def __init__(self):
        self.config_path = Path(__file__).parent / "sync-with-gdrive.json"

    def get_entire_config(self) -> ConfigSchema:
        """Lấy toàn bộ nội dung file cấu hình sync-with-gdrive.json dưới dạng dict."""
        try:
            if not self.config_path.exists():
                return ConfigSchema(
                    remotes=[],
                    active_remote=None,
                    last_sync=None,
                    last_gdrive_entered_dir=None,
                )
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception:
            return ConfigSchema(
                remotes=[],
                active_remote=None,
                last_sync=None,
                last_gdrive_entered_dir=None,
            )

    def get_last_gdrive_entered_dir(self) -> str | None:
        """Trả về gdrive root dir đã lưu (nếu có)."""
        return get_json_field_value("last_gdrive_entered_dir", self.config_path)

    def get_remotes_list(self) -> list[str]:
        """Trả về danh sách remotes đã cấu hình trong rclone."""
        remotes = get_json_field_value("remotes", self.config_path)
        if isinstance(remotes, list):
            return remotes
        return []

    def is_empty_remotes_list(self) -> bool:
        """Kiểm tra xem danh sách remotes có rỗng không."""
        remotes = self.get_remotes_list()
        return len(remotes) == 0

    def get_active_remote(self) -> str | None:
        """Trả về remote đang được sử dụng (nếu có)."""
        return get_json_field_value("active_remote", self.config_path)

    def save_active_remote(self, remote_name: str) -> None:
        """Lưu remote đang được sử dụng."""
        try:
            if not self.config_path.exists():
                data = {}
            else:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["active_remote"] = remote_name
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f">>> Error saving active remote: {e}")
            raise e

    def add_new_remote(self, remote_name: str) -> None:
        """Thêm remote mới vào danh sách remotes đã cấu hình."""
        try:
            if not self.config_path.exists():
                data = {"remotes": []}
            else:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            remotes = data.get("remotes", [])
            if remote_name not in remotes:
                remotes.append(remote_name)
                data["remotes"] = remotes
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f">>> Error adding new remote: {e}")
            raise e
