import os
import sys
import glob


def delete_files_by_ext(folder: str, ext: str) -> None:
    """
    Xóa tất cả file có extension chỉ định trong folder.

    Args:
        folder: Đường dẫn đến folder cần xóa file.
        ext:    Extension của file cần xóa (ví dụ: 'txt', '.txt', 'jpg').
    """
    # Chuẩn hóa extension: bỏ dấu chấm thừa rồi thêm lại 1 dấu chấm
    ext = ext.lstrip(".").lower()

    if not os.path.isdir(folder):
        print(f"[ERROR] Folder không tồn tại: {folder}")
        sys.exit(1)

    pattern = os.path.join(folder, f"*.{ext}")
    files = glob.glob(pattern)

    if not files:
        print(f"[INFO] Không tìm thấy file nào có extension '.{ext}' trong: {folder}")
        return

    deleted = 0
    failed = 0

    for file_path in files:
        try:
            os.remove(file_path)
            print(f"[DELETED] {file_path}")
            deleted += 1
        except Exception as e:
            print(f"[FAILED]  {file_path} — {e}")
            failed += 1

    print(f"\nHoàn tất: {deleted} file đã xóa, {failed} file thất bại.")


def main():
    if len(sys.argv) != 3:
        print("Cách dùng: py delete_files.py <folder> <ext>")
        print('Ví dụ:     py delete_files.py "C:/Downloads" "txt"')
        sys.exit(1)

    folder = sys.argv[1]
    ext = sys.argv[2]

    delete_files_by_ext(folder, ext)


if __name__ == "__main__":
    main()
