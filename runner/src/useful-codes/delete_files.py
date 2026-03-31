import os
import sys
import glob


def delete_files_by_ext_list(folder: str, ext_list: list[str]) -> None:
    """
    Xóa tất cả file có extension trong ext_list thuộc folder.

    Args:
        folder:   Đường dẫn đến folder cần xóa file.
        ext_list: Danh sách extension cần xóa (ví dụ: ['txt', 'jpg', 'png']).
    """
    if not os.path.isdir(folder):
        print(f"[ERROR] Folder không tồn tại: {folder}")
        sys.exit(1)

    total_deleted = 0
    total_failed = 0

    for ext in ext_list:
        # Chuẩn hóa extension: bỏ dấu chấm thừa rồi thêm lại 1 dấu chấm
        ext = ext.strip().lstrip(".").lower()
        if not ext:
            continue

        pattern = os.path.join(folder, f"*.{ext}")
        files = glob.glob(pattern)

        if not files:
            print(f"[INFO] Không tìm thấy file nào có extension '.{ext}' trong: {folder}")
            continue

        for file_path in files:
            try:
                os.remove(file_path)
                print(f"[DELETED] {file_path}")
                total_deleted += 1
            except Exception as e:
                print(f"[FAILED]  {file_path} — {e}")
                total_failed += 1

    print(f"\nHoàn tất: {total_deleted} file đã xóa, {total_failed} file thất bại.")


def main():
    if len(sys.argv) != 3:
        print("Cách dùng: py delete_files.py <folder> <ext1,ext2,...>")
        print('Ví dụ:     py delete_files.py "C:/Downloads" "txt,jpg,png"')
        sys.exit(1)

    folder = sys.argv[1]
    ext_list = sys.argv[2].split(",")

    delete_files_by_ext_list(folder, ext_list)


if __name__ == "__main__":
    main()
