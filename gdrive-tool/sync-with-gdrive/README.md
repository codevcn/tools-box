# Sync with Google Drive (SynRive)

Ứng dụng desktop (PySide6) giúp đồng bộ file/thư mục từ máy lên Google Drive bằng rclone, có UI trực quan, log chi tiết và hỗ trợ chọn nhiều mục từ Windows Explorer.

## Tính năng chính
- Đăng nhập Google Drive qua rclone OAuth và lưu remote đã cấu hình.
- Chọn nhiều file/thư mục local, xem preview kèm icon theo loại.
- Nhập đường dẫn đích trên Google Drive và đồng bộ 1 lần bằng rclone `copy`.
- Hiển thị log chi tiết và tiến trình từng file.
- Tích hợp context menu Windows cho file, folder và background folder (multi-select).
- Cửa sổ Settings: phím tắt + About.

## Yêu cầu
- Windows.
- Python 3.x để chạy dạng script.
- `PySide6` (có trong `requirements.txt`).
- `rclone.exe`.

## Cài đặt nhanh (dev)
```powershell
pip install -r requirements.txt
py app/src/main.py
```

Hoặc dùng:
```powershell
dev.cmd
```

> Lưu ý: `run_app.py` và `run_app_multi.py` đang hardcode đường dẫn Python và `main.py`. Nếu máy bạn khác, cần sửa lại 2 file này.

## Chuẩn bị rclone.exe
### 1) Cho bước **đồng bộ**
Hàm `rclone_executable_path()` đang trỏ tới:
```
app/build/bin/rclone.exe
```
Hãy đặt `rclone.exe` đúng vị trí trên trước khi sync, hoặc chỉnh lại đường dẫn trong `app/src/utils/helpers.py`.

### 2) Cho bước **đăng nhập**
`LoginGDriveScreen` dùng `RcloneDriveSetup` với tham số mặc định `rclone` → cần `rclone.exe` nằm trong `PATH`.

Nếu bạn không muốn chỉnh PATH, có thể sửa code để truyền đường dẫn tuyệt đối vào `RcloneDriveSetup` (gợi ý: dùng `rclone_executable_path()`).

## Cách dùng app (chi tiết)
### Bước 1: Mở app
- Chạy `py app/src/main.py` hoặc `dev.cmd`.
- Có thể truyền sẵn đường dẫn:
  ```powershell
  py app/src/main.py "C:\Data\ProjectA" "D:\Docs\Report.pdf"
  ```

### Bước 2: Chọn file/thư mục local
Bạn có 2 cách:
- Nhấn nút **“Chọn thư mục/tệp...”** (Ctrl+O) để chọn 1 thư mục.
- Hoặc mở từ context menu Windows (xem phần “Tích hợp context menu”).

Các mục đã chọn sẽ hiển thị dưới dạng chip; click vào chip sẽ mở File Explorer và select đúng file/thư mục.

### Bước 3: Đăng nhập Google Drive
1. Nhấn **“Đăng nhập Google Drive”** (Ctrl+L).
2. Nhập tên remote (ví dụ: `Drive cá nhân`).
3. Rclone sẽ mở trình duyệt để bạn cấp quyền.
4. Sau khi login thành công, remote sẽ được lưu và đặt là active.

> Nếu login không chạy, kiểm tra rclone trong `PATH`.

### Bước 4: Chọn kho lưu trữ (Active Remote)
Nhấn vào thanh **“Bạn đang đồng bộ lên kho lưu trữ”** để mở danh sách remote và chọn remote đang dùng.

### Bước 5: Nhập đường dẫn đích trên Google Drive
Nhập theo format:
```
Thu muc 1/Thu muc 2/Thu muc 3
```
Không cần dấu `/` ở đầu hoặc cuối. App sẽ lưu đường dẫn đã nhập gần nhất.

### Bước 6: Đồng bộ
Nhấn **“Đồng bộ ngay”** hoặc Ctrl+Enter.

App sẽ:
- Tạo thư mục staging tạm.
- Symlink hoặc copy file/thư mục vào staging.
- Chạy rclone `copy` tới `remote:duong_dan`.

> Hiện tại code đang dùng `MockRcloneSyncWorker` (giả lập tiến trình).  
> Để chạy sync thật, hãy chuyển sang `RcloneSyncWorker` trong `app/src/main.py`.

### Bước 7: Theo dõi tiến trình & log
- Cửa sổ tiến trình hiển thị % từng file.
- Log chi tiết ở phần “Chi tiết đồng bộ”.
- Có nút **“Sao chép”** để copy log nhanh.

### Bước 8: Cài đặt (Settings)
Nhấn Ctrl+I hoặc nút Settings (nếu đã login) để xem:
- Danh sách phím tắt.
- About (tên app, version, tác giả).

## Tích hợp context menu Windows
File: `add_sync_with_gdrive.reg`
- Tạo menu “Sync with Google Drive” cho:
  - File
  - Folder
  - Background folder (chuột phải trong thư mục)

Trước khi chạy `.reg`, hãy chỉnh lại:
- `PYTHON_EXE_FILE_PATH`
- `APP_PY_FILE_PATH`

Sau đó chạy file `.reg` để thêm vào Registry.

## Phím tắt
Ở màn hình chính:
- Ctrl+Q hoặc Alt+Q: Thoát app
- Ctrl+Enter: Đồng bộ ngay
- Ctrl+O: Chọn file/thư mục local
- Ctrl+I: Mở Settings
- Ctrl+L: Đăng nhập Google Drive

Ở các dialog khác:
- Ctrl+Q hoặc Alt+Q: Đóng dialog

## Lưu dữ liệu người dùng
File cấu hình được lưu tại:
```
%APPDATA%\SynRive\data\sync-with-gdrive.json
```
Bao gồm:
- Danh sách remote đã tạo
- Remote đang active
- Đường dẫn Drive đã nhập gần nhất

## Troubleshooting nhanh
- **Không tìm thấy rclone.exe**  
  → Đặt `rclone.exe` vào `app/build/bin/` hoặc chỉnh `rclone_executable_path()`.

- **Login không chạy / không mở browser**  
  → Cần `rclone.exe` trong `PATH` (login đang dùng `rclone` mặc định).

- **Không thấy đồng bộ thật**  
  → Đang dùng mock worker. Chuyển sang `RcloneSyncWorker` trong `app/src/main.py`.

- **Context menu không xuất hiện**  
  → Chạy lại `.reg` sau khi cập nhật đường dẫn Python/app.

## Ghi chú cho dev
- Khi cập nhật icon hoặc `resources.qrc`, chạy `gen-asset.cmd` để rebuild `app/src/resources_rc.py`.
- `run_app_multi.py` gom nhiều item bằng socket port 65432 và chạy app một lần với danh sách paths.
