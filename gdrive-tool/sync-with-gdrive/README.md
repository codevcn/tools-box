# 🚀 Sync with Google Drive

Ứng dụng desktop Windows giúp đồng bộ file và folder lên Google Drive nhanh chóng qua context menu chuột phải, sử dụng PySide6 (Qt) và rclone.

## ✨ Tính năng

- 🖱️ **Context menu integration**: Chuột phải trên file/folder → "Sync with Google Drive"
- 📦 **Multi-select support**: Chọn nhiều file/folder cùng lúc
- 🔐 **Multi-account**: Hỗ trợ nhiều tài khoản Google Drive
- 📊 **Progress tracking**: Theo dõi tiến trình chi tiết từng file
- ⚡ **Master-Slave architecture**: Gom file thông minh với socket TCP
- 🎨 **Modern dark UI**: Giao diện đẹp với theme tối
- ⌨️ **Keyboard shortcuts**: Ctrl+Q, Ctrl+Enter, Ctrl+O, Ctrl+I
- 🔄 **Auto-login**: Tự động xử lý OAuth với Google Drive

## 📋 Yêu cầu

- **Windows 10/11**
- **Python 3.10+** (khuyến nghị 3.12)
- **rclone** (phải có trong PATH)
- **PySide6** và dependencies

## 🔧 Cài đặt

### 1. Cài đặt Python dependencies

```bash
pip install PySide6
```

### 2. Cài đặt rclone

Tải và cài đặt [rclone](https://rclone.org/downloads/) cho Windows, đảm bảo `rclone.exe` nằm trong PATH.

Kiểm tra:
```bash
rclone version
```

### 3. Cấu hình đường dẫn

Chỉnh sửa các file sau để phù hợp với hệ thống của bạn:

**run_app_multi.py**:
```python
PYTHON_EXE_FILE_PATH = r"D:\Python-3-12\python.exe"  # Đường dẫn Python của bạn
APP_PY_FILE_PATH = r"D:\...\sync-with-gdrive\app\src\app.py"  # Đường dẫn app.py
```

**run_app.py**: Tương tự như trên

**add_sync_with_gdrive.reg**: Chỉnh sửa tất cả đường dẫn:
```reg
@="\"D:\\Python-3-12\\python.exe\" \"D:\\...\\run_app_multi.py\" \"%1\""
"Icon"="D:\\...\\app_logo.ico"
```

### 4. Đăng ký Context Menu

1. Mở file `add_sync_with_gdrive.reg` bằng Notepad
2. Kiểm tra lại tất cả đường dẫn đã chính xác
3. Double-click file `.reg` để thêm vào Registry
4. Chấp nhận cảnh báo của Windows

## 🎯 Cách sử dụng

### Lần đầu sử dụng

1. Chọn file/folder → Chuột phải → **"Sync with Google Drive"**
2. Click **"Đăng nhập Google Drive"**
3. Nhập tên kho lưu trữ (ví dụ: "My Drive", "Work Drive")
4. Trình duyệt sẽ mở → Đăng nhập Google và cấp quyền
5. Hoàn tất!

### Sử dụng thường xuyên

1. Chọn file/folder muốn sync
2. Chuột phải → **"Sync with Google Drive"**
3. Chọn kho lưu trữ (nếu có nhiều tài khoản)
4. Nhập đường dẫn đích trên Google Drive (ví dụ: `Documents/Projects`)
5. Click **"Đồng bộ ngay"** hoặc nhấn **Ctrl+Enter**
6. Theo dõi tiến trình trong dialog

### Phím tắt

| Phím tắt | Chức năng |
|----------|-----------|
| `Ctrl+Q` hoặc `Alt+Q` | Thoát ứng dụng |
| `Ctrl+Enter` | Bắt đầu đồng bộ |
| `Ctrl+O` | Chọn thư mục/tệp |
| `Ctrl+I` | Mở cài đặt |

## 📁 Cấu trúc dự án

```
sync-with-gdrive/
├── app/
│   └── src/
│       ├── app.py                      # Main window
│       ├── login_gdrive_screen.py      # Dialog đăng nhập
│       ├── active_remote_info.py       # Chọn kho lưu trữ
│       ├── settings_screen.py          # Cài đặt
│       ├── sync_progress.py            # Dialog tiến trình
│       ├── components/                 # UI components
│       │   ├── button.py
│       │   ├── dialog.py
│       │   ├── label.py
│       │   └── ...
│       ├── workers/                    # Background tasks
│       │   ├── sync_worker.py          # Rclone sync worker
│       │   └── authorize_gdrive_worker.py
│       ├── data/
│       │   ├── data_manager.py         # Quản lý config
│       │   └── sync-with-gdrive.json   # User data
│       ├── configs/
│       │   └── configs.py              # Constants & colors
│       ├── utils/
│       │   └── helpers.py              # Helper functions
│       └── mixins/
│           └── keyboard_shortcuts.py
├── run_app_multi.py                    # Launcher (multi-select)
├── run_app.py                          # Launcher (send-to)
├── add_sync_with_gdrive.reg            # Registry file
├── app_logo.ico                        # Icon
├── dev.cmd                             # Development script
└── test.cmd                            # Test script
```

## ⚙️ Cơ chế hoạt động

### Master-Slave Architecture (run_app_multi.py)

Khi user chọn nhiều file, Windows gọi script nhiều lần song song. Để gom tất cả file vào 1 lần chạy app:

```
┌─────────────────────────────────────────────────────┐
│ User chọn 3 files → Windows gọi script 3 lần       │
└─────────────────────────────────────────────────────┘
                    ↓
        ┌───────────┴────────────┐
        ↓                        ↓                    ↓
   Process 1               Process 2           Process 3
  (Master)                 (Slave)             (Slave)
        │                        │                    │
   Bind port 65432         Try bind → Fail      Try bind → Fail
        │                        │                    │
   Listen for files         Send file          Send file
        │                   to Master          to Master
        │◄───────────────────┘                       │
        │◄────────────────────────────────────────────┘
        │
   Wait 1s (sliding timeout)
        │
   No more files → Launch app with all 3 files
```

**Cơ chế Sliding Timeout**: Timeout reset mỗi khi nhận file mới, đảm bảo gom đủ tất cả file.

### Sync Worker (RcloneSyncWorker)

1. Tạo staging directory (temp folder)
2. Symlink/copy files vào staging
3. Gọi `rclone copy` với `--use-json-log`
4. Parse JSON log real-time để lấy progress
5. Emit signals để update UI
6. Cleanup staging sau khi xong

## 🔍 Troubleshooting

### Vấn đề: Không thấy "Sync with Google Drive" trong context menu

**Giải pháp**:
1. Kiểm tra file `.reg` đã chạy chưa
2. Restart File Explorer: `Ctrl+Shift+Esc` → Restart "Windows Explorer"
3. Kiểm tra đường dẫn trong Registry Editor (`regedit.exe`):
   - `HKEY_CURRENT_USER\Software\Classes\*\shell\SyncWithGDrive`
   - `HKEY_CURRENT_USER\Software\Classes\Directory\shell\SyncWithGDrive`

### Vấn đề: App không mở hoặc crash

**Giải pháp**:
1. Kiểm tra log: `%USERPROFILE%\AppData\Local\Temp\SyncWithGDrive\errors.log`
2. Kiểm tra Python path trong script có đúng không
3. Test trực tiếp: `python app/src/app.py "D:\test.txt"`

### Vấn đề: "Không tìm thấy rclone"

**Giải pháp**:
```bash
# Kiểm tra rclone
where rclone

# Nếu không có, thêm vào PATH hoặc đặt đường dẫn đầy đủ
```

### Vấn đề: Chọn 2 file nhưng chỉ sync 1 file

**Giải pháp**:
- Tăng `SLIDING_TIMEOUT` trong `run_app_multi.py` (mặc định 1.0s)
- Kiểm tra log test: `%USERPROFILE%\AppData\Local\Temp\SyncWithGDrive\test.log`

### Vấn đề: "Permission denied" khi sync

**Giải pháp**:
1. Đăng nhập lại Google Drive
2. Kiểm tra scope: Phải là `drive` (full access)
3. Xóa token cũ: `rclone config` → Delete remote → Tạo lại

## 📝 Config file

**Vị trí**: `app/src/data/sync-with-gdrive.json`

```json
{
    "remotes": ["My-Drive", "Work-Drive"],
    "active_remote": "My-Drive",
    "last_gdrive_entered_dir": "Documents/Projects",
    "last_sync": "2026-01-26T10:30:00"
}
```

## 🛠️ Development

### Chạy trực tiếp (test)

```bash
# Test với 1 file
python app/src/app.py "D:\test.txt"

# Test với nhiều file
python app/src/app.py "D:\file1.txt" "D:\file2.txt" "D:\folder"

# Hoặc dùng dev.cmd
dev "D:\test.txt"
```

### Test Master-Slave

```bash
# Terminal 1
python run_app_multi.py "D:\file1.txt"

# Terminal 2 (trong vòng 1 giây)
python run_app_multi.py "D:\file2.txt"
```

### Gỡ context menu

Tạo file `remove_sync_with_gdrive.reg`:
```reg
Windows Registry Editor Version 5.00

[-HKEY_CURRENT_USER\Software\Classes\*\shell\SyncWithGDrive]
[-HKEY_CURRENT_USER\Software\Classes\Directory\shell\SyncWithGDrive]
[-HKEY_CURRENT_USER\Software\Classes\Directory\Background\shell\SyncWithGDrive]
```

## 📄 License

MIT License - Tự do sử dụng và chỉnh sửa.

## 🤝 Contributing

Mọi đóng góp đều được hoan nghênh! Vui lòng:
1. Fork repo
2. Tạo branch mới
3. Commit changes
4. Push và tạo Pull Request

## 📧 Liên hệ

Nếu gặp vấn đề, vui lòng tạo issue trên GitHub hoặc kiểm tra log files:
- Error log: `%TEMP%\SyncWithGDrive\errors.log`
- Test log: `%TEMP%\SyncWithGDrive\test.log`

---

**Made with ❤️ using PySide6 & rclone**
