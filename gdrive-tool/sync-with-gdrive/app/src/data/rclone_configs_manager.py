import sys
from pathlib import Path
from ..utils.helpers import app_data_dir, resolve_from_root_dir
import os


class RCloneConfigManager:
    @staticmethod
    def rclone_config_path() -> Path:
        # %AppData%/SynRive/rclone/rclone.conf
        p = app_data_dir() / "rclone"
        p.mkdir(parents=True, exist_ok=True)
        return p / "rclone.conf"

    @staticmethod
    def init_rclone_config_path() -> str:
        config_path = RCloneConfigManager.rclone_config_path()
        if not config_path.exists():
            config_path.touch()
        os.environ["RCLONE_CONFIG"] = str(config_path)
        return str(config_path)

    @staticmethod
    def rclone_executable_path() -> str:
        """
        Trả về đường dẫn tuyệt đối đến rclone.exe:
        - Frozen (PyInstaller): nằm ở root bundle (cạnh exe)
        - Dev: lấy từ 1 vị trí bạn đặt rclone trong repo (gợi ý: app/dev/bin/rclone.exe)
        """
        path = ""
        if getattr(sys, "frozen", False):
            path = resolve_from_root_dir("rclone.exe")
        else:
            path = resolve_from_root_dir("app", "build", "bin", "rclone.exe")
        if not Path(path).exists():
            raise RuntimeError(f"Không tìm thấy rclone.exe tại: {path}")
        return path
