"""
This script handles git operations for the runner project.

The script takes command line arguments to perform git operations:
- First argument: git operation type (currently only supports "commit")
- Remaining arguments: commit message (when operation is "commit")

For commit operations:
- Opens a new Windows Terminal window
- Changes to the runner root directory
- Runs git add, commit and push commands in sequence
- Uses the provided commit message

Example usage:
python runner_git.py commit "update readme"

Constants:
RUNNER_GIT_TYPE: The supported git operation ("commit")
RUNNER_ROOT_DIR: Root directory path for the runner project
"""

import sys
import subprocess
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/runner/.env")

RUNNER_GIT_TYPE = "commit"
RUNNER_GIT_REMOTE = "remote"
RUNNER_ROOT_DIR = os.getenv("ROOT_FOLDER_PATH")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(">>> No valid git command found.")
        sys.exit(1)
    git_type = sys.argv[1]
    if git_type == RUNNER_GIT_TYPE:
        if len(sys.argv) < 3:
            print(">>> Missing commit message.")
            sys.exit(1)
        commit_message = " ".join(sys.argv[2:])  # Lấy toàn bộ phần còn lại
        cmd = (
            f'wt nt -d "{RUNNER_ROOT_DIR}" '
            f'cmd /k "git add . && git commit -m \\"{commit_message}\\" && git push origin main"'
        )
        subprocess.run(cmd, shell=True)
    elif git_type == RUNNER_GIT_REMOTE:
        cmd = f'wt nt -d "{RUNNER_ROOT_DIR}" ' f'cmd /k "git remote -v"'
        subprocess.run(cmd, shell=True)
    else:
        print(">>> No valid git command found.")
