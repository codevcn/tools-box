import vtracer
import os


def convert_png_to_svg(input_path, output_path):
    # Sử dụng đúng tên hàm convert_image_to_svg_py
    # Các tham số dưới đây là cấu hình chuẩn xác được hỗ trợ trong Python
    vtracer.convert_image_to_svg_py(
        input_path,
        output_path,
        colormode="color",  # Chế độ màu: "color" (nhiều màu) hoặc "binary" (đen trắng)
        hierarchical="stacked",  # Cách xếp lớp: "stacked" (chồng lên nhau) hoặc "cutout" (cắt xén)
        mode="spline",  # Tạo đường cong mềm mại: "spline", "polygon", hoặc "none"
        filter_speckle=4,  # Lọc các điểm nhiễu nhỏ (mặc định: 4)
        color_precision=6,  # Độ chính xác của màu sắc (mặc định: 6)
        layer_difference=16,  # Độ sai lệch màu giữa các lớp (mặc định: 16)
        corner_threshold=60,  # Ngưỡng tạo góc nhọn (mặc định: 60)
        length_threshold=4.0,  # Chiều dài tối thiểu của một đoạn (mặc định: 4.0)
        max_iterations=10,  # Số vòng lặp tối đa để làm mịn (mặc định: 10)
        splice_threshold=45,  # Ngưỡng nối các đoạn (mặc định: 45)
        path_precision=8,  # Số chữ số thập phân cho các tọa độ path (mặc định: 8)
    )
w

# Kiểm tra tập tin đầu vào có tồn tại hay không trước khi tiến hành chuyển đổi
input_file = "input.png"
output_file = "output.svg"

if os.path.exists(input_file):
    convert_png_to_svg(input_file, output_file)
else:
    print(f"Lỗi: Không tìm thấy tập tin {input_file}")
