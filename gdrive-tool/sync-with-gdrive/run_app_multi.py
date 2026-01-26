# File dùng cho Registry (chọn nhiều file -> chạy script nhiều lần)

import sys
import socket
import subprocess
import traceback
from datetime import datetime
from pathlib import Path

PYTHON_EXE_FILE_PATH = r"D:\Python-3-12\python.exe"
APP_PY_FILE_PATH = r"D:\D-Documents\TOOLs\gdrive-tool\sync-with-gdrive\app\src\app.py"

# --- CẤU HÌNH ---
PORT = 65432  # Cổng TCP để Master lắng nghe kết nối từ Slave (nên chọn cổng > 1024)
HOST = "127.0.0.1"

# Thời gian chờ (giây). Nếu sau khoảng này không có thêm file nào, Master sẽ chốt đơn.
# Windows gửi các lệnh rất nhanh, nên 0.2 - 0.5 là đủ an toàn và nhanh.
SLIDING_TIMEOUT = 1.0

# Kích thước message khi socket nhận dữ liệu.
# 4096 là "tiêu chuẩn vàng" (convention) trong lập trình mạng và hệ thống, đủ lớn để chứa trọn vẹn các gói tin TCP trong ngữ cảnh truyền path string này.
BUFFER_SIZE = 4096


def log_test(any):
    try:
        # Sử dụng thư mục TEMP của Windows
        log_dir = Path.home() / "AppData" / "Local" / "Temp" / "SyncWithGDrive"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "test.log"

        # Tạo nội dung log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_content = f"""
    {'='*80}
    [{timestamp}] TEST
    Message: {any}
    {'='*80}

    """
        # Ghi log (append mode)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_content)
    except Exception:
        pass


def run_slave(file_path: str):
    """Slave: Chỉ có nhiệm vụ gửi file cho Master rồi tự sát"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(file_path.encode("utf-8"))
    except ConnectionRefusedError:
        # Trường hợp hiếm: Slave gọi đến cổng 65432 nhưng không có ai nghe máy.
        # Có thể Master vừa mới bị tắt đột ngột, hoặc Master gặp lỗi và crash ngay trước khi Slave kịp gọi.
        raise ValueError("??? Lỗi: Không thể kết nối đến Master để gửi file")
    except Exception as e:
        # Silent fail để không hiện lỗi lên mặt người dùng
        raise ValueError(f"??? Lỗi không xác định ở Slave: {e}")


def run_master(initial_file_path: str):
    """Master: Gom file với cơ chế Sliding Timeout"""
    files_to_process = [initial_file_path]

    # Tạo socket server, AF_INET cho IPv4, SOCK_STREAM cho TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        server_socket.settimeout(
            SLIDING_TIMEOUT
        )  # Thiết lập thời gian chờ cho việc lắng nghe kết nối từ Slave

        while True:
            try:
                # (Blocking) Chờ kết nối từ Slave. Nếu quá SLIDING_TIMEOUT không có Slave nào gọi, sẽ nhảy vào except
                conn, _ = server_socket.accept()

                with conn:
                    # Nếu có kết nối, nhận file path
                    data = conn.recv(BUFFER_SIZE)
                    if data:
                        new_file = data.decode("utf-8")
                        files_to_process.append(new_file)
                        # Mỗi khi nhận được 1 file, vòng lặp while quay lại
                        # và settimeout lại được kích hoạt từ đầu.
                        # -> Đây chính là cơ chế Sliding Timeout.

            except socket.timeout:
                # Không còn Slave nào gửi file nữa, dừng gom.
                # --- LOGIC XỬ LÝ CHÍNH ---
                run_app(files_to_process)
                return  # Kết thúc Master
    except Exception as e:
        raise e
    finally:
        server_socket.close()


def run_app(file_paths: list[str]):
    subprocess.Popen([PYTHON_EXE_FILE_PATH, APP_PY_FILE_PATH, *file_paths])


def log_exception(e: Exception):
    """Ghi log lỗi ra file trong thư mục hệ thống"""
    try:
        # Sử dụng thư mục TEMP của Windows
        log_dir = Path.home() / "AppData" / "Local" / "Temp" / "SyncWithGDrive"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "errors.log"

        # Tạo nội dung log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_content = f"""
{'='*80}
[{timestamp}] ERROR
{'='*80}
Exception Type: {type(e).__name__}
Exception Message: {str(e)}

Traceback:
{traceback.format_exc()}
{'='*80}

"""

        # Ghi log (append mode)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_content)

    except Exception:
        # Silent fail - không làm gì nếu không ghi được log
        # để tránh crash khi có lỗi trong quá trình log
        pass


if __name__ == "__main__":
    # Lấy file path an toàn
    current_file_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        if current_file_path:
            # Cố gắng BIND port.
            # Nếu thành công -> Ta là Master (người đầu tiên).
            # Nếu thất bại (Port đang bận) -> Ta là Slave (người đến sau).
            try:
                # Kiểm tra nhanh bằng cách tạo socket bind thử
                # Lưu ý: Không cần close socket này ở đây vì nếu bind được,
                # ta sẽ dùng logic trong run_master để tạo lại hoặc pass socket object vào (tùy cách viết).
                # Để code đơn giản và sạch, ta dùng try/except block trong run_master nhưng
                # cách tốt nhất là tách biệt việc check.

                # CÁCH TIẾP CẬN ATOMIC:
                # Thử làm Master luôn. Nếu lỗi Address already in use thì làm Slave.
                run_master(current_file_path)

            except Exception as e:
                if isinstance(e, OSError):
                    log_test(e.errno)
                    if e.errno == 10048:  # Mã lỗi: Address already in use (Windows)
                        run_slave(current_file_path)
                    else:
                        raise ValueError("??? Lỗi nội bộ: Sai mã lỗi OSError")
                else:
                    raise ValueError("??? Lỗi: Không xác định khi cố gắng bind port")
        else:
            raise ValueError("??? Lỗi: Thiếu tham số file path")
    except ValueError as ve:
        log_exception(ve)
