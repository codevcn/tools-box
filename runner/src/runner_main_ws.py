import subprocess
import time
import argparse


def open_working_workspace_photobooth(ide_prefix, powershell_only=False) -> None:
    folders: list[str] = [
        "D:/D-Documents/Code_VCN/Photobooth/code/ptm",
        "D:/D-Documents/Code_VCN/Photobooth/recover-image",
    ]

    # Nếu dùng flag -p, chỉ mở 3 thư mục chính trong terminal
    if powershell_only:
        cmd = f'wt -w _blank -d "{folders[0]}" --title "PTM"'
        cmd += f' ; nt -d "{folders[1]}" --title "recover-image"'
        subprocess.run(cmd, shell=True)
        return

    folders_for_CLI: list[str] = [
        folders[0],
        folders[1],
    ]
    folders_for_ide: list[str] = [
        folders[0],
        folders[1],
    ]

    # Mở các tab trong Windows Terminal
    limit = 99
    cmd = "wt -w 0 " + " ; ".join(
        [
            (
                f'nt -d "{folder}" --title "{folder.split("/")[-1]}" '
                f'cmd {"/k dev" if current_index <= limit else ""}'
            )
            for current_index, folder in enumerate(folders_for_CLI)
        ]
    )
    subprocess.run(cmd, shell=True)

    # Mở các thư mục trong IDE
    for folder in folders_for_ide:
        subprocess.run([ide_prefix, folder], shell=True)
        time.sleep(2)  # Đợi 2 giây giữa các lần mở

    time.sleep(4)  # Đợi 4 giây sau khi mở IDE

    destinations_for_browser: list[list[str]] = [
        ["Profile 2", "http://localhost:3000"],
        ["Profile 23", "https://chatgpt.com", "https://gemini.google.com/app"],
    ]

    chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    for profile in destinations_for_browser:
        profile_name = profile[0]
        for url in profile[1:]:
            subprocess.Popen([chrome_path, f"--profile-directory={profile_name}", url])
            time.sleep(1)  # Đợi 1 giây giữa các lần mở


def open_working_workspace_rclone_tool(ide_prefix, powershell_only=False) -> None:
    folders: list[str] = [
        "D:/D-Documents/TOOLs/gdrive-tool/sync-with-gdrive",
    ]

    # Nếu dùng flag -p, chỉ mở 3 thư mục chính trong terminal
    if powershell_only:
        cmd = f'wt -w _blank -d "{folders[0]}" --title "gdrive-tool"'
        subprocess.run(cmd, shell=True)
        return

    folders_for_CLI: list[str] = [
        folders[0],
    ]
    folders_for_ide: list[str] = [
        folders[0],
    ]

    # Mở các tab trong Windows Terminal
    limit = 99
    cmd = "wt -w 0 " + " ; ".join(
        [
            (
                f'nt -d "{folder}" --title "{folder.split("/")[-1]}" '
                f'cmd {"/k test" if current_index <= limit else ""}'
            )
            for current_index, folder in enumerate(folders_for_CLI)
        ]
    )
    subprocess.run(cmd, shell=True)

    # Mở các thư mục trong IDE
    for folder in folders_for_ide:
        subprocess.run([ide_prefix, folder], shell=True)
        time.sleep(2)  # Đợi 2 giây giữa các lần mở

    destinations_for_browser: list[list[str]] = [
        ["Profile 23", "https://chatgpt.com", "https://gemini.google.com/app"],
    ]

    chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
    for profile in destinations_for_browser:
        profile_name = profile[0]
        for url in profile[1:]:
            subprocess.Popen([chrome_path, f"--profile-directory={profile_name}", url])
            time.sleep(1)  # Đợi 1 giây giữa các lần mở


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Open PTM project & recover-image server"
    )
    parser.add_argument(
        "ide_prefix", nargs="?", default="anti", help="IDE prefix (code or cs)"
    )
    parser.add_argument(
        "value", nargs="?", default="photobooth", help="Works that you want to work on"
    )
    parser.add_argument(
        "-p",
        "--powershell-only",
        dest="powershell_only",
        action="store_true",
        help="Only open folders in Windows Terminal (skip IDE)",
    )
    args = parser.parse_args()

    value = args.value.lower()
    if value == "ptb":
        open_working_workspace_photobooth(
            args.ide_prefix, powershell_only=args.powershell_only
        )
    elif value == "tool":
        open_working_workspace_rclone_tool(
            args.ide_prefix, powershell_only=args.powershell_only
        )
