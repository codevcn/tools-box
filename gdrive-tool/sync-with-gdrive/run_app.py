import sys
from pathlib import Path
import subprocess

PYTHON_EXE_FILE_PATH = r"D:\Python-3-12\python.exe"
APP_PY_FILE_PATH = r"D:\D-Documents\TOOLs\gdrive-tool\sync-with-gdrive\app\src\app.py"


def get_selected_paths() -> list[str]:
    """
    Lấy danh sách path được truyền từ Windows (Send To / shortcut).

    - Bỏ argv[0] (script path)
    - Chuẩn hóa path tuyệt đối
    - Loại trùng
    - Giữ nguyên thứ tự
    """

    raw_args = sys.argv[1:]

    seen = set()
    result: list[str] = []

    for arg in raw_args:
        if not arg:
            continue

        p = Path(arg).resolve()

        # (tuỳ chọn) chỉ lấy path tồn tại
        if not p.exists():
            continue

        key = str(p)
        if key in seen:
            continue

        seen.add(key)
        result.append(key)

    return result


def run_app():
    valid_paths = get_selected_paths()
    print(">>> paths:", valid_paths)

    # gọi app 1 lần, truyền nhiều path (khuyến nghị)
    subprocess.Popen([PYTHON_EXE_FILE_PATH, APP_PY_FILE_PATH, *valid_paths])



if __name__ == "__main__":
    run_app()
