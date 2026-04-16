"""
setup_venv_in_project.py
========================
Chương trình thiết lập môi trường ảo (venv) chuẩn cho dự án Python trên Windows.
Chạy script này khi đang đứng ở thư mục gốc của dự án trong Windows Terminal.

Cách dùng:
    python setup_venv_in_project.py
    python setup_venv_in_project.py --path "D:/my-project"
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path


# ─────────────────────────────────────────────
#  Màu sắc terminal (ANSI)
# ─────────────────────────────────────────────
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    DIM = "\033[2m"


def enable_ansi_windows():
    """Bật hỗ trợ ANSI color trên Windows Terminal / cmd."""
    if sys.platform == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def info(msg: str):
    print(f"{C.CYAN}ℹ {C.RESET} {msg}")


def success(msg: str):
    print(f"{C.GREEN}✔ {C.RESET} {msg}")


def warn(msg: str):
    print(f"{C.YELLOW}⚠ {C.RESET} {msg}")


def error(msg: str):
    print(f"{C.RED}✖ {C.RESET} {msg}")


def step(title: str):
    print(f"\n{C.BOLD}{C.CYAN}── {title} {'─' * (50 - len(title))}{C.RESET}")


# ─────────────────────────────────────────────
#  Tiện ích
# ─────────────────────────────────────────────
def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Chạy lệnh và trả về kết quả; ném lỗi nếu thất bại."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result


def find_python() -> str:
    """Tìm đường dẫn Python đang dùng (ưu tiên python, sau đó python3)."""
    for candidate in ("python", "python3"):
        found = shutil.which(candidate)
        if found:
            return found
    raise RuntimeError("Không tìm thấy Python trong PATH. Hãy cài Python trước.")


def get_venv_python(venv_dir: Path) -> Path:
    """Trả về đường dẫn python.exe bên trong venv."""
    return venv_dir / "Scripts" / "python.exe"


def get_venv_pip(venv_dir: Path) -> Path:
    """Trả về đường dẫn pip.exe bên trong venv."""
    return venv_dir / "Scripts" / "pip.exe"


# ─────────────────────────────────────────────
#  Các bước setup
# ─────────────────────────────────────────────
def step_create_venv(project_dir: Path, venv_name: str, python_exe: str) -> Path:
    """Bước 1 - Tạo thư mục venv."""
    step("Bước 1: Tạo môi trường ảo (venv)")
    venv_dir = project_dir / venv_name

    if venv_dir.exists():
        warn(f"Thư mục '{venv_name}' đã tồn tại.")
        choice = input(f"  Bạn muốn xoá và tạo lại? [y/n]: ").strip().lower()
        if choice == "y":
            info(f"Đang xoá '{venv_dir}'...")
            shutil.rmtree(venv_dir)
        else:
            info("Giữ nguyên venv hiện tại, bỏ qua bước tạo mới.")
            return venv_dir

    info(f" Đang tạo venv tại: {venv_dir}")
    result = run([python_exe, "-m", "venv", str(venv_dir)], cwd=project_dir)
    if result.returncode != 0:
        error(f"Tạo venv thất bại:\n{result.stderr}")
        sys.exit(1)

    success(f"Đã tạo venv: {venv_name}/")
    return venv_dir


def step_upgrade_pip(venv_dir: Path):
    """Bước 2 – Nâng cấp pip, setuptools, wheel."""
    step("Bước 2: Nâng cấp pip / setuptools / wheel")
    python = get_venv_python(venv_dir)

    pkgs = ["pip", "setuptools", "wheel"]
    info(f"Đang nâng cấp: {', '.join(pkgs)}")
    result = run([str(python), "-m", "pip", "install", "--upgrade"] + pkgs)
    if result.returncode != 0:
        warn(f"Nâng cấp thất bại (không nghiêm trọng):\n{result.stderr}")
    else:
        # Lấy phiên bản pip mới
        ver_result = run([str(python), "-m", "pip", "--version"])
        success(f"pip đã sẵn sàng – {ver_result.stdout.strip()}")


def step_install_requirements(venv_dir: Path, project_dir: Path):
    """Bước 3 – Cài packages từ requirements.txt nếu có."""
    step("Bước 3: Cài đặt packages từ requirements.txt")
    req_file = project_dir / "requirements.txt"

    if not req_file.exists():
        warn("Không tìm thấy requirements.txt → bỏ qua bước cài packages.")
        _offer_create_requirements(project_dir)
        return

    python = get_venv_python(venv_dir)
    info(f"Tìm thấy: {req_file}")
    info("Đang cài đặt packages...")

    result = run(
        [str(python), "-m", "pip", "install", "-r", str(req_file)],
        cwd=project_dir,
    )
    if result.returncode != 0:
        error(f"Cài đặt thất bại:\n{result.stderr}")
        sys.exit(1)

    success("Đã cài đặt tất cả packages trong requirements.txt")

    # Hiện danh sách packages đã cài
    list_result = run([str(python), "-m", "pip", "list", "--format=columns"])
    if list_result.returncode == 0:
        print(f"\n{C.DIM}{list_result.stdout}{C.RESET}")


def _offer_create_requirements(project_dir: Path):
    """Hỏi người dùng có muốn tạo requirements.txt rỗng không."""
    choice = input("  Tạo file requirements.txt trống? [y/n]: ").strip().lower()
    if choice == "y":
        req_file = project_dir / "requirements.txt"
        req_file.write_text(
            "# Khai báo các thư viện cần thiết cho dự án\n"
            "# Ví dụ:\n"
            "# requests==2.31.0\n"
            "# python-dotenv==1.0.0\n",
            encoding="utf-8",
        )
        success(f"Đã tạo: {req_file}")


def step_create_dotenv(project_dir: Path):
    """Bước 4 – Tạo file .env mẫu nếu chưa có."""
    step("Bước 4: Kiểm tra file .env")
    env_file = project_dir / ".env"

    if env_file.exists():
        info(".env đã tồn tại → bỏ qua.")
        return

    choice = input("  Bạn có muốn tạo file .env mẫu không? [y/n]: ").strip().lower()
    if choice == "y":
        env_file.write_text(
            "# ──────────────────────────────────────\n"
            "# Biến môi trường cho dự án\n"
            "# KHÔNG commit file này lên git!\n"
            "# ──────────────────────────────────────\n\n"
            "# API_KEY=your_api_key_here\n"
            "# DEBUG=true\n",
            encoding="utf-8",
        )
        success(f"Đã tạo: {env_file}")
        _ensure_gitignore_has_dotenv(project_dir)


def _ensure_gitignore_has_dotenv(project_dir: Path):
    """Đảm bảo .gitignore có entry cho .env và venv."""
    gitignore = project_dir / ".gitignore"
    entries_to_add = []

    existing_content = (
        gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    )

    for entry in [".env", "venv/", ".venv/", "__pycache__/", "*.pyc"]:
        if entry not in existing_content:
            entries_to_add.append(entry)

    if not entries_to_add:
        return

    with open(gitignore, "a", encoding="utf-8") as f:
        f.write("\n# Auto-added by setup_venv_in_project.py\n")
        for entry in entries_to_add:
            f.write(f"{entry}\n")

    success(f"Đã cập nhật .gitignore: thêm {', '.join(entries_to_add)}")


def step_show_activate_guide(venv_dir: Path, project_dir: Path):
    """Bước 5 – In hướng dẫn kích hoạt venv."""
    step("Bước 5: Hướng dẫn kích hoạt môi trường ảo")

    activate_cmd = str(venv_dir / "Scripts" / "Activate.ps1")
    activate_cmd_bat = str(venv_dir / "Scripts" / "activate.bat")

    print(
        f"""
  {C.BOLD}PowerShell:{C.RESET}
    {C.GREEN}{activate_cmd}{C.RESET}

  {C.BOLD}CMD:{C.RESET}
    {C.GREEN}{activate_cmd_bat}{C.RESET}

  {C.BOLD}Thoát venv:{C.RESET}
    {C.YELLOW}deactivate{C.RESET}

  {C.BOLD}Lưu packages hiện tại ra requirements.txt:{C.RESET}
    {C.CYAN}pip freeze > requirements.txt{C.RESET}
"""
    )


def step_create_venv_cmd(venv_dir: Path, project_dir: Path):
    """Bước 6 - Tạo file venv.cmd để kích hoạt venv nhanh."""
    step("Bước 6: Tạo file venv.cmd")
    venv_cmd_file = project_dir / "venv.cmd"
    relative_activate = venv_dir.name + r"\Scripts\activate"

    venv_cmd_file.write_text(relative_activate + "\n", encoding="utf-8")
    success(f"Đã tạo: {venv_cmd_file}")
    info(f"Nội dung: {relative_activate}")
    info("Dùng lệnh 'venv' trong CMD để kích hoạt môi trường ảo.")


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Thiết lập môi trường ảo (venv) chuẩn cho dự án Python trên Windows.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--path",
        "-p",
        type=str,
        default=None,
        help="Đường dẫn thư mục dự án (mặc định: thư mục hiện tại).",
    )
    parser.add_argument(
        "--name",
        "-n",
        type=str,
        default=".venv",
        help="Tên thư mục venv (mặc định: 'venv').",
    )
    parser.add_argument(
        "--skip-dotenv",
        action="store_true",
        help="Bỏ qua bước tạo .env.",
    )
    return parser.parse_args()


def main():
    enable_ansi_windows()

    args = parse_args()

    # Xác định thư mục dự án
    if args.path:
        project_dir = Path(args.path).resolve()
    else:
        project_dir = Path(os.getcwd()).resolve()

    if not project_dir.exists():
        error(f"Thư mục không tồn tại: {project_dir}")
        sys.exit(1)

    venv_name: str = args.name

    # ── Header ──────────────────────────────────
    print(f"\n{C.BOLD}{C.CYAN}{'═' * 56}{C.RESET}")
    print(f"{C.BOLD}  🐍  Setup Python venv – Windows Terminal{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'═' * 56}{C.RESET}")
    print(f"  Thư mục dự án : {C.YELLOW}{project_dir}{C.RESET}")
    print(f"  Tên venv       : {C.YELLOW}{venv_name}{C.RESET}")

    # Tìm Python
    try:
        python_exe = find_python()
    except RuntimeError as e:
        error(str(e))
        sys.exit(1)

    py_ver = run([python_exe, "--version"])
    print(f"  Python         : {C.GREEN}{py_ver.stdout.strip()}{C.RESET}")
    print(f"  Executable     : {C.DIM}{python_exe}{C.RESET}\n")

    # ── Các bước setup ──────────────────────────
    venv_dir = step_create_venv(project_dir, venv_name, python_exe)
    step_upgrade_pip(venv_dir)
    step_install_requirements(venv_dir, project_dir)

    if not args.skip_dotenv:
        step_create_dotenv(project_dir)

    step_show_activate_guide(venv_dir, project_dir)
    step_create_venv_cmd(venv_dir, project_dir)

    # ── Footer ──────────────────────────────────
    print(f"{C.BOLD}{C.GREEN}{'═' * 56}{C.RESET}")
    print(f"{C.BOLD}{C.GREEN}  ✔  Setup hoàn tất!{C.RESET}")
    print(f"{C.BOLD}{C.GREEN}{'═' * 56}{C.RESET}\n")


if __name__ == "__main__":
    main()
