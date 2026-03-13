import os
import re
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/runner/.env")


def main():
    # Tên tệp chứa cấu trúc dữ liệu nguồn của bạn
    source_file = (os.getenv("CONTENTS_FOLDER_PATH") or "") + "/files_source.txt"

    # Kiểm tra xem tệp nguồn có tồn tại trong thư mục hiện tại hay không
    if not os.path.exists(source_file):
        print(
            f"Lỗi: Không tìm thấy tệp '{source_file}'. Vui lòng đảm bảo tệp tồn tại trong cùng thư mục với tập lệnh Python."
        )
        return

    # Đọc toàn bộ nội dung của tệp nguồn
    with open(source_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Sử dụng biểu thức chính quy (Regex) để trích xuất thông tin
    pattern = r"@@file-name\[\[(.*?)\]\]\{\{(.*?)\}\}\s*@@file-content\{\{([\s\S]*?)\}\}(?=\s*@@file-name|$)"
    matches = re.findall(pattern, content)

    if not matches:
        print(
            "Không tìm thấy dữ liệu hợp lệ trong tệp nguồn. Vui lòng kiểm tra lại cấu trúc văn bản của bạn."
        )
        return

    # Hiển thị các tùy chọn ra terminal
    print("Danh sách các tùy chọn:")
    print("0. quit")  # Thêm tùy chọn thoát chương trình ở đầu danh sách

    for i, match in enumerate(matches, 1):
        display_name = match[0].strip()
        print(f"{i}. {display_name}")

    # Chờ người dùng nhập vào các con số
    user_input = input(
        "\nNhập các mục bạn muốn tạo, cách nhau bởi khoảng trắng (ví dụ: 1 2 3) hoặc nhập 0 để thoát: "
    )

    # Xử lý chuỗi dữ liệu đầu vào của người dùng
    try:
        choices = [int(x) for x in user_input.split()]
    except ValueError:
        print("Lỗi: Vui lòng chỉ nhập các con số nguyên, cách nhau bởi khoảng trắng.")
        return

    # Kiểm tra xem người dùng có chọn thoát chương trình hay không
    if 0 in choices:
        print("Đã nhận được lệnh thoát. Đang đóng chương trình...")
        sys.exit()  # Kết thúc chương trình hoàn toàn

    # Xử lý quá trình tạo tệp và thư mục
    print("\nĐang tiến hành tạo tệp và thư mục...")
    current_dir = os.getcwd()  # Lấy thư mục hiện tại nơi terminal đang đứng

    for choice in choices:
        # Kiểm tra xem con số người dùng nhập có nằm trong phạm vi menu hay không
        if 1 <= choice <= len(matches):
            file_name = matches[choice - 1][1].strip()
            file_content = matches[choice - 1][2]

            # Tạo đường dẫn tuyệt đối cho tệp mới
            file_path = os.path.join(current_dir, file_name)

            # Lấy phần đường dẫn thư mục từ đường dẫn tệp đầy đủ
            dir_path = os.path.dirname(file_path)

            # Tự động tạo thư mục nếu dir_path không rỗng và thư mục chưa tồn tại
            # Tham số exist_ok=True giúp bỏ qua lỗi nếu thư mục đã có sẵn
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)

            try:
                # Tạo tệp và ghi nội dung vào
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)

                print(f"  + Đã tạo thành công: {file_name}")
            except Exception as e:
                print(f"  - Lỗi khi tạo tệp '{file_name}': {e}")
        else:
            print(
                f"  - Cảnh báo: Lựa chọn '{choice}' không hợp lệ, hệ thống đã bỏ qua tùy chọn này."
            )


if __name__ == "__main__":
    main()
