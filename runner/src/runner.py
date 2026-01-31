import argparse
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/runner/.env")

# --- Static parameters (constants) ---
RUNNER_STATUS = "OK"
RUNNER_TYPE_OPEN = "open"
RUNNER_TYPE_CODE = "code"
RUNNER_TYPE_RUN = "run"
RUNNER_TYPE_PRINT = "print"
RUNNER_TYPE_GIT = "git"

# --- Actions ---
# google drive
RUNNER_GDRIVE = "gdrive"
# open
RUNNER_OPEN_ENV = "env"
# code
RUNNER_CODE_VSCODE_WORKSPACE = "ws"
RUNNER_CODE_TEST = "test"
RUNNER_CODE_TYPESCRIPT_TEMPLATE = "ts-template"
RUNNER_CODE_JS = "js"
RUNNER_CODE_TS = "ts"
RUNNER_CODE_NESTJS = "nestjs"
RUNNER_CODE_PY = "py"
RUNNER_CODE_EXTENSIONS = "ext"
# run
RUNNER_RUN_TEST_BAT = "test-bat"
RUNNER_RUN_UNIKEY_APP = "unikey"
# git
RUNNER_GIT_COMMIT_AND_PUSH = "commit"
# print
RUNNER_PRINT_OS_INFO = "os"
RUNNER_PRINT_STATUSES_INFO = "stts"
RUNNER_PRINT_VSCODE_WORKSPACES = "ws"
RUNNER_PRINT_CURL = "curl"
RUNNER_PRINT_DIRECTORY = "dir"
RUNNER_PRINT_USEFUL_COMMANDS = "cmds"

RUNNER_FLAG_H = "-h"
RUNNER_FLAG_M = "-m"
RUNNER_FLAG_V = "-v"
RUNNER_FLAG_C = "-c"
RUNNER_FLAG_CURSOR = "--cursor"
RUNNER_FLAG_HELP = "--help"
RUNNER_FLAG_MESSAGE = "--message"
RUNNER_FLAG_VALUE = "--value"

RUNNER_WARNING_TYPE_WRONG = "WRONG-TYPE"
RUNNER_WARNING_TYPE_MISSING = "MISSING-TYPE"
RUNNER_WARNING_ACTION_WRONG = "WRONG-ACTION"
RUNNER_WARNING_ACTION_MISSING = "MISSING-ACTION"
RUNNER_WARNING_FLAG_WRONG = "WRONG-FLAG"
RUNNER_WARNING_FLAG_MISSING = "MISSING-FLAG"

RUNNER_ROOT_FOLDER = os.getenv("ROOT_FOLDER_PATH")
RUNNER_USEFUL_CODES_PREFIX_PATH = f"{RUNNER_ROOT_FOLDER}/src/useful-codes/"

# --- Functions ---


def gdrive_execute(gdrive_command, *args):
    subprocess.run(
        [
            "python",
            f"{RUNNER_ROOT_FOLDER}/src/runner_gdrive.py",
            gdrive_command,
        ]
        + list(args),
        check=True,
        shell=True,
    )
    sys.exit(0)


def print_content(content_filename):
    subprocess.run(
        [
            "python",
            f"{RUNNER_ROOT_FOLDER}/src/runner_print_content.py",
            content_filename,
        ],
        check=True,
        shell=True,
    )
    sys.exit(0)


def open_vscode_extensions_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Browser-Extensions"], shell=True)
    sys.exit(0)


def warn_user_error(warning_message: str):
    global RUNNER_STATUS
    print(">>> Warn: " + warning_message)
    sys.exit(0)


def open_testing_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Testing"], shell=True)
    sys.exit(0)


def print_runner_files_root_dir():
    print(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(0)


def print_useful_commands():
    print_content("list-useful-commands.txt")


def run_git_command(git_type, user_message=None):
    args = [
        "python",
        f"{RUNNER_ROOT_FOLDER}/src/runner_git.py",
        git_type,
    ]
    if user_message:
        args.append(user_message)
    subprocess.run(
        args,
        check=True,
    )
    sys.exit(0)


def open_runner_file_in_system_folder():
    subprocess.run(["start", f"{RUNNER_ROOT_FOLDER}"], shell=True)
    sys.exit(0)


def print_statuses_info():
    subprocess.run(
        ["python", f"{RUNNER_ROOT_FOLDER}/src/runner_statuses.py"],
        check=True,
        shell=True,
    )
    sys.exit(0)


def print_help():
    print_content("help.txt")


def print_cURL():
    subprocess.run(
        ["python", f"{RUNNER_ROOT_FOLDER}/src/runner_cURL.py"],
        check=True,
        shell=True,
    )
    sys.exit(0)


def open_environment_variables_panel():
    subprocess.run(["rundll32.exe", "sysdm.cpl,EditEnvironmentVariables"], shell=True)
    sys.exit(0)


def open_vscode_workspaces_in_system_folder():
    subprocess.run(["start", "D:/D-Documents/VSCode-Workspaces"], shell=True)
    sys.exit(0)


def open_working_vscode(ide_prefix: str, value: str, powershell_only=False):
    if not ide_prefix:
        raise Exception("IDE prefix is missing.")
    cmd_args = [
        "python",
        f"{RUNNER_ROOT_FOLDER}/src/runner_main_ws.py",
        ide_prefix,
    ]
    if value:
        cmd_args.append(value)
    if powershell_only:
        cmd_args.append("-p")
    subprocess.run(
        cmd_args,
        check=True,
        shell=True,
    )
    sys.exit(0)


def print_vscode_workspaces(workspace_path):
    subprocess.run(
        [
            "python",
            os.path.join(RUNNER_USEFUL_CODES_PREFIX_PATH, "print_runner_folder.py"),
            workspace_path,
        ],
        check=True,
    )
    sys.exit(0)


def open_runner_files_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, f"{RUNNER_ROOT_FOLDER}"], shell=True)
    sys.exit(0)


def open_template_nestjs_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Code_VCN/nestjs"], shell=True)
    sys.exit(0)


def run_test_bat(*args):
    subprocess.run(
        ["python", r"{RUNNER_ROO}src/runner_test.py"] + list(args),
        check=True,
        shell=True,
    )
    sys.exit(0)


def print_os_info():
    subprocess.run(["python", "src/runner_os_info.py"], check=True, shell=True)
    sys.exit(0)


def run_Unikey_app():
    subprocess.run(["start", "C:/Users/dell/Downloads/UniKeyNT.exe"], shell=True)
    sys.exit(0)


def open_typescript_template_in_cursor(ide_prefix):
    subprocess.run(
        [ide_prefix, "D:/D-Documents/Templates/standard-express-server-ts"], shell=True
    )
    sys.exit(0)


def open_testing_javascript_typescript_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Testing/js-ts"], shell=True)
    sys.exit(0)


def open_testing_python_folder_in_vscode(ide_prefix):
    subprocess.run([ide_prefix, "D:/D-Documents/Testing/py"], shell=True)
    sys.exit(0)


# --- Main ---

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="runner (Python version) - Command line tool for automating tasks."
        )
        parser.add_argument(
            "type", nargs="?", default=None, help="Type (open, code, run, print, git)"
        )
        parser.add_argument(
            "action",
            nargs="?",
            default=None,
            help="Action (e.g. env, ws, test, commit, os, stts, curl, dir, test-bat, unikey)",
        )
        parser.add_argument(
            "value",
            nargs="?",
            default=None,
            help="Value (e.g. <remote-name> for gdrive set-remote)",
        )
        parser.add_argument(
            "-m",
            "--message",
            default=None,
            dest="user_message",
            help="User message (for git commit)",
        )
        parser.add_argument(
            "-c",
            "--cursor",
            default=None,
            dest="cursor_IDE",
            action="store_true",
            help="Open codes in Cursor IDE",
        )
        parser.add_argument(
            "-p",
            "--powershell-only",
            default=None,
            dest="powershell_only",
            action="store_true",
            help="Only open folders in Windows Terminal (skip IDE)",
        )
        args = parser.parse_args()

        type_included = args.type
        action_included = args.action
        value_included = args.value
        user_message_included = args.user_message

        # for coding
        cursor_IDE_included = args.cursor_IDE
        powershell_only_included = args.powershell_only
        default_ide_prefix: str = "cs" if cursor_IDE_included else "anti"

        if type_included == None:
            if action_included == None:
                print_help()
            else:
                raise Exception(RUNNER_WARNING_TYPE_MISSING)
        elif type_included == RUNNER_GDRIVE:
            gdrive_execute(action_included, value_included)
        elif type_included == RUNNER_TYPE_CODE:
            if action_included == None:
                open_runner_files_in_vscode(default_ide_prefix)
            elif action_included == RUNNER_CODE_VSCODE_WORKSPACE:
                open_working_vscode(
                    default_ide_prefix,
                    value_included,
                    powershell_only_included,
                )
            elif action_included == RUNNER_CODE_TEST:
                open_testing_folder_in_vscode(default_ide_prefix)
            elif action_included == RUNNER_CODE_TYPESCRIPT_TEMPLATE:
                open_typescript_template_in_cursor(default_ide_prefix)
            elif action_included == RUNNER_CODE_JS or action_included == RUNNER_CODE_TS:
                open_testing_javascript_typescript_folder_in_vscode(default_ide_prefix)
            elif action_included == RUNNER_CODE_NESTJS:
                open_template_nestjs_folder_in_vscode(default_ide_prefix)
            elif action_included == RUNNER_CODE_PY:
                open_testing_python_folder_in_vscode(default_ide_prefix)
            elif action_included == RUNNER_CODE_EXTENSIONS:
                open_vscode_extensions_in_vscode(default_ide_prefix)
            else:
                raise Exception(RUNNER_WARNING_ACTION_WRONG)
        elif type_included == RUNNER_TYPE_GIT:
            if action_included == RUNNER_GIT_COMMIT_AND_PUSH:
                if not user_message_included:
                    raise Exception("Missing commit message (use -m or --message)")
            if not action_included:
                raise Exception(RUNNER_WARNING_ACTION_MISSING)
            run_git_command(action_included, user_message_included)
        elif type_included == RUNNER_TYPE_RUN:
            if action_included == RUNNER_RUN_TEST_BAT:
                run_test_bat()
            elif action_included == RUNNER_RUN_UNIKEY_APP:
                run_Unikey_app()
            elif action_included == None:
                raise Exception(RUNNER_WARNING_ACTION_MISSING)
            else:
                raise Exception(RUNNER_WARNING_ACTION_WRONG)
        elif type_included == RUNNER_TYPE_OPEN:
            if action_included == None:
                open_runner_files_in_vscode(default_ide_prefix)
            elif action_included == RUNNER_OPEN_ENV:
                open_environment_variables_panel()
            elif action_included == RUNNER_CODE_VSCODE_WORKSPACE:
                open_vscode_workspaces_in_system_folder()
            else:
                raise Exception(RUNNER_WARNING_ACTION_WRONG)
        elif type_included == RUNNER_TYPE_PRINT:
            if action_included == RUNNER_PRINT_OS_INFO:
                print_os_info()
            elif action_included == RUNNER_PRINT_VSCODE_WORKSPACES:
                print_vscode_workspaces("D:/D-Documents/VSCode-Workspaces")
            elif action_included == RUNNER_PRINT_DIRECTORY:
                print_runner_files_root_dir()
            elif action_included == RUNNER_PRINT_USEFUL_COMMANDS:
                print_useful_commands()
            elif action_included == RUNNER_PRINT_CURL:
                print_cURL()
            elif action_included == RUNNER_PRINT_STATUSES_INFO:
                print_statuses_info()
            elif action_included == None:
                raise Exception(RUNNER_WARNING_ACTION_MISSING)
            else:
                raise Exception(RUNNER_WARNING_ACTION_WRONG)
        else:
            raise Exception(RUNNER_WARNING_TYPE_WRONG)

        # Nếu chạy đến đây (không rẽ nhánh nào) thì báo lỗi.
        RUNNER_STATUS = "OUT-OF-MAIN-SECTION"
        print(">>> These commands end up with runner-status: " + RUNNER_STATUS)
        sys.exit(1)
    except Exception as e:
        warn_user_error(str(e))
        sys.exit(1)
