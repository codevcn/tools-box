from __future__ import annotations

import subprocess
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "app" / "src" / "__init__.py"


def run(cmd: list[str]):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd)


def read_version() -> str:
    text = VERSION_FILE.read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*["\'](.+?)["\']', text)
    if not m:
        raise RuntimeError("Không tìm thấy __version__ trong __init__.py")
    return m.group(1)


def main():
    if len(sys.argv) < 2:
        print('Usage: py scripts/git_commit.py "commit message"')
        sys.exit(1)

    message = sys.argv[1]
    version = read_version()
    tag = f"v{version}"

    print(f"Commit message: {message}")
    print(f"Version: {version}")
    print(f"Tag: {tag}")

    # 1. add all
    run(["git", "add", "-A"])

    # 2. commit
    run(["git", "commit", "-m", message])

    # 3. create tag
    run(["git", "tag", tag])

    # 4. push commit
    run(["git", "push"])

    # 5. push tag
    run(["git", "push", "--tags"])

    print("Xong ✅")


if __name__ == "__main__":
    main()
