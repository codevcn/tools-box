import os


def generate_qrc():
    # Đường dẫn đến thư mục chứa icon
    assets_dir = "app/src/assets/images/svg"
    qrc_content = ['<!DOCTYPE RCC><RCC version="1.0">', '  <qresource prefix="icons">']

    # Quét tất cả file .svg
    if os.path.exists(assets_dir):
        for filename in os.listdir(assets_dir):
            if filename.endswith(".svg"):
                # Quan trọng: Tạo alias để code có thể gọi ngắn gọn
                # Ví dụ: code gọi ":/icons/app_logo.svg" -> trỏ tới "app/src/assets/images/svg/app_logo.svg"
                file_path = f"{assets_dir}/{filename}"
                qrc_content.append(f'    <file alias="{filename}">{file_path}</file>')
    else:
        print(f"Không tìm thấy thư mục: {assets_dir}")
        return

    qrc_content.append("  </qresource>")
    qrc_content.append("</RCC>")

    # Ghi ra file resources.qrc
    with open("resources.qrc", "w", encoding="utf-8") as f:
        f.write("\n".join(qrc_content))

    print("Đã tạo xong file 'resources.qrc'.")
    print(
        "Vui lòng chạy lệnh biên dịch: pyside6-rcc resources.qrc -o app/src/resources_rc.py"
    )


if __name__ == "__main__":
    generate_qrc()
