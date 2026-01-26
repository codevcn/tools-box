# File dùng cho send to menu (chọn nhiều file -> gom nhiều file chạy script một lần)

import sys
import subprocess

PYTHON_EXE_FILE_PATH = r"D:\Python-3-12\python.exe"
APP_PY_FILE_PATH = r"D:\D-Documents\TOOLs\gdrive-tool\sync-with-gdrive\app\src\app.py"


def run_app():
    paths = sys.argv[1:]
    subprocess.Popen([PYTHON_EXE_FILE_PATH, APP_PY_FILE_PATH, *paths])


if __name__ == "__main__":
    run_app()
