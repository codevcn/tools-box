import os
import sys
import re


def read_file_definitions(config_path: str):
    """
    Đọc và phân tích file cấu hình file_contents.txt.
    Format:
    @<filename>
    @<multi-line content>
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Không tìm thấy file cấu hình: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Regex: tìm tất cả các cặp @<...>
    pattern = re.compile(r"@<([^>]+)>\s*@<([\s\S]*?)>", re.MULTILINE)
    matches = pattern.findall(text)

    files = []
    for filename, content in matches:
        files.append({"filename": filename.strip(), "content": content.strip("\n")})

    return files


def create_files(target_dir: str, files_to_create: list):
    print(f">>> Thư mục được chọn: {target_dir}\n")

    for f in files_to_create:
        file_path = os.path.join(target_dir, f["filename"])
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(f["content"])
        print(f">>> Đã tạo: {f['filename']}")


if __name__ == "__main__":
    # Xác định thư mục đích
    if len(sys.argv) > 1:
        target_dir = os.path.abspath(sys.argv[1])
    else:
        target_dir = os.getcwd()

    if not os.path.isdir(target_dir):
        print(f"??? Lỗi: '{target_dir}' không phải là thư mục hợp lệ.")
        sys.exit(1)

    # File cấu hình nằm ở thư mục cha của script
    files_info_filename = "files_info.txt"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(script_dir), files_info_filename)

    try:
        files_to_create = read_file_definitions(config_path)
        if not files_to_create:
            print(
                f"??? Không tìm thấy định nghĩa file hợp lệ trong {files_info_filename}."
            )
            sys.exit(0)

        create_files(target_dir, files_to_create)
    except Exception as e:
        print(f"??? Lỗi: {e}")
