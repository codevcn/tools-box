from typing import TypedDict
import json
from pathlib import Path
from ..utils.helpers import get_json_field_value, set_json_field_value
from ..utils.helpers import app_data_dir


def create_data_config_path() -> Path:
    return app_data_dir() / "data" / "sync-with-gdrive.json"


class UserDataConfigSchema(TypedDict):
    remotes: list[str]
    active_remote: str | None
    last_sync: str | None
    last_gdrive_entered_dir: str | None


class UserDataManager:
    def __init__(self):
        self._data_config_path: Path = create_data_config_path()
        self._is_data_inited: bool = False

    @staticmethod
    def get_data_config_path() -> str:
        """Trả về đường dẫn file cấu hình sync-with-gdrive.json."""
        return str(create_data_config_path())

    def check_if_data_inited(self) -> bool:
        """
        Kiểm tra xem dữ liệu đã được khởi tạo chưa.
        """
        file_exists = self._data_config_path.exists()
        if file_exists:
            self._is_data_inited = True
        return self._is_data_inited

    def init_data_config_file(self) -> None:
        """Khởi tạo file cấu hình sync-with-gdrive.json nếu chưa tồn tại."""
        path = self._data_config_path

        # 1. Đảm bảo thư mục cha tồn tại
        path.parent.mkdir(parents=True, exist_ok=True)

        # 2. Nếu file chưa tồn tại thì tạo mới với dữ liệu mặc định
        if not path.exists():
            initial_data: UserDataConfigSchema = {
                "remotes": [],
                "active_remote": None,
                "last_sync": None,
                "last_gdrive_entered_dir": None,
            }

            with path.open("w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)

        # 3. Đánh dấu đã init
        self._is_data_inited = True

    def get_entire_config(self) -> UserDataConfigSchema:
        """Lấy toàn bộ nội dung file cấu hình sync-with-gdrive.json dưới dạng dict."""
        try:
            if not self._data_config_path.exists():
                return UserDataConfigSchema(
                    remotes=[],
                    active_remote=None,
                    last_sync=None,
                    last_gdrive_entered_dir=None,
                )
            with open(self._data_config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception:
            return UserDataConfigSchema(
                remotes=[],
                active_remote=None,
                last_sync=None,
                last_gdrive_entered_dir=None,
            )

    def get_last_gdrive_entered_dir(self) -> str | None:
        """Trả về gdrive root dir đã lưu (nếu có)."""
        return get_json_field_value(
            "last_gdrive_entered_dir", self._data_config_path, True
        )

    def get_remotes_list(self) -> list[str]:
        """Trả về danh sách remotes đã cấu hình trong rclone."""
        remotes = get_json_field_value("remotes", self._data_config_path, True)
        if isinstance(remotes, list):
            return remotes
        return []

    def is_empty_remotes_list(self) -> bool:
        """Kiểm tra xem danh sách remotes có rỗng không."""
        remotes = self.get_remotes_list()
        return len(remotes) == 0

    def get_active_remote(self) -> str | None:
        """Trả về remote đang được sử dụng (nếu có)."""
        return get_json_field_value("active_remote", self._data_config_path, True)

    def save_active_remote(self, remote_name: str) -> None:
        """Lưu remote đang được sử dụng."""
        set_json_field_value("active_remote", remote_name, self._data_config_path, True)

    def add_new_remote(self, remote_name: str) -> None:
        """Thêm remote mới vào danh sách remotes đã cấu hình."""
        remotes = self.get_remotes_list()
        if remote_name not in remotes:
            remotes.append(remote_name)
            set_json_field_value("remotes", remotes, self._data_config_path, True)

    def save_last_gdrive_entered_dir(self, gdrive_dir: str) -> None:
        """Lưu gdrive root dir đã nhập gần nhất."""
        set_json_field_value(
            "last_gdrive_entered_dir", gdrive_dir, self._data_config_path, True
        )
