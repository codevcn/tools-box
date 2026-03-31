# Runner CLI - Công Cụ Tự Động Hóa Dòng Lệnh Python

**Runner CLI** là một công cụ dòng lệnh (CLI) được viết bằng Python nhằm tự động hóa các tác vụ lặp đi lặp lại hàng ngày trên hệ điều hành Windows. Công cụ cung cấp một wrapper thống nhất và tiện lợi để điều khiển ứng dụng hệ thống, mở Workspace/IDE (VSCode, Antigravity, Cursor), thao tác Git tự động và thực thi các tiện ích xử lý file nhanh chóng.

---

## 🚀 Tính Năng Nổi Bật

- **Mở siêu tốc:** Mở thư mục gốc, thư mục làm việc, Prompt templates hoặc Environment Variables chỉ qua 2-3 ký tự.
- **Tích hợp IDE:** Tự động mở project cùng với các cửa sổ terminal phục vụ chạy scripts tương ứng bằng `wt` (Windows Terminal) và mở trình duyệt tự động. Hỗ trợ đa IDE qua cờ lệnh (VSCode, Antigravity).
- **Git thông minh:** Rút gọn chuỗi lệnh `git add .`, `git commit` và `git push` khép kín vào một câu lệnh duy nhất hoạt động trên thread terminal độc lập.
- **Quản lý File & Tooling độc lập:** Đổi tên hàng loạt (`rn-files`), Xóa theo format (`del-files`, `keep-files`), tự động setup default Chrome Download Path, sinh file mẫu (`cr-files`), convert định dạng (`png->svg`, `txt->srt`).
- **In Output Hệ Thống:** Lấy OS Infomation siêu nhanh, tra cứu lệnh cURL thần tốc, kiểm tra Path.
- **Hệ thống Tra cứu Tích hợp:** Dùng flag `--des` sau mỗi lệnh để render ra mô tả chi tiết của lệnh đó trực tiếp trên terminal.

---

## 📦 Yêu Cầu & Cài Đặt

### Yêu cầu nền tảng:

- **Python:** `>= 3.12.0`
- **Hệ điều hành:** Windows (sử dụng Windows Terminal, PowerShell và lệnh `cmd`)
- **Git** đã thêm vào PATH.
- (Tùy chọn) Cài sẵn VSCode hoặc Antigravity IDE.

### Cài đặt:

1. Clone hoặc tải project này về máy vào một thư mục cố định (Ví dụ: `D:/D-Documents/TOOLs/runner/`).
2. Mở Terminal tại thư mục đó và cài đặt thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
3. Khởi tạo cấu hình bằng file `.env` (xem chi tiết ở mục Cấu hình).
4. Thêm thư mục chứa project (`runner/`) vào **Environment Variables (PATH)** để có thể gọi lệnh `runner` ở bất kỳ thư mục nào trên cmd/powershell.

---

## ⚙️ Cấu Hình (`.env`)

Tạo một file `.env` ở thư mục gốc của project theo mẫu dưới đây:

```env
ROOT_FOLDER_PATH=D:/D-Documents/TOOLs/runner
USEFUL_CODES_FOLDER_PATH=D:/D-Documents/TOOLs/runner/src/useful-codes
CONTENTS_FOLDER_PATH=D:/D-Documents/TOOLs/runner/src/contents
TEMPLATE_REPLACER_FOLDER_PATH=<Đường_dẫn_đến_Template_Replacer>

# API dùng cho Auto-Gen Subtitles YouTube
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash
TRANSLATE_CHUNK_SIZE=30
```

---

## 📖 Cách Sử Dụng

### Cú pháp chung

```bash
runner [<type> <action> [<value> [<extra>]]] [flags...]
```

### Các Flags Toàn Cục

| Flag                      | Mô tả                                                              |
| ------------------------- | ------------------------------------------------------------------ |
| `-h`, `--help`            | In hướng dẫn (`help.txt`) ra màn hình terminal.                    |
| `--des`                   | In ra mô tả, giải thích chi tiết chức năng của câu lệnh hiện tại.  |
| `-m "text"`, `--message`  | Truyền message (thường bắt buộc khi dùng chung với `git commit`).  |
| `-a`, `--antigravity-IDE` | Cờ ép mở bằng Antigravity IDE (mặc định là VSCode).                |
| `-p`, `--powershell-only` | Bỏ qua việc mở giao diện IDE, chỉ mở folder trên Windows Terminal. |

---

## 🛠 Tập Hợp Các Lệnh (31 Lệnh)

### 1. TYPE `open` - Mở bằng File Explorer hệ thống

- `runner open` — Mở thư mục gốc của runner.
- `runner open ws` — Mở folder chứa VSCode Workspaces.
- `runner open env` — Mở bảng Environment Variables (Windows).
- `runner open proms` — Mở thư mục Prompts của Template Replacer.

### 2. TYPE `code` - Mở bằng IDE (VSCode / Antigravity)

- `runner code` — Mở source code runner trong IDE.
- `runner code ws <value>` — Mở một working workspace thiết lập sẵn. VD: `ptb` (Photobooth) hoặc `tool` (GDrive Tool).
- `runner code test` — Mở thư mục Testing sandbox.
- `runner code ts-template` — Mở template Express TypeScript.
- `runner code js` / `ts` / `py` — Mở các thư mục testing riêng lẻ của ngôn ngữ tương ứng.
- `runner code nestjs` — Mở NestJS template.
- `runner code ext` — Mở thư mục Browser Extensions.

### 3. TYPE `git` - Thao tác Version Control

- `runner git commit -m "<msg>"` — Tự động mở thread tab: `git add .`, `commit`, và `push`.

### 4. TYPE `run` - Thực thi Script tiện ích

- `runner run test-bat` — Chạy thử batch script nội bộ.
- `runner run unikey` — Khởi động UniKey (với path cứng cài đặt).
- `runner run cr-files` — Giao diện Interactive Tự tạo file dựa trên text templates.
- `runner run dld-path [<folder>]` — Đặt lại Download Path an toàn cho tất cả Profile Chrome.
- `runner run fm-sub <path.txt>` — Convert file sub dạng text sang `.srt`.
- `runner run proms` — Kích hoạt script chỉnh sửa prompts.
- `runner run rn-files <folder> [<prefix>]` — **Đổi tên hàng loạt**: Đổi sạch file cấp 1 thành `<prefix>-[N].ext`.
- `runner run del-files <folder> <ext1,ext2>` — **Dọn dẹp nâng cao**: Del sạch file có các extension được chỉ định.
- `runner run keep-files <folder> <ext>` — **Filter bảo vệ**: Chỉ giữ lại file có đuôi `ext`, xóa phần còn lại.

### 5. TYPE `print` - In Info

- `runner print os` — In nhanh OS Information & Hardware Data (CPU, Ram, Bios, IPs).
- `runner print stts` — In các runner Status code description.
- `runner print ws` — Liệt kê tên toàn bộ các file VSCode Workspaces.
- `runner print curl` — Bảng tra cứu mẫu mã cURL (CRUD).
- `runner print cmds` — Liệt kê Cheat-sheet list lệnh hữu ích liên quan.

### 6. SCRIPTS Tiện ích Độc lập (Chạy tay / ngoài Runner Tool)

_Không gọi bằng cờ `runner`, đây là các tools độc lập được tích hợp trong source._

- **Generate YouTube Sub (`useful-codes/sub-youtube-video/gen_sub_file.py`)**: Crawler hút sub tiếng anh YouTube, sau đó dịch chunks song ngữ sang Vietnamese qua Gemini API và compose thành `.srt`.
- **PNG to SVG Converter (`useful-codes/convert_png_to_svg.py`)**: Số hoá trace raster image thành vector curves bằng thư viện `vtracer`. Cấu hình cực mạnh về spline/corners.

---

## 🎯 Ví dụ Trực quan

```bash
# Xem mô tả xem lệnh "rn-files" này làm gì
runner run rn-files --des

# Xoá tất cả file .tmp và .log trong folder Downloads
runner run del-files "D:/D-Downloads/Trash" "tmp,log"

# Mở workspace Photobooth thông qua Antigravity IDE thay vì VSCode
runner code ws ptb -a

# Lưu code đang dở và push thẳng lên repo chỉ với 1 lệnh
runner git commit -m "feat: handle config variables"

# Print OS spec (hữu ích khi cần share logs)
runner print os
```

---

_Tài liệu tự động hóa - Cập nhật lần cuối: 2026-03-31_
