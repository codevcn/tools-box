import sys
import subprocess
import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/runner/.env")

RUNNER_USEFUL_CODES_FOLDER_PATH = os.getenv("USEFUL_CODES_FOLDER_PATH")

GDRIVE_ACTION_SYNC = "sync"
GDRIVE_ACTION_GUIDE = "guide"
GDRIVE_ACTION_RESET = "reset"
GDRIVE_ACTION_LIST = "list"
GDRIVE_ACTION_REMOTE = "remote"
GDRIVE_ACTION_DEL_FD = "del-fd"
GDRIVE_ACTION_URL = "url"

# Tên tệp cấu hình JSON sẽ lưu trữ thông tin remote
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs.json")


def load_remote_name():
    """Đọc tên remote từ tệp JSON. Trả về None nếu tệp không tồn tại."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("remote_name")
        except (json.JSONDecodeError, KeyError):
            return None
    return None


def save_remote_name(remote_name):
    """Lưu tên remote vào tệp JSON để sử dụng cho lần sau."""
    # Đảm bảo tên remote có dấu hai chấm ở cuối nếu người dùng quên nhập
    if not remote_name.endswith(":"):
        remote_name += ":"

    data = {"remote_name": remote_name}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f"Đã lưu cấu hình remote '{remote_name}' vào tệp {CONFIG_FILE}.")


def check_remote_exists(remote_name):
    """Kiểm tra xem tên remote có thực sự tồn tại trong hệ thống rclone hay không."""
    try:
        result = subprocess.run(
            ["rclone", "listremotes"],
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return remote_name in result.stdout
    except subprocess.CalledProcessError:
        return False


def run_setup_flow():
    """Luồng thiết lập lần đầu: Chạy rclone config và lưu tên vào JSON."""
    print("-" * 50)
    print("# Hệ thống chưa được cấu hình remote Google Drive.")
    print("  1. Sau đây, giao diện cấu hình của rclone sẽ hiện ra.")
    print(
        "  2. Bạn hãy chọn 'n' để tạo mới và làm theo hướng dẫn cấp quyền truy cập Google Drive cho rclone."
    )
    print(
        "# Chỉ cần làm bước này lần đầu tiên, những lần sau hệ thống sẽ tự động sử dụng cấu hình đã lưu."
    )
    print("# Tùy chọn:")
    print("  - Chạy lệnh 'runner gdrive guide' để xem hướng dẫn cấp quyền truy cập")
    print("-" * 50)

    try:
        try:
            result_before = subprocess.run(
                ["rclone", "listremotes"],
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                check=True,
            )
            remotes_before = set(
                [
                    r.strip()
                    for r in result_before.stdout.strip().split("\n")
                    if r.strip()
                ]
            )
        except subprocess.CalledProcessError:
            remotes_before = set()

        subprocess.run(["rclone", "config"], check=True)

        try:
            result_after = subprocess.run(
                ["rclone", "listremotes"],
                stdout=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                check=True,
            )
            remotes_after = set(
                [
                    r.strip()
                    for r in result_after.stdout.strip().split("\n")
                    if r.strip()
                ]
            )
        except subprocess.CalledProcessError:
            remotes_after = set()

        print("\n" + "=" * 50)

        new_remotes = remotes_after - remotes_before

        if len(new_remotes) == 1:
            new_name = list(new_remotes)[0].rstrip(":")
            print(f"Đã tự động nhận diện remote mới tạo: {new_name}")
            save_remote_name(new_name)
            return load_remote_name()
        elif len(new_remotes) > 1:
            new_name = list(new_remotes)[0].rstrip(":")
            print(f"Đã tự động nhận diện remote mới tạo: {new_name}")
            save_remote_name(new_name)
            return load_remote_name()
        elif len(remotes_after) == 1:
            new_name = list(remotes_after)[0].rstrip(":")
            print(f"Hệ thống nhận thấy có sẵn 1 remote: {new_name}")
            save_remote_name(new_name)
            return load_remote_name()
        elif len(remotes_after) > 1:
            print("Hệ thống phát hiện nhiều remote. Hãy chọn một remote để sử dụng:")
            remotes_list = list(remotes_after)
            for idx, r in enumerate(remotes_list):
                print(f"[{idx + 1}] {r.rstrip(':')}")

            while True:
                choice = input("Nhập số thứ tự: ").strip()
                try:
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(remotes_list):
                        new_name = remotes_list[choice_idx].rstrip(":")
                        save_remote_name(new_name)
                        return load_remote_name()
                except ValueError:
                    pass
                print("Lựa chọn không hợp lệ, vui lòng thử lại.")
        else:
            print("Lỗi: Bạn chưa thiết lập thành công remote nào trong rclone!")
            sys.exit(1)

    except subprocess.CalledProcessError:
        print("Đã xảy ra lỗi trong quá trình cấu hình rclone.")
        sys.exit(1)


def sync_to_gdrive(source_path, dest_path, remote_name):
    """Thực hiện lệnh đồng bộ dữ liệu."""
    if not os.path.exists(source_path):
        print(f"Lỗi: Thư mục nguồn '{source_path}' không tồn tại.")
        sys.exit(1)

    # Đảm bảo đường dẫn đích bắt đầu bằng tên remote từ JSON và đóng vai trò là absolute path trên root
    if not dest_path.startswith(remote_name):
        _dest = dest_path
        if _dest and not _dest.startswith("/"):
            _dest = "/" + _dest
        remote_dest = f"{remote_name}{_dest}"
    else:
        remote_dest = dest_path

    print(f"Bắt đầu đồng bộ dữ liệu lên Google Drive...")
    print(f"  Remote sử dụng: {remote_name}")
    print(f"  Nguồn: {os.path.abspath(source_path)}")
    print(f"  Đích: {remote_dest}")
    print("-" * 50)

    command = ["rclone", "sync", source_path, remote_dest, "--progress"]

    try:
        subprocess.run(command, check=True)
        print("-" * 50)
        print("Đồng bộ hoàn tất thành công!")

        # Bổ sung tính năng lấy link Web cho folder đích sau khi sync
        try:
            print("Đang tạo/lấy URL thư mục đích...")
            link_result = subprocess.run(
                ["rclone", "link", remote_dest],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                check=True,
            )
            folder_link = link_result.stdout.strip()
            print(f"URL truy cập: {folder_link}")
            print("-" * 50)
        except subprocess.CalledProcessError as e:
            print(
                f"Không thể tạo URL thư mục đích (Lỗi do remote hoặc cấp quyền). Chi tiết: {e.stderr.strip()}"
            )

    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi thực thi rclone: {e}")


def list_directories(target_path, remote_name, is_deep=False, is_file=False):
    """Lấy danh sách các thư mục hoặc tệp từ Google Drive."""
    # Loại bỏ dấu ngoặc kép bọc quanh nếu chạy qua shell làm tham số chuỗi trống bị bọc
    if target_path in ['""', "''"]:
        target_path = ""

    clean_target_path = target_path.strip("/")

    if target_path and not target_path.startswith("/"):
        target_path = "/" + target_path

    remote_dest = f"{remote_name}{target_path}"

    item_type = "tệp tin" if is_file else "thư mục"
    mode_flag = "--files-only" if is_file else "--dirs-only"

    if is_deep:
        print(f'Đang lấy danh sách {item_type} đệ quy (deep) từ "{remote_dest}"')
        command = ["rclone", "lsf", remote_dest, mode_flag, "-R"]
    else:
        print(f'Đang lấy danh sách {item_type} trực tiếp từ "{remote_dest}"')
        command = ["rclone", "lsf", remote_dest, mode_flag]

    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, text=True, encoding="utf-8", check=True
        )
        print("-" * 50)
        output = result.stdout.strip()
        if output:
            if is_deep:
                for line in output.split("\n"):
                    if not is_file:
                        line = line.strip().rstrip("/")
                    else:
                        line = line.strip()

                    if not line:
                        continue

                    if clean_target_path:
                        print(f"{clean_target_path}/{line}")
                    else:
                        print(line)
            else:
                print(output)
        else:
            print(f"(Không có {item_type} nào)")
        print("-" * 50)
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi thực thi rclone lấy danh sách: {e}")


def display_auth_guide():
    subprocess.Popen(
        ["notepad", f"{RUNNER_USEFUL_CODES_FOLDER_PATH}/sync-to-gdrive/AUTH_GUIDE.txt"],
        shell=True,
    )
    sys.exit(0)


def reset_config():
    print("Đang tiến hành làm mới cấu hình rclone...")

    try:
        result = subprocess.run(
            ["rclone", "listremotes"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            check=True,
        )
        remotes = [
            r.strip().rstrip(":")
            for r in result.stdout.strip().split("\n")
            if r.strip()
        ]
    except subprocess.CalledProcessError:
        remotes = []

    print("\nChọn 1 remote để xóa:")
    if remotes:
        for r in remotes:
            print(f"- {r}")
    else:
        print("(Không có remote nào được tìm thấy)")

    choice = input("\nNhập tên remote để xóa (để trống để xóa toàn bộ): ").strip()

    if choice:
        remote_to_delete = choice.rstrip(":")
        try:
            subprocess.run(["rclone", "config", "delete", remote_to_delete], check=True)
            print(f"Đã xóa cấu hình của remote: {remote_to_delete}")

            current_local = load_remote_name()
            if current_local and current_local.replace(":", "") == remote_to_delete:
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
                    print(
                        f"Đã xóa kèm file configs.json nội bộ do trùng với remote vừa xóa."
                    )
        except subprocess.CalledProcessError:
            print(
                f"Lỗi: Không tìm thấy hoặc không thể xóa remote '{remote_to_delete}'."
            )
    else:
        confirm = (
            input(
                "Cảnh báo: Chuẩn bị xóa toàn bộ nội dung trong file cấu hình rclone, bạn có chắc muốn xóa chứ? Nhập 'y' để xóa, nhập 'n' để bỏ qua: "
            )
            .strip()
            .lower()
        )
        if confirm == "y":
            try:
                result = subprocess.run(
                    ["rclone", "config", "file"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    check=True,
                )
                output = result.stdout

                lines = output.strip().split("\n")
                config_path = None
                for i, line in enumerate(lines):
                    if "Configuration file is stored at:" in line:
                        if i + 1 < len(lines):
                            config_path = lines[i + 1].strip()
                        break

                if config_path and os.path.exists(config_path):
                    os.remove(config_path)
                    print(f"Đã xóa file cấu hình rclone tại: {config_path}")
                else:
                    print(
                        "Không tìm thấy file cấu hình rclone hoặc nó đã bị xóa từ trước."
                    )

            except subprocess.CalledProcessError as e:
                print(f"Lỗi khi chạy lệnh rclone config file: {e}")
            except Exception as e:
                print(f"Lỗi khi xóa file cấu hình rclone: {e}")

            if os.path.exists(CONFIG_FILE):
                try:
                    os.remove(CONFIG_FILE)
                    print(f"Đã xóa file cấu hình nội bộ tại: {CONFIG_FILE}")
                except Exception as e:
                    print(f"Lỗi khi xóa {CONFIG_FILE}: {e}")

            print("Quá trình reset toàn bộ hoàn tất!")
        else:
            print("Đã bỏ qua xóa toàn bộ file cấu hình.")

    sys.exit(0)


def show_remote_info(remote_name):
    print(f"--- Thông tin cấu hình và dung lượng của remote: {remote_name} ---")

    clean_remote = remote_name.rstrip(":")

    try:
        about_result = subprocess.run(
            ["rclone", "about", remote_name],
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            check=True,
        )
        print(">> Thông tin dung lượng:")
        print(about_result.stdout.strip())
        print("-" * 50)
    except subprocess.CalledProcessError:
        print(
            ">> Không thể lấy thông tin dung lượng (có thể remote không hỗ trợ tính năng này)."
        )
        print("-" * 50)

    try:
        config_result = subprocess.run(
            ["rclone", "config", "show", clean_remote],
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            check=True,
        )
        print(">> Cấu hình thực tế trên rclone:")
        for line in config_result.stdout.strip().split("\n"):
            if line.strip().startswith("token ="):
                print("token = ***_HIDDEN_***")
            elif line.strip().startswith("client_secret ="):
                print("client_secret = ***_HIDDEN_***")
            else:
                print(line)
    except subprocess.CalledProcessError as e:
        print(f">> Cảnh báo không lấy được cấu hình chi tiết: {e}")


def delete_folder_on_remote(target_path, remote_name):
    if target_path in ['""', "''"]:
        target_path = ""

    target_path = target_path.strip()

    if not target_path or target_path == "/":
        print("Lỗi: Đường dẫn rỗng hoặc là thư mục gốc (root), xin đừng làm vậy!")
        return

    if not target_path.startswith("/"):
        target_path = "/" + target_path

    remote_dest = f"{remote_name}{target_path}"

    print(f"Đang tiến hành xóa: {remote_dest} ...")
    try:
        subprocess.run(["rclone", "purge", remote_dest], check=True)
        print(
            f"Đã xóa thành công toàn bộ thư mục '{target_path.strip('/')}' trên remote!"
        )
    except subprocess.CalledProcessError as e:
        print(f"Đã xảy ra lỗi trong quá trình xóa thư mục: {e}")


def get_url_from_remote(target_path, remote_name):
    if target_path in ['""', "''"]:
        target_path = ""

    target_path = target_path.strip()

    if target_path and not target_path.startswith("/"):
        target_path = "/" + target_path

    remote_dest = f"{remote_name}{target_path}"

    print(f"Đang lấy URL truy cập cho: {remote_dest} ...")
    try:
        link_result = subprocess.run(
            ["rclone", "link", remote_dest],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            check=True,
        )
        folder_link = link_result.stdout.strip()
        print(f"URL: {folder_link}")
    except subprocess.CalledProcessError as e:
        print(f"Lỗi khi lấy URL: {e.stderr.strip()}")


def switch_actions():
    action = sys.argv[1] if len(sys.argv) > 1 else None

    if action == GDRIVE_ACTION_GUIDE:
        display_auth_guide()
    elif action == GDRIVE_ACTION_RESET:
        reset_config()
    elif action == GDRIVE_ACTION_REMOTE:
        rclone_remote = load_remote_name()
        if not rclone_remote or not check_remote_exists(rclone_remote):
            rclone_remote = run_setup_flow()
        show_remote_info(rclone_remote)
    elif action == GDRIVE_ACTION_DEL_FD:
        target_path = sys.argv[2] if len(sys.argv) > 2 else ""
        if not target_path:
            print("Cú pháp: runner gdrive del-fd <tên_thư_mục_trên_remote>")
            sys.exit(1)

        rclone_remote = load_remote_name()
        if not rclone_remote or not check_remote_exists(rclone_remote):
            rclone_remote = run_setup_flow()

        # Hỏi xác nhận
        confirm = input(
            f'Có chắc muốn xóa thư mục "{target_path}" ko? nhập y để xóa, nhập n để hủy: '
        ).strip()
        if confirm == "y":
            delete_folder_on_remote(target_path, rclone_remote)
        else:
            print("Đã hủy bỏ thao tác xóa.")
    elif action == GDRIVE_ACTION_URL:
        target_path = sys.argv[2] if len(sys.argv) > 2 else ""
        if not target_path:
            print("Cú pháp: runner gdrive url <đường_dẫn_trên_remote>")
            sys.exit(1)

        rclone_remote = load_remote_name()
        if not rclone_remote or not check_remote_exists(rclone_remote):
            rclone_remote = run_setup_flow()

        get_url_from_remote(target_path, rclone_remote)
    elif action == GDRIVE_ACTION_LIST:
        args_list = sys.argv[2:]
        is_deep = False
        is_file = False
        if "-d" in args_list:
            is_deep = True
            args_list.remove("-d")
        if "--deep" in args_list:
            is_deep = True
            args_list.remove("--deep")
        if "--file" in args_list:
            is_file = True
            args_list.remove("--file")

        target_path = args_list[0] if len(args_list) > 0 else ""

        rclone_remote = load_remote_name()
        if not rclone_remote or not check_remote_exists(rclone_remote):
            rclone_remote = run_setup_flow()

        list_directories(target_path, rclone_remote, is_deep, is_file)
    elif action == GDRIVE_ACTION_SYNC:
        if len(sys.argv) < 4:
            print(
                'Cú pháp: py sync_to_gdrive.py sync "<folder nguồn>" "<path đích trên gdrive>"'
            )
            sys.exit(1)

        source_dir = sys.argv[2]
        dest_dir = sys.argv[3]

        # Bước 1: Lấy tên remote từ tệp JSON
        rclone_remote = load_remote_name()

        # Bước 2: Nếu chưa có JSON hoặc remote không tồn tại, yêu cầu thiết lập
        if not rclone_remote or not check_remote_exists(rclone_remote):
            rclone_remote = run_setup_flow()

        # Bước 3: Tiến hành đồng bộ
        sync_to_gdrive(source_dir, dest_dir, rclone_remote)
    else:
        print(f"Lỗi: Không tìm thấy hành động '{action}'.")
        sys.exit(1)


if __name__ == "__main__":
    print("Kiểm tra các tham số đầu vào...")

    if len(sys.argv) < 2:
        print("Cú pháp: py sync_to_gdrive.py <action> ...")
        sys.exit(1)

    try:
        switch_actions()
    except KeyboardInterrupt:
        print("\n\nTiến trình đồng bộ Google Drive đã bị ngắt (KeyboardInterrupt).")
        sys.exit(0)
