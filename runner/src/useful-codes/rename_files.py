import os
import sys


def validate_inputs():
    if len(sys.argv) < 3:
        print(">>> Lỗi: Cần truyền đúng 2 tham số.")
        print('>>> Cách dùng: python rename_files.py "<folder_path>" "<prefix>"')
        return False
    return True


def main():
    if not validate_inputs():
        sys.exit(1)

    folder_path = sys.argv[1].strip()
    prefix = sys.argv[2].strip()

    if not os.path.isdir(folder_path):
        print(f">>> Lỗi: Thư mục không tồn tại: {folder_path}")
        sys.exit(1)

    # Chỉ lấy các file con cấp 1 (không đệ quy vào thư mục con)
    files = [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]

    if not files:
        print(f">>> Không tìm thấy file nào trong: {folder_path}")
        sys.exit(0)

    files.sort()  # Sắp xếp để đảm bảo thứ tự đặt tên nhất quán

    print(f">>> Tìm thấy {len(files)} file. Bắt đầu đổi tên...")

    for index, filename in enumerate(files, start=1):
        _, ext = os.path.splitext(filename)
        new_name = f"{prefix}-{index}{ext}"
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_name)
        os.rename(old_path, new_path)
        print(f"  {filename} -> {new_name}")

    print(f">>> Hoàn thành! Đã đổi tên {len(files)} file.")


if __name__ == "__main__":
    main()
