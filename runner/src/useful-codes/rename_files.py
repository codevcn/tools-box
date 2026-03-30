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

    # Bước 1: Đổi tất cả sang tên tạm thời để tránh conflict với file đang tồn tại
    tmp_paths = []
    for index, filename in enumerate(files):
        old_path = os.path.join(folder_path, filename)
        tmp_name = f"__tmp_{index}__"
        tmp_path = os.path.join(folder_path, tmp_name)
        os.rename(old_path, tmp_path)
        tmp_paths.append((tmp_path, filename))

    # Bước 2: Đổi từ tên tạm sang tên đích cuối cùng
    renamed = 0
    for index, (tmp_path, original_name) in enumerate(tmp_paths, start=1):
        _, ext = os.path.splitext(original_name)
        new_name = f"{prefix}-{index}{ext}"
        new_path = os.path.join(folder_path, new_name)
        os.rename(tmp_path, new_path)
        print(f"  {original_name} -> {new_name}")
        renamed += 1

    print(f">>> Hoàn thành! Đã đổi tên {renamed} file.")


if __name__ == "__main__":
    main()
