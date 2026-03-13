import os
import re
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

USER_DATA_DIR = r"C:\Users\dell\AppData\Local\Google\Chrome\User Data"
DOWNLOAD_DIRECTORIES_DIR = r"D:\D-Downloads"
PROFILE_DIR_RE = re.compile(r"^(Default|Profile \d+)$")


def is_chrome_running() -> bool:
    try:
        out = subprocess.check_output(
            ["tasklist"], text=True, encoding="utf-8", errors="ignore"
        )
        return "chrome.exe" in out.lower()
    except Exception:
        return False


def read_last_used_profile(user_data: Path) -> str | None:
    local_state = user_data / "Local State"
    if not local_state.exists():
        return None
    try:
        data = json.loads(local_state.read_text(encoding="utf-8"))
        return data.get("profile", {}).get("last_used")
    except Exception:
        return None


def get_current_download_dir(pref_path: Path) -> str | None:
    try:
        data = json.loads(pref_path.read_text(encoding="utf-8"))
        dl = data.get("download", {})
        if isinstance(dl, dict):
            return dl.get("default_directory")
    except Exception:
        pass
    return None


def set_download_dir_in_preferences(pref_path: Path, download_dir: str) -> bool:
    try:
        data = json.loads(pref_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[SKIP] Ko đọc/parse dc JSON: {pref_path} ({e})")
        return False

    download = data.get("download")
    if not isinstance(download, dict):
        download = {}
        data["download"] = download

    download["default_directory"] = download_dir
    download["prompt_for_download"] = False
    download["directory_upgrade"] = True

    try:
        pref_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True
    except Exception as e:
        print(f"[FAIL] Ko ghi dc Preferences: {pref_path} ({e})")
        return False


def init_download_dir() -> str:
    """
    Lấy tham số path truyền vào khi chạy file. Nếu có path thì dùng path làm thư mục tải về.
    Còn ko có path thì quét DOWNLOAD_DIRECTORIES_DIR để tìm folder có index lớn nhất từ trc
    và tạo 1 folder download-{index mới}.
    """
    # 1. Nếu có truyền path vào khi chạy script (ví dụ: python script.py D:\MyPath)
    if len(sys.argv) > 1:
        custom_path = Path(sys.argv[1])
        custom_path.mkdir(parents=True, exist_ok=True)
        print(f"Sử dụng đường dẫn tham số = {custom_path}")
        return str(custom_path.resolve())

    # 2. Nếu ko truyền path, quét thư mục gốc
    base_dir = Path(DOWNLOAD_DIRECTORIES_DIR)
    base_dir.mkdir(parents=True, exist_ok=True)

    max_index = 0
    folder_pattern = re.compile(r"^download-(\d+)$")

    for item in base_dir.iterdir():
        if item.is_dir():
            match = folder_pattern.match(item.name)
            if match:
                current_index = int(match.group(1))
                if current_index > max_index:
                    max_index = current_index

    # 3. Tạo thư mục với index mới
    new_index = max_index + 1
    new_folder_name = f"download-{new_index}"
    new_path = base_dir / new_folder_name

    new_path.mkdir(parents=True, exist_ok=True)
    print(f"Tự động tạo thư mục tải về mới = {new_path}")
    return str(new_path.resolve())


def main():
    if is_chrome_running():
        print(
            "❗ Chrome đang chạy (chrome.exe). Hãy tắt Chrome hoàn toàn trc, ko thì sẽ bị ghi đè lại."
        )
        print("⚙️  Chạy lệnh sau để tắt Chrome (cẩn thận với các tab đang mở):")
        # /F = Force (ép tắt)
        # /IM chrome.exe = tất cả tiến trình Chrome
        # /T = kill cả tiến trình con
        print("taskkill /F /IM chrome.exe /T")
        print("")
        return

    user_data = Path(USER_DATA_DIR)

    # Khởi tạo thư mục download
    download_dir = init_download_dir()

    if not user_data.exists():
        raise FileNotFoundError(f"USER_DATA_DIR ko tồn tại: {user_data}")

    last_used = read_last_used_profile(user_data)
    if last_used:
        print(f"Last used profile (theo Local State): {last_used}")

    profile_dirs = []
    for name in os.listdir(user_data):
        if PROFILE_DIR_RE.match(name):
            pref = user_data / name / "Preferences"
            if pref.exists():
                profile_dirs.append((name, pref))

    if not profile_dirs:
        print("Ko tìm thấy profile nào (Default / Profile N) có file Preferences.")
        return

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(
        f"\nFound {len(profile_dirs)} profiles. Target download dir = {download_dir}\n"
    )

    ok = 0
    for profile_name, pref_path in sorted(profile_dirs, key=lambda x: x[0]):
        before = get_current_download_dir(pref_path)

        backup_path = pref_path.with_suffix(f".bak.{stamp}")
        try:
            shutil.copy2(pref_path, backup_path)
        except Exception as e:
            print(f"[SKIP] {profile_name}: ko backup dc ({e})")
            continue

        if set_download_dir_in_preferences(pref_path, download_dir):
            after = get_current_download_dir(pref_path)
            ok += 1
            print(f"[OK]  {profile_name}:")
            print(f"      before: {before}")
            print(f"      after : {after}")
            print(f"      backup: {backup_path.name}")
        else:
            print(
                f"[FAIL] {profile_name}: update thất bại (backup: {backup_path.name})"
            )

    print(f"\n✅ Done. Updated {ok}/{len(profile_dirs)} profiles.")
    print(
        "⚠️ Nếu mở Chrome lên lại bị quay về path cũ → gần như chắc chắn do Chrome Sync hoặc Chrome vẫn chạy nền."
    )


if __name__ == "__main__":
    main()
