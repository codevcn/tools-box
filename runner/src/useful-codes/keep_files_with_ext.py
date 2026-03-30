import os
import sys


def keep_files_with_ext(folder: str, ext: str) -> None:
    """
    Xóa tất cả file KHÔNG có extension chỉ định trong folder.

    Args:
        folder: Đường dẫn đến folder cần xử lý.
        ext:    Extension cần giữ lại (ví dụ: 'png', '.png', 'jpg').
    """
    # Chuẩn hóa extension: bỏ dấu chấm thừa rồi thêm lại 1 dấu chấm
    ext = "." + ext.lstrip(".").lower()

    if not os.path.isdir(folder):
        print(f"[ERROR] Folder không tồn tại: {folder}")
        sys.exit(1)

    all_files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
    ]

    if not all_files:
        print(f"[INFO] Folder trống, không có file nào: {folder}")
        return

    to_delete = [f for f in all_files if not f.lower().endswith(ext)]

    if not to_delete:
        print(f"[INFO] Tất cả file đều có extension '{ext}', không cần xóa.")
        return

    deleted = 0
    failed = 0

    for file_path in to_delete:
        try:
            os.remove(file_path)
            print(f"[DELETED] {file_path}")
            deleted += 1
        except Exception as e:
            print(f"[FAILED]  {file_path} — {e}")
            failed += 1

    kept = len(all_files) - deleted - failed
    print(f"\nHoàn tất: {deleted} file đã xóa, {failed} file thất bại, {kept} file được giữ lại ('{ext}').")


def main():
    if len(sys.argv) != 3:
        print("Cách dùng: py keep_files_with_ext.py <folder> <ext>")
        print('Ví dụ:     py keep_files_with_ext.py "C:/Downloads" "png"')
        sys.exit(1)

    folder = sys.argv[1]
    ext = sys.argv[2]

    keep_files_with_ext(folder, ext)


if __name__ == "__main__":
    main()
