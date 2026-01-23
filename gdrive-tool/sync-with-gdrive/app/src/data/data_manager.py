from pathlib import Path
from utils.helpers import get_json_field_value


class DataManager:
    def __init__(self):
        self.config_path = Path(__file__).parent / "sync-with-gdrive.json"

    def get_saved_gdrive_root_dir(self) -> str | None:
        """Trả về gdrive root dir đã lưu (nếu có)."""
        return get_json_field_value("saved_gdrive_root_dir", self.config_path)

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
