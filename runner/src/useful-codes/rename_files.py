import os
import sys
import re


def validate_inputs():
    if len(sys.argv) < 2:
        print(">>> Lỗi: Cần truyền ít nhất 1 tham số (folder_path).")
        print('>>> Cách dùng: python rename_files.py "<folder_path>" ["<prefix>"]')
        return False
    return True


def detect_prefix(files: list[str]) -> str | None:
    """
    Tự động phát hiện prefix từ danh sách file.
    Tìm các file có dạng <prefix>-<number>.<ext>.
    Chỉ chấp nhận prefix nếu có ít nhất 2 file cùng prefix.

    Returns:
        prefix (str) nếu phát hiện được, None nếu không.
    """
    pattern = re.compile(r"^(.+)-(\d+)\.[^.]+$")
    prefix_counts: dict[str, int] = {}

    for filename in files:
        match = pattern.match(filename)
        if match:
            detected = match.group(1)
            prefix_counts[detected] = prefix_counts.get(detected, 0) + 1

    # Lọc prefix có ít nhất 2 file
    valid_prefixes = {p: c for p, c in prefix_counts.items() if c >= 2}

    if not valid_prefixes:
        return None

    # Chọn prefix có nhiều file nhất (ưu tiên prefix phổ biến nhất)
    best_prefix = max(valid_prefixes, key=lambda p: valid_prefixes[p])
    return best_prefix


def main():
    if not validate_inputs():
        sys.exit(1)

    folder_path = sys.argv[1].strip()
    prefix = sys.argv[2].strip() if len(sys.argv) >= 3 else ""

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

    # --- Pre-processing: xác định prefix ---
    if prefix:
        # Prefix được cung cấp trực tiếp -> dùng luôn
        print(f'>>> Dùng prefix được cung cấp: "{prefix}"')
    else:
        # Tự động detect prefix từ các file có dạng <prefix>-<number>.<ext>
        prefix = detect_prefix(files)
        if not prefix:
            prefix = os.path.basename(os.path.abspath(folder_path))
            print(f'>>> Không tìm thấy prefix, sử dụng tên folder làm prefix: "{prefix}"')
        else:
            print(f'>>> Tự động phát hiện prefix: "{prefix}"')

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
