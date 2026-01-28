import sys
from pathlib import Path

APP_SRC_DIR = Path(__file__).resolve().parent / "app" / "src"
sys.path.insert(0, str(APP_SRC_DIR))

from main import start_app  # noqa: E402 # type: ignore


def run_app():
    """
    Entry point cho:
    - double click SynRive.exe
    - context menu (file/folder/background/multi-select)
    """
    paths = sys.argv[1:]  # nhận toàn bộ path từ context menu
    start_app(paths)


if __name__ == "__main__":
    run_app()
