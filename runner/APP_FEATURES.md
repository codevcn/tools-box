# APP FEATURES — Runner Tool

> Cập nhật: 2026-03-31  
> Cú pháp chung: `runner [<type> <action> [<value> [<extra>]]] [-m "message"] [-a] [-p]`

---

## FLAGS TOÀN CỤC

| Flag                      | Mô tả                                                 |
| ------------------------- | ----------------------------------------------------- |
| `-h`, `--help`            | In help ra terminal                                   |
| `-m`, `--message`         | Truyền message cho script ngoài (dùng cho git commit) |
| `-a`, `--antigravity-IDE` | Dùng Antigravity IDE thay vì VSCode                   |
| `-p`, `--powershell-only` | Chỉ mở folder trong Windows Terminal, không mở IDE    |

---

## TYPE: `open` — Mở trong System Explorer

### #01 — Mở runner files trong VSCode

- **Lệnh:** `runner open`
- **Tóm tắt:** Mở thư mục gốc của runner project trong IDE.
- **Chi tiết:** Chạy `code <RUNNER_ROOT_FOLDER>` hoặc `anti <RUNNER_ROOT_FOLDER>` tùy theo flag `-a`.
- **Điều kiện:** Không có điều kiện đặc biệt.

---

### #02 — Mở VSCode Workspaces trong System Explorer

- **Lệnh:** `runner open ws`
- **Tóm tắt:** Mở thư mục chứa các VSCode workspace trong File Explorer.
- **Chi tiết:** Chạy `start D:/D-Documents/VSCode-Workspaces`.
- **Điều kiện:** Thư mục `D:/D-Documents/VSCode-Workspaces` phải tồn tại.

---

### #03 — Mở Environment Variables Panel

- **Lệnh:** `runner open env`
- **Tóm tắt:** Mở panel Environment Variables của Windows.
- **Chi tiết:** Chạy `rundll32.exe sysdm.cpl,EditEnvironmentVariables`.
- **Điều kiện:** Chỉ hoạt động trên Windows.

---

### #04 — Mở Prompts Folder

- **Lệnh:** `runner open proms`
- **Tóm tắt:** Mở thư mục Prompts của Template Replacer Extension trong File Explorer.
- **Chi tiết:** Chạy `start <TEMPLATE_REPLACER_FOLDER_PATH>/Prompts`.
- **Điều kiện:** Biến môi trường `TEMPLATE_REPLACER_FOLDER_PATH` phải được cấu hình trong `.env`.

---

## TYPE: `code` — Mở trong IDE

### #05 — Mở runner files trong IDE

- **Lệnh:** `runner code`
- **Tóm tắt:** Mở thư mục gốc của runner project trong IDE.
- **Chi tiết:** Chạy `code <RUNNER_ROOT_FOLDER>` hoặc `anti ...` tùy flag `-a`.
- **Điều kiện:** Không có điều kiện đặc biệt.

---

### #06 — Mở Working Workspace

- **Lệnh:** `runner code ws <value>`
- **Tóm tắt:** Mở một working workspace cụ thể trong IDE và terminal.
- **Chi tiết:** Gọi `runner_main_ws.py` với `<value>`:
  - `ptb` → Mở Photobooth project: mở terminal tabs cho `ptm` + `recover-image`, mở IDE, mở Chrome với `localhost:3000` và các tab AI.
  - `tool` → Mở gdrive-tool project: mở terminal tab cho `sync-with-gdrive`, mở IDE, mở Chrome với tab AI.
- **Điều kiện:** `<value>` phải là `ptb` hoặc `tool`. Cần Chrome và Windows Terminal (`wt`) đã cài.

---

### #07 — Mở Testing Folder

- **Lệnh:** `runner code test`
- **Tóm tắt:** Mở thư mục Testing chung trong IDE.
- **Chi tiết:** Chạy `code D:/D-Documents/Testing`.
- **Điều kiện:** Không có điều kiện đặc biệt.

---

### #08 — Mở TypeScript Template

- **Lệnh:** `runner code ts-template`
- **Tóm tắt:** Mở thư mục template Express server TypeScript trong IDE.
- **Chi tiết:** Chạy `code D:/D-Documents/Templates/standard-express-server-ts`.
- **Điều kiện:** Thư mục template phải tồn tại.

---

### #09 — Mở Testing JS/TS Folder

- **Lệnh:** `runner code js` hoặc `runner code ts`
- **Tóm tắt:** Mở thư mục testing JavaScript/TypeScript trong IDE.
- **Chi tiết:** Chạy `code D:/D-Documents/Testing/js-ts`.
- **Điều kiện:** Không có điều kiện đặc biệt.

---

### #10 — Mở NestJS Template

- **Lệnh:** `runner code nestjs`
- **Tóm tắt:** Mở thư mục NestJS template trong IDE.
- **Chi tiết:** Chạy `code D:/D-Documents/Code_VCN/nestjs`.
- **Điều kiện:** Không có điều kiện đặc biệt.

---

### #11 — Mở Testing Python Folder

- **Lệnh:** `runner code py`
- **Tóm tắt:** Mở thư mục testing Python trong IDE.
- **Chi tiết:** Chạy `code D:/D-Documents/Testing/py`.
- **Điều kiện:** Không có điều kiện đặc biệt.

---

### #12 — Mở Browser Extensions Folder

- **Lệnh:** `runner code ext`
- **Tóm tắt:** Mở thư mục chứa các browser extension trong IDE.
- **Chi tiết:** Chạy `code D:/D-Documents/Browser-Extensions`.
- **Điều kiện:** Không có điều kiện đặc biệt.

---

## TYPE: `git` — Thao tác Git

### #13 — Git Commit & Push

- **Lệnh:** `runner git commit -m "message"`
- **Tóm tắt:** Tự động `git add .`, `git commit`, `git push` trong một terminal mới.
- **Chi tiết:** Mở Windows Terminal tab mới (dùng `wt nt`) tại thư mục `RUNNER_ROOT_FOLDER`, chạy `git add . && git commit -m "..." && git push origin main`.
- **Điều kiện:** Flag `-m "message"` là bắt buộc. Cần `git` và Windows Terminal (`wt`) đã cài. Repo phải đã có remote `origin`.

---

## TYPE: `run` — Thực thi script

### #14 — Chạy Test Batch File

- **Lệnh:** `runner run test-bat`
- **Tóm tắt:** Chạy file batch test (`runner_test.py`).
- **Chi tiết:** Gọi `python runner_test.py`.
- **Điều kiện:** File `runner_test.py` phải tồn tại trong thư mục src.

---

### #15 — Chạy UniKey

- **Lệnh:** `runner run unikey`
- **Tóm tắt:** Khởi động ứng dụng gõ tiếng Việt UniKey.
- **Chi tiết:** Chạy `start C:/Users/dell/Downloads/UniKeyNT.exe`.
- **Điều kiện:** File `UniKeyNT.exe` phải tồn tại tại đường dẫn cứng trong code.

---

### #16 — Tạo Files từ Template

- **Lệnh:** `runner run cr-files`
- **Tóm tắt:** Tạo file/folder từ danh sách template định nghĩa sẵn trong `files_source.txt`.
- **Chi tiết:**
  - Đọc file `contents/files_source.txt` theo cú pháp `@@file-name[[name]]{{filename}} @@file-content{{content}}`.
  - Hiển thị menu cho người dùng chọn (nhập số, cách nhau bởi dấu cách).
  - Tạo file/folder tại thư mục **hiện tại của terminal** (`os.getcwd()`).
  - Hỗ trợ tạo nested folder tự động.
- **Điều kiện:** File `contents/files_source.txt` phải tồn tại và có đúng cú pháp template. Script chạy **interactive** (cần input từ người dùng).

---

### #17 — Đặt Download Path trong Chrome

- **Lệnh:** `runner run dld-path [<folder_name>]`
- **Tóm tắt:** Thay đổi thư mục download mặc định của Chrome cho tất cả profile.
- **Chi tiết:**
  - Nếu có `<folder_name>`: tạo folder `D:/D-Downloads/<folder_name>` và set làm download dir.
  - Nếu không có: tự động tạo folder `D:/D-Downloads/download-{N}` với N tăng dần.
  - Backup file `Preferences` của từng Chrome profile trước khi ghi (định dạng `.bak.YYYYMMDD-HHMMSS`).
  - Cập nhật `download.default_directory` trong `Preferences` JSON của **tất cả** Chrome profile (`Default` và `Profile N`).
- **Điều kiện:** ⚠️ **Chrome phải được tắt hoàn toàn** trước khi chạy (script tự kiểm tra `chrome.exe` trong `tasklist` và cảnh báo nếu Chrome đang chạy). Chrome User Data phải tồn tại tại `C:/Users/dell/AppData/Local/Google/Chrome/User Data`.

---

### #18 — Format Subtitle TXT → SRT

- **Lệnh:** `runner run fm-sub <value>`
- **Tóm tắt:** Chuyển đổi file phụ đề định dạng TXT sang SRT.
- **Chi tiết:** Gọi `sub-youtube-video/format_subtitle_txt_to_srt.py` với `<value>` là đường dẫn file.
- **Điều kiện:** `<value>` (đường dẫn file TXT) là bắt buộc.

---

### #19 — Edit Prompts

- **Lệnh:** `runner run proms`
- **Tóm tắt:** Mở thư mục prompts của Template Replacer Extension bằng lệnh batch.
- **Chi tiết:** Chạy file `edit-prompts.cmd` trong `TEMPLATE_REPLACER_FOLDER_PATH`.
- **Điều kiện:** Biến môi trường `TEMPLATE_REPLACER_FOLDER_PATH` phải được cấu hình. File `edit-prompts.cmd` phải tồn tại.

---

### #20 — Rename Files

- **Lệnh:** `runner run rn-files <folder_path> [<prefix>]`
- **Tóm tắt:** Đổi tên toàn bộ file trong folder theo dạng `<prefix>-1.ext`, `<prefix>-2.ext`, ...
- **Chi tiết:**
  - **Bước 1 - Xác định prefix:**
    - Nếu `<prefix>` được cung cấp và không rỗng: dùng trực tiếp.
    - Nếu `<prefix>` rỗng hoặc không có: tự động phát hiện từ các file có dạng `<prefix>-<number>.<ext>`. Yêu cầu **ít nhất 2 file** cùng pattern. Nếu có nhiều prefix valid → chọn cái có nhiều file nhất.
    - Nếu không detect được: báo lỗi và thoát.
  - **Bước 2 - Đổi tên 2 giai đoạn:** Đổi sang tên tạm `__tmp_N__` trước, sau đó đổi sang tên đích (tránh conflict khi đặt tên trùng).
  - Chỉ xử lý file cấp 1 (không đệ quy vào thư mục con).
  - File được sort trước khi đổi tên để đảm bảo thứ tự nhất quán.
- **Điều kiện:** `<folder_path>` phải là thư mục hợp lệ. Nếu không truyền prefix thì folder phải có ít nhất 2 file khớp pattern `<prefix>-<number>.<ext>`.

---

### #21 — Delete Files by Extensions

- **Lệnh:** `runner run del-files <folder_path> <ext1,ext2,...>`
- **Tóm tắt:** Xóa tất cả file có extension nằm trong danh sách chỉ định.
- **Chi tiết:**
  - Nhận vào một chuỗi extension ngăn cách bởi dấu phẩy (vd: `"txt,jpg,png"`).
  - Lặp qua từng extension, chuẩn hóa (strip dấu chấm, lowercase), glob toàn bộ file khớp và xóa.
  - In `[DELETED]` hoặc `[FAILED]` cho từng file. Tổng kết ở cuối.
  - Chỉ xử lý file cấp 1 trong folder (không đệ quy).
- **Điều kiện:** `<folder_path>` phải là thư mục hợp lệ và tồn tại. Cả 2 tham số đều bắt buộc.

---

### #22 — Keep Files by Extension (Xóa file không khớp)

- **Lệnh:** `runner run keep-files <folder_path> <ext>`
- **Tóm tắt:** Giữ lại chỉ các file có extension chỉ định, xóa toàn bộ file còn lại trong folder.
- **Chi tiết:**
  - Nhận 1 extension duy nhất (vd: `"png"`).
  - Liệt kê tất cả file trong folder, lọc ra những file **không** có extension đó và xóa.
  - In `[DELETED]` hoặc `[FAILED]` cho từng file. Tổng kết số file xóa / thất bại / giữ lại.
  - Chỉ xử lý file cấp 1 (không đệ quy).
- **Điều kiện:** `<folder_path>` phải là thư mục hợp lệ. Cả 2 tham số đều bắt buộc. Chỉ nhận **1 extension** (khác với `del-files` nhận nhiều).

---

## TYPE: `print` — In thông tin

### #23 — In OS Info

- **Lệnh:** `runner print os`
- **Tóm tắt:** In thông tin hệ thống của máy tính.
- **Chi tiết:** Chạy `systeminfo`, `wmic cpu get name`, `ipconfig` và lọc ra các thông tin quan trọng:
  - OS Name, OS Version, System Manufacturer, System Model
  - System Type (BIOS)
  - Total/Available Physical Memory, Virtual Memory
  - CPU Name
  - IPv4/IPv6 addresses
- **Điều kiện:** Chỉ hoạt động trên Windows (dùng `systeminfo`, `wmic`, `ipconfig`).

---

### #24 — In Runner Statuses Info

- **Lệnh:** `runner print stts`
- **Tóm tắt:** In mô tả các runner status code.
- **Chi tiết:** Đọc và in file `contents/statuses.txt`.
- **Điều kiện:** File `contents/statuses.txt` phải tồn tại. Biến `CONTENTS_FOLDER_PATH` phải được cấu hình.

---

### #25 — In VSCode Workspaces

- **Lệnh:** `runner print ws`
- **Tóm tắt:** In danh sách các VSCode workspace file trong thư mục Workspaces.
- **Chi tiết:** Gọi `useful-codes/print_vcnbat_folder.py` với đường dẫn `D:/D-Documents/VSCode-Workspaces`.
- **Điều kiện:** Thư mục `D:/D-Documents/VSCode-Workspaces` phải tồn tại.

---

### #26 — In cURL Reference

- **Lệnh:** `runner print curl`
- **Tóm tắt:** In tài liệu tham chiếu cú pháp cURL (CRUD).
- **Chi tiết:** Đọc và in file `contents/cURL.txt`.
- **Điều kiện:** File `contents/cURL.txt` phải tồn tại. Biến `CONTENTS_FOLDER_PATH` phải được cấu hình.

---

### #27 — In Runner Directory Path

- **Lệnh:** `runner print dir`
- **Tóm tắt:** In đường dẫn tuyệt đối của thư mục runner src.
- **Chi tiết:** Gọi `os.path.dirname(os.path.abspath(__file__))` và in ra terminal.
- **Điều kiện:** Không có điều kiện đặc biệt.

---

### #28 — In Useful Commands

- **Lệnh:** `runner print cmds`
- **Tóm tắt:** In danh sách các lệnh hữu ích thường dùng.
- **Chi tiết:** Đọc và in file `contents/list-useful-commands.txt`.
- **Điều kiện:** File `contents/list-useful-commands.txt` phải tồn tại. Biến `CONTENTS_FOLDER_PATH` phải được cấu hình.

---

### #29 — In Help

- **Lệnh:** `runner` (không có tham số) hoặc `runner -h`
- **Tóm tắt:** In hướng dẫn sử dụng runner tool.
- **Chi tiết:** Đọc và in file `contents/help.txt`.
- **Điều kiện:** File `contents/help.txt` phải tồn tại.

---

## SCRIPTS ĐỘC LẬP (không qua runner CLI)

### #30 — Generate YouTube Subtitle (SRT)

- **File:** `useful-codes/sub-youtube-video/gen_sub_file.py`
- **Tóm tắt:** Tải phụ đề tiếng Anh từ YouTube và dịch sang tiếng Việt bằng Gemini AI, xuất file `.srt`.
- **Chi tiết:**
  - Đọc YouTube link từ file `input/video_config.txt` (key `youtube_video_link`).
  - Dùng `youtube_transcript_api` để fetch phụ đề tiếng Anh.
  - Tóm tắt nội dung video qua Gemini (đọc từ `input/video_summary.md` nếu đã có, gọi API nếu chưa).
  - Chia phụ đề thành các chunk (`TRANSLATE_CHUNK_SIZE`), dịch từng chunk qua Gemini API.
  - Retry tự động (tối đa 3 lần) với delay đọc từ error message khi bị rate limit.
  - Nếu chunk thất bại: fallback giữ nguyên text tiếng Anh.
  - Xuất file SRT ra `result/vietsub_<video_id>.srt`.
- **Điều kiện:** Biến môi trường `GEMINI_API_KEY`, `GEMINI_MODEL`, `TRANSLATE_CHUNK_SIZE` phải được cấu hình. Video YouTube phải có phụ đề tiếng Anh. Cần thư viện `youtube_transcript_api`, `google-genai`.

---

### #31 — Convert PNG to SVG

- **File:** `useful-codes/convert_png_to_svg.py`
- **Tóm tắt:** Chuyển đổi ảnh PNG sang SVG vector bằng thư viện `vtracer`.
- **Chi tiết:**
  - Input: `input.png` (cứng trong code, cùng thư mục).
  - Output: `output.svg` (cùng thư mục).
  - Dùng mode `spline` + `color` để tạo SVG nhiều màu, đường cong mềm.
  - Các tham số: `filter_speckle=4`, `color_precision=6`, `layer_difference=16`, `corner_threshold=60`, `max_iterations=10`.
- **Điều kiện:** Thư viện `vtracer` phải được cài (`pip install vtracer`). File `input.png` phải tồn tại cùng thư mục với script.

---

## CẤU HÌNH (`.env` file)

| Biến                            | Mô tả                                              |
| ------------------------------- | -------------------------------------------------- |
| `ROOT_FOLDER_PATH`              | Đường dẫn gốc của runner project                   |
| `USEFUL_CODES_FOLDER_PATH`      | Đường dẫn đến thư mục `useful-codes`               |
| `CONTENTS_FOLDER_PATH`          | Đường dẫn đến thư mục `contents`                   |
| `TEMPLATE_REPLACER_FOLDER_PATH` | Đường dẫn đến extension Template Replacer          |
| `GEMINI_API_KEY`                | API key của Google Gemini (cho subtitle generator) |
| `GEMINI_MODEL`                  | Tên model Gemini sử dụng                           |
| `TRANSLATE_CHUNK_SIZE`          | Số dòng phụ đề mỗi lần gửi API                     |
