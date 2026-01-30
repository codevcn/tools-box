# Runner - Công Cụ Tự Động Hóa Dòng Lệnh

Công cụ dòng lệnh dựa trên Python để tự động hóa các tác vụ phát triển phổ biến, quản lý workspace và thực thi các thao tác git trên Windows.

## Tính Năng

- 🚀 Quản lý workspace và thư mục nhanh chóng
- 📝 Tự động hóa thao tác Git (commit, push, remote)
- 💻 Mở dự án trong VSCode hoặc Cursor IDE
- 🔧 Hiển thị tiện ích và thông tin hệ thống
- 📊 Quản lý trạng thái dự án
- 🔗 Tài liệu tham khảo lệnh cURL

## Yêu Cầu

- Python >= 3.12.0
- Windows OS (sử dụng Windows Terminal và lệnh cmd)
- VSCode hoặc Cursor IDE (cho tính năng mở code)
- Git (cho các thao tác git)

## Cài Đặt

1. Clone hoặc tải repository này về
2. Cài đặt các dependencies Python:
   ```bash
   pip install -r requirements.txt
   ```
3. Tạo file `.env` trong `D:/D-Documents/TOOLs/runner/` với nội dung:
   ```env
   ROOT_FOLDER_PATH=D:/D-Documents/TOOLs/runner
   ```
4. Thêm thư mục runner vào biến môi trường PATH để sử dụng lệnh `runner` toàn cục

## Cách Sử Dụng

```bash
runner [type] [action] [flags]
```

### Các Type Có Sẵn

- `open` - Mở thư mục trong file explorer của hệ thống
- `code` - Mở dự án trong VSCode/Cursor
- `git` - Thực thi thao tác git
- `run` - Chạy ứng dụng hoặc script
- `print` - Hiển thị thông tin

### Các Flag Có Sẵn

- `-h, --help` - Hiển thị thông tin trợ giúp
- `-m, --message` - Cung cấp message (cho git commit)
- `-c, --cursor` - Sử dụng Cursor IDE thay vì VSCode
- `-p, --powershell-only` - Chỉ mở thư mục trong Windows Terminal (bỏ qua IDE)
- `-v, --value` - Giá trị đầu vào cho script bên ngoài

## Các Lệnh

### Lệnh Open

```bash
runner open              # Mở file runner trong VSCode
runner open ws           # Mở thư mục working workspaces trong system folder
runner open env          # Mở bảng điều khiển biến môi trường
```

### Lệnh Code

```bash
runner code              # Mở file runner trong VSCode
runner code ws           # Mở working workspace trong VSCode và terminal
runner code test         # Mở thư mục testing
runner code ts-template  # Mở TypeScript template
runner code js           # Mở thư mục testing JavaScript
runner code ts           # Mở thư mục testing TypeScript
runner code nestjs       # Mở NestJS template
runner code py           # Mở thư mục testing Python
runner code ext          # Mở thư mục browser extensions
```

Thêm flag `-c` hoặc `--cursor` để mở trong Cursor IDE:
```bash
runner code test -c      # Mở thư mục testing trong Cursor IDE
```

### Lệnh Git

```bash
runner git commit -m "your commit message"  # Add, commit, và push lên origin main
runner git remote                           # Hiển thị git remote repositories
```

### Lệnh Run

```bash
runner run test-bat      # Chạy file batch test
runner run unikey        # Khởi động ứng dụng Unikey
```

### Lệnh Print

```bash
runner print os          # Hiển thị thông tin OS
runner print stts        # Hiển thị mô tả runner status
runner print ws          # Liệt kê các VSCode workspace
runner print curl        # Hiển thị tài liệu tham khảo lệnh cURL
runner print dir         # Hiển thị đường dẫn thư mục runner
runner print cmds        # Hiển thị danh sách các lệnh hữu ích
```

## Ví Dụ

```bash
# Mở workspace trong VSCode với terminal
runner code ws

# Mở workspace trong Cursor chỉ với PowerShell terminal
runner code ws -c -p

# Commit và push thay đổi
runner git commit -m "Add new feature"

# Kiểm tra git remotes
runner git remote

# Mở thư mục testing trong Cursor IDE
runner code test --cursor

# Hiển thị thông tin hệ thống
runner print os
```

## Cấu Trúc Dự Án

```
runner/
├── src/
│   ├── runner.py              # Điểm khởi đầu chính
│   ├── runner_git.py          # Xử lý thao tác Git
│   ├── runner_cURL.py         # Hiển thị tài liệu tham khảo cURL
│   ├── runner_os_info.py      # Hiển thị thông tin OS
│   ├── runner_print_content.py # Hiển thị file nội dung
│   ├── runner_statuses.py     # Thông tin trạng thái
│   ├── runner_main_ws.py      # Quản lý workspace
│   ├── contents/              # Các file nội dung văn bản
│   │   ├── help.txt
│   │   ├── cURL.txt
│   │   ├── statuses.txt
│   │   └── list-useful-commands.txt
│   └── useful-codes/          # Các script tiện ích
│       ├── create_files_in_folder.py
│       ├── print_folder_tree.py
│       └── rename_files.py
├── warehouse/                 # Các file lưu trữ/backup
├── requirements.txt           # Các thư viện Python
├── runner.cmd                 # File batch khởi động Windows
└── README.md                  # File này
```

## Cấu Hình

Công cụ sử dụng file `.env` để cấu hình. Tạo file tại:
```
D:/D-Documents/TOOLs/runner/.env
```

Các biến môi trường bắt buộc:
- `ROOT_FOLDER_PATH` - Đường dẫn thư mục gốc cho dự án runner

## Phát Triển

### Thêm Lệnh Mới

1. Định nghĩa hằng số trong [runner.py](src/runner.py):
   ```python
   RUNNER_TYPE_NEW = "newtype"
   RUNNER_ACTION_NEW = "newaction"
   ```

2. Tạo hàm xử lý:
   ```python
   def handle_new_action():
       # Code của bạn
       sys.exit(0)
   ```

3. Thêm vào logic chính:
   ```python
   elif type_included == RUNNER_TYPE_NEW:
       if action_included == RUNNER_ACTION_NEW:
           handle_new_action()
   ```

### Xử Lý Lỗi

Công cụ sử dụng exceptions để xử lý lỗi. Tất cả lỗi từ người dùng được bắt và hiển thị với thông báo mô tả:
```python
raise Exception("Thông báo lỗi")
```

## Giấy Phép

Đây là công cụ tự động hóa cá nhân. Bạn có thể tự do điều chỉnh để sử dụng cho mình.

## Tác Giả

Được tạo ra để tự động hóa quy trình phát triển cá nhân.

## Cập Nhật Lần Cuối

11 tháng 1, 2026
