import sys
from app.src.main import start_app


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
