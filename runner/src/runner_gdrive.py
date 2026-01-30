import subprocess
from pathlib import Path
import sys


def get_config_file_path() -> Path:
    """Lấy đường dẫn đến file config."""
    return Path(__file__).parent / "configs" / "gdrive" / "gdrive.config.txt"


def get_config_value(key: str, config_file: Path | None = None) -> str:
    """
    Trích xuất value từ key trong file config.

    Format file config:
    - Comment lines bắt đầu bằng #
    - Key-value format: key = "value" hoặc key = value

    Args:
        key: Tên key cần tìm
        config_file: Đường dẫn đến file config (mặc định: configs/gdrive/gdrive.config.txt)

    Returns:
        Value tương ứng với key (đã loại bỏ dấu ngoặc kép nếu có)

    Raises:
        RuntimeError: Nếu không tìm thấy key hoặc file không tồn tại
    """
    if config_file is None:
        config_file = get_config_file_path()

    if not config_file.exists():
        raise RuntimeError(f"Config file not found: {config_file}")

    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Bỏ qua comment và dòng trống
            if not line or line.startswith("#"):
                continue

            # Parse key = value
            if "=" in line:
                parts = line.split("=", 1)
                config_key = parts[0].strip()
                config_value = parts[1].strip()

                if config_key == key:
                    # Loại bỏ dấu ngoặc kép nếu có
                    if config_value.startswith('"') and config_value.endswith('"'):
                        config_value = config_value[1:-1]
                    return config_value

    raise RuntimeError(f"Key '{key}' not found in config file: {config_file}")


def set_config_value(key: str, value: str, config_file: Path | None = None) -> None:
    """
    Cập nhật giá trị của key trong file config.

    Args:
        key: Tên key cần cập nhật
        value: Giá trị mới (sẽ tự động wrap trong dấu ngoặc kép)
        config_file: Đường dẫn đến file config

    Raises:
        RuntimeError: Nếu không tìm thấy key hoặc file không tồn tại
    """
    if config_file is None:
        config_file = get_config_file_path()

    if not config_file.exists():
        raise RuntimeError(f"Config file not found: {config_file}")

    lines = []
    key_found = False

    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()

            # Giữ nguyên comment và dòng trống
            if not stripped or stripped.startswith("#"):
                lines.append(line)
                continue

            # Parse key = value
            if "=" in stripped:
                parts = stripped.split("=", 1)
                config_key = parts[0].strip()

                if config_key == key:
                    # Cập nhật value mới
                    lines.append(f'{config_key} = "{value}"\n')
                    key_found = True
                else:
                    lines.append(line)
            else:
                lines.append(line)

    if not key_found:
        raise RuntimeError(f"Key '{key}' not found in config file: {config_file}")

    # Ghi lại file
    with open(config_file, "w", encoding="utf-8") as f:
        f.writelines(lines)


# (2) Đọc thư mục gốc từ file config
rclone_active_remote = get_config_value("rclone_active_remote", None)
gdrive_base_dir = get_config_value("folder_path_from_root", None)


def gdrive_push(local_dir: Path) -> None:
    """
    Sync toàn bộ folder local_dir lên:
      {rclone_active_remote}:/{gdrive_base_dir}/{local_dir.name}
    => nghĩa là: cd vào thư mục A, tool sẽ sync A lên Drive vào folder cùng tên "A"
    """
    if not local_dir.exists() or not local_dir.is_dir():
        raise RuntimeError(f"Local dir is invalid: {local_dir}")

    # Folder A trên máy (tên folder hiện tại)
    folder_name = local_dir.name

    # Target Drive folder: gdrive:/RunnerSynced/A
    remote_target = f"{rclone_active_remote}:/{gdrive_base_dir}/{folder_name}"

    print("===== RUNNER GDRIVE PUSH =====")
    print(f"Local : {str(local_dir)}")
    print(f"Remote: {remote_target}")
    print("--------------------------")

    # Lệnh sync:
    # - sync: Drive mirror theo local (xóa file trên Drive nếu local xóa)
    # - Nếu bạn muốn chỉ upload/update mà KHÔNG xóa trên Drive -> dùng "copy" thay vì "sync"
    cmd = [
        "rclone",
        "sync",  # <-- đổi thành "copy" nếu bạn không muốn xóa file trên Drive
        str(local_dir),
        remote_target,
        "--progress",
        "--create-empty-src-dirs",
        "--exclude",
        ".git/**",  # bỏ git
        "--exclude",
        "node_modules/**",  # bỏ node_modules (nếu có)
        "--exclude",
        ".DS_Store",
    ]

    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        raise RuntimeError(
            "Không tìm thấy rclone. Hãy cài rclone và đảm bảo nó nằm trong PATH."
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"rclone failed with exit code {e.returncode}")

    print("✅ Done.")


def gdrive_list_remotes() -> None:
    """
    Liệt kê các remote rclone có sẵn và hiển thị remote đang active.

    Lấy từ file config:
      - rclone_remotes: danh sách remote, phân tách bằng dấu phẩy
      - rclone_active_remote: remote đang dùng
    """
    try:
        remotes_str = get_config_value("rclone_remotes")
        active_remote = get_config_value("rclone_active_remote")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Parse danh sách remotes từ config
    remotes = [r.strip() for r in remotes_str.split(",") if r.strip()]

    if not remotes:
        print("❌ Không có remote nào trong config key 'rclone_remotes'.")
        print("👉 Hãy cập nhật configs/gdrive/gdrive.config.txt, ví dụ:")
        print('   rclone_remotes = "gdrive_personal,gdrive_work"')
        sys.exit(1)

    print("===== RUNNER GDRIVE REMOTES =====")

    # Nếu active_remote không nằm trong danh sách, vẫn hiển thị nhưng cảnh báo
    if active_remote not in remotes:
        print(
            f"⚠️  Active remote '{active_remote}' KHÔNG nằm trong danh sách rclone_remotes."
        )
        print(f"    Available: {', '.join(remotes)}")
        print("    Bạn có thể sửa config hoặc chạy: runner gdrive set-remote <name>")
        print("----------------------------")
        print("Available remotes:")
    else:
        print(f"Active remote: {active_remote}")
        print("----------------------------")
        print("Available remotes:")

    for r in remotes:
        prefix = "* " if r == active_remote else "  "
        print(f"{prefix}{r}")


def gdrive_set_active_remote(remote_name: str) -> None:
    """
    Thiết lập remote rclone đang hoạt động.

    Args:
        remote_name: Tên remote cần thiết lập

    Raises:
        RuntimeError: Nếu remote không có trong danh sách
    """
    remotes_str = get_config_value("rclone_remotes")
    remotes = [r.strip() for r in remotes_str.split(",")]

    if remote_name not in remotes:
        print(f"❌ Remote '{remote_name}' không có trong danh sách.")
        print(f"⚙️ Available remotes: {', '.join(remotes)}")
        sys.exit(1)

    # Cập nhật config
    print("===== RUNNER GDRIVE SET ACTIVE REMOTE =====")
    set_config_value("rclone_active_remote", remote_name)
    print(f"✅ Đã thiết lập active remote: {remote_name}")


def gdrive_add_remote(remote_name: str) -> None:
    """
    Thêm một remote rclone mới vào danh sách rclone_remotes trong config.

    Args:
        remote_name: Tên remote cần thêm

    Behavior:
        - Nếu remote đã tồn tại: báo và thoát lỗi.
        - Nếu active_remote hiện tại không hợp lệ (không nằm trong list): có thể set active = remote mới.
          (Để tránh trạng thái active bị sai)
    """
    remote_name = remote_name.strip()
    if not remote_name:
        print("❌ Remote name is empty.")
        sys.exit(1)

    try:
        remotes_str = get_config_value("rclone_remotes")
        active_remote = get_config_value("rclone_active_remote")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    remotes = [r.strip() for r in remotes_str.split(",") if r.strip()]

    if remote_name in remotes:
        print("===== RUNNER GDRIVE ADD REMOTE =====")
        print(f"❌ Remote '{remote_name}' đã tồn tại.")
        print(f"⚙️ Available remotes: {', '.join(remotes)}")
        sys.exit(1)

    remotes.append(remote_name)

    # Ghi lại danh sách remotes
    new_remotes_str = ",".join(remotes)

    print("===== RUNNER GDRIVE ADD REMOTE =====")
    set_config_value("rclone_remotes", new_remotes_str)
    print(f"✅ Đã thêm remote: {remote_name}")
    print(f"⚙️ Available remotes: {', '.join(remotes)}")

    # Nếu active_remote không hợp lệ, tự set sang remote mới để tránh config trạng thái "broken"
    if active_remote not in remotes:
        set_config_value("rclone_active_remote", remote_name)
        print(
            f"ℹ️ Active remote trước đó không hợp lệ -> set active remote = {remote_name}"
        )


def gdrive_remove_remote(remote_name: str) -> None:
    """
    Xóa một remote rclone khỏi danh sách rclone_remotes trong config.

    Args:
        remote_name: Tên remote cần xóa

    Safety:
        - Không cho xóa remote đang active. Bạn phải set active sang remote khác trước.
        - Không cho xóa nếu remote không tồn tại.
    """
    remote_name = remote_name.strip()
    if not remote_name:
        print("❌ Remote name is empty.")
        sys.exit(1)

    try:
        remotes_str = get_config_value("rclone_remotes")
        active_remote = get_config_value("rclone_active_remote")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)

    remotes = [r.strip() for r in remotes_str.split(",") if r.strip()]

    print("===== RUNNER GDRIVE REMOVE REMOTE =====")

    if remote_name not in remotes:
        print(f"❌ Remote '{remote_name}' không có trong danh sách.")
        print(f"⚙️ Available remotes: {', '.join(remotes)}")
        sys.exit(1)

    if remote_name == active_remote:
        print(f"❌ Không thể xóa remote đang active: '{remote_name}'.")
        print("👉 Hãy đổi active remote trước:")
        print("   runner gdrive set-remote <another_remote>")
        sys.exit(1)

    remotes = [r for r in remotes if r != remote_name]

    if not remotes:
        print("❌ Không thể xóa remote cuối cùng. Danh sách remotes sẽ bị rỗng.")
        print("👉 Hãy add remote khác trước khi remove.")
        sys.exit(1)

    new_remotes_str = ",".join(remotes)
    set_config_value("rclone_remotes", new_remotes_str)

    print(f"✅ Đã xóa remote: {remote_name}")
    print(f"⚙️ Available remotes: {', '.join(remotes)}")


RUNNER_GDRIVE_TYPE_PUSH = "push"  # đồng bộ thư mục hiện tại lên GDrive
RUNNER_GDRIVE_TYPE_LIST_REMOTES = "remotes"  # liệt kê các remote rclone
RUNNER_GDRIVE_TYPE_SET_ACTIVE_REMOTE = "set-remote"  # thiết lập remote rclone đang dùng
RUNNER_GDRIVE_ADD_REMOTE = "add-remote"  # thêm remote rclone mới
RUNNER_GDRIVE_REMOVE_REMOTE = "remove-remote"  # xóa remote rclone

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(">>> No valid gdrive command found.")
        sys.exit(1)
    gdrive_type = sys.argv[1]

    if gdrive_type == RUNNER_GDRIVE_TYPE_PUSH:
        current_dir = Path.cwd()
        gdrive_push(current_dir)

    elif gdrive_type == RUNNER_GDRIVE_TYPE_LIST_REMOTES:
        gdrive_list_remotes()

    elif gdrive_type == RUNNER_GDRIVE_TYPE_SET_ACTIVE_REMOTE:
        if len(sys.argv) < 3:
            print("❌ Missing remote name.")
            print("⚠️ Usage: runner gdrive set-remote <remote_name>")
            sys.exit(1)
        remote_name = sys.argv[2].strip()
        gdrive_set_active_remote(remote_name)

    elif gdrive_type == RUNNER_GDRIVE_ADD_REMOTE:
        if len(sys.argv) < 3:
            print("❌ Missing remote name.")
            print("⚠️ Usage: runner gdrive add-remote <remote_name>")
            sys.exit(1)
        remote_name = sys.argv[2].strip()
        gdrive_add_remote(remote_name)

    elif gdrive_type == RUNNER_GDRIVE_REMOVE_REMOTE:
        if len(sys.argv) < 3:
            print("❌ Missing remote name.")
            print("⚠️ Usage: runner gdrive remove-remote <remote_name>")
            sys.exit(1)
        remote_name = sys.argv[2].strip()
        gdrive_remove_remote(remote_name)

    else:
        print(">>> No valid gdrive command found.")
