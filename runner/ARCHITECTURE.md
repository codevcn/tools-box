# Kiến trúc Code: `src/runner.py`

> **Project:** Runner Tool — công cụ CLI tự động hóa tác vụ phát triển trên Windows  
> **File phân tích:** `src/runner.py` (584 dòng)  
> **Entry point:** `runner.cmd` → gọi `py .../src/runner.py %*`

---

## 1. Tổng quan

`runner.py` là **trung tâm điều phối** (dispatcher) của toàn bộ tool. Nó nhận lệnh từ CLI của người dùng, phân tích cú pháp các tham số, rồi **ủy thác** (delegate) việc thực thi sang các script con tương ứng thông qua `subprocess.run()`. Bản thân file này **không chứa logic nghiệp vụ** — nó chỉ định tuyến (route) lệnh đến đúng handler.

```
người dùng gõ lệnh
        │
        ▼
  runner.cmd  (entry point)
        │  py runner.py <args>
        ▼
  src/runner.py  ◄── file phân tích này
    ├── parse args (argparse)
    ├── resolve IDE prefix
    └── dispatch → hàm handler
              │
              ▼
    subprocess.run(<script hoặc lệnh hệ thống>)
```

---

## 2. Cấu trúc tổng thể của file

```
runner.py
│
├── [L1–8]    Imports & load .env
├── [L9–70]   Hằng số (Constants)
│   ├── RUNNER_TYPE_*       (7 type)
│   ├── RUNNER_*_ACTION_*   (actions cho mỗi type)
│   ├── RUNNER_FLAG_*       (flag names)
│   └── RUNNER_WARNING_*    (mã cảnh báo lỗi)
├── [L71–75]  Biến môi trường (từ .env)
├── [L79–381] Các hàm handler
└── [L383–583] Khối __main__ (dispatcher chính)
    ├── [L387–453] Định nghĩa argparse
    ├── [L455–468] Giải ánh xạ args
    └── [L471–577] Logic phân nhánh if/elif
```

---

## 3. Hệ thống hằng số (Constants)

### 3.1 — Runner Types (7 loại lệnh chính)

| Hằng số              | Giá trị    | Ý nghĩa                               |
| -------------------- | ---------- | ------------------------------------- |
| `RUNNER_TYPE_OPEN`   | `"open"`   | Mở file/thư mục trong System Explorer |
| `RUNNER_TYPE_CODE`   | `"code"`   | Mở dự án trong IDE                    |
| `RUNNER_TYPE_RUN`    | `"run"`    | Thực thi script/ứng dụng              |
| `RUNNER_TYPE_PRINT`  | `"print"`  | In thông tin ra terminal              |
| `RUNNER_TYPE_GIT`    | `"git"`    | Thực hiện thao tác Git                |
| `RUNNER_TYPE_GDRIVE` | `"gdrive"` | Thao tác với Google Drive qua rclone  |
| `RUNNER_TYPE_INIT`   | `"init"`   | Khởi tạo môi trường                   |
| `RUNNER_TYPE_PY`     | `"py"`     | Công cụ cho Python                    |

### 3.2 — Actions theo từng Type

**`open` actions:**
| Hằng số | Giá trị | Lệnh |
|---|---|---|
| `RUNNER_OPEN_ENV` | `"env"` | `runner open env` |
| `RUNNER_OPEN_PROMPTS_FOLDER` | `"proms"` | `runner open proms` |

**`code` actions:**
| Hằng số | Giá trị | Lệnh |
|---|---|---|
| `RUNNER_CODE_VSCODE_WORKSPACE` | `"ws"` | `runner code ws <value>` |
| `RUNNER_CODE_TEST` | `"test"` | `runner code test` |
| `RUNNER_CODE_TYPESCRIPT_TEMPLATE` | `"ts-template"` | `runner code ts-template` |
| `RUNNER_CODE_JS` | `"js"` | `runner code js` |
| `RUNNER_CODE_TS` | `"ts"` | `runner code ts` |
| `RUNNER_CODE_NESTJS` | `"nestjs"` | `runner code nestjs` |
| `RUNNER_CODE_PY` | `"py"` | `runner code py` |
| `RUNNER_CODE_EXTENSIONS` | `"ext"` | `runner code ext` |

**`run` actions:**
| Hằng số | Giá trị | Lệnh |
|---|---|---|
| `RUNNER_RUN_TEST_BAT` | `"test-bat"` | `runner run test-bat` |
| `RUNNER_RUN_UNIKEY_APP` | `"unikey"` | `runner run unikey` |
| `RUNNER_RUN_CREATE_FILES_IN_FOLDER` | `"cr-files"` | `runner run cr-files` |
| `RUNNER_RUN_SET_DOWNLOAD_PATH_IN_CHROME` | `"dld-path"` | `runner run dld-path [<folder>]` |
| `RUNNER_FORMAT_SUBTITLE_TXT_TO_SRT` | `"fm-sub"` | `runner run fm-sub <value>` |
| `RUNNER_EDIT_PROMPTS` | `"proms"` | `runner run proms` |
| `RUNNER_RENAME_FILES` | `"rn-files"` | `runner run rn-files <path> [<prefix>]` |
| `RUNNER_DELETE_FILES` | `"del-files"` | `runner run del-files <path> <exts>` |
| `RUNNER_KEEP_FILES` | `"keep-files"` | `runner run keep-files <path> <ext>` |

**`git` actions:**
| Hằng số | Giá trị | Lệnh |
|---|---|---|
| `RUNNER_GIT_COMMIT_AND_PUSH` | `"commit"` | `runner git commit -m "message"` |

**`print` actions:**
| Hằng số | Giá trị | Lệnh |
|---|---|---|
| `RUNNER_PRINT_OS_INFO` | `"os"` | `runner print os` |
| `RUNNER_PRINT_STATUSES_INFO` | `"stts"` | `runner print stts` |
| `RUNNER_PRINT_VSCODE_WORKSPACES` | `"ws"` | `runner print ws` |
| `RUNNER_PRINT_CURL` | `"curl"` | `runner print curl` |
| `RUNNER_PRINT_DIRECTORY` | `"dir"` | `runner print dir` |
| `RUNNER_PRINT_USEFUL_COMMANDS` | `"cmds"` | `runner print cmds` |

### 3.3 — Warning Codes (mã lỗi nội bộ)

```python
RUNNER_WARNING_TYPE_WRONG    = "WRONG-TYPE"      # Type không tồn tại
RUNNER_WARNING_TYPE_MISSING  = "MISSING-TYPE"    # Thiếu type
RUNNER_WARNING_ACTION_WRONG  = "WRONG-ACTION"    # Action không tồn tại
RUNNER_WARNING_ACTION_MISSING= "MISSING-ACTION"  # Thiếu action
RUNNER_WARNING_FLAG_WRONG    = "WRONG-FLAG"      # Flag không hợp lệ
RUNNER_WARNING_FLAG_MISSING  = "MISSING-FLAG"    # Thiếu flag
```

### 3.4 — Biến môi trường (đọc từ `.env`)

| Biến                            | Mục đích                                         |
| ------------------------------- | ------------------------------------------------ |
| `ROOT_FOLDER_PATH`              | Đường dẫn gốc của runner project                 |
| `USEFUL_CODES_FOLDER_PATH`      | Đường dẫn đến `src/useful-codes/`                |
| `CONTENTS_FOLDER_PATH`          | Đường dẫn đến `src/contents/`                    |
| `TEMPLATE_REPLACER_FOLDER_PATH` | Đường dẫn đến VSCode Extension Template Replacer |

---

## 4. Các hàm Handler

Tất cả các hàm handler đều theo cùng một pattern:

1. Xây dựng `cmd_args` list
2. Gọi `subprocess.run()` hoặc lệnh hệ thống
3. Kết thúc bằng `sys.exit(0)`

### 4.1 — Nhóm `gdrive`

#### `gdrive_execute(gdrive_command, *args)` — L79

```
Mục đích : Ủy thác toàn bộ logic gdrive cho script sync_to_gdrive.py
Script   : useful-codes/sync-to-gdrive/sync_to_gdrive.py
Args     : gdrive_command (action) + value + extra + flags (-d, --file)
```

### 4.2 — Nhóm `print` (in nội dung ra terminal)

#### `print_content(content_filename)` — L96

```
Mục đích : Script lõi để in bất kỳ file .txt nào trong thư mục contents/
Script   : system-codes/runner_print_content.py
Dùng bởi : print_help(), print_useful_commands()
```

#### `print_help()` — L163

```
In : contents/help.txt
```

#### `print_useful_commands()` — L130

```
In : contents/list_useful_commands.txt
```

#### `print_cURL()` — L167

```
Script : useful-codes/runner_cURL.py
In     : contents/cURL.txt
```

#### `print_os_info()` — L242

```
Script : useful-codes/runner_os_info.py
In     : systeminfo, wmic cpu, ipconfig (Windows only)
```

#### `print_statuses_info()` — L154

```
Script : system-codes/runner_statuses.py
In     : contents/statuses.txt
```

#### `print_vscode_workspaces(workspace_path)` — L211

```
Script : useful-codes/print_runner_folder.py
In     : danh sách .code-workspace files
```

#### `print_runner_files_root_dir()` — L125

```
In trực tiếp : os.path.dirname(os.path.abspath(__file__))
```

### 4.3 — Nhóm `open` (mở thư mục/ứng dụng)

#### `open_environment_variables_panel()` — L176

```
Lệnh : rundll32.exe sysdm.cpl,EditEnvironmentVariables
```

#### `open_prompts_folder()` — L181

```
Lệnh : start <TEMPLATE_REPLACER_FOLDER_PATH>/Prompts
```

#### `open_vscode_workspaces_in_system_folder()` — L186

```
Lệnh : start D:/D-Documents/VSCode-Workspaces
```

#### `open_runner_file_in_system_folder()` — L149

```
Lệnh : start <RUNNER_ROOT_FOLDER>
```

### 4.4 — Nhóm `code` (mở trong IDE)

Tất cả các hàm code đều nhận `ide_prefix` (giá trị là `"code"` hoặc `"anti"`) để hỗ trợ cả VSCode lẫn Antigravity IDE.

#### `open_working_vscode(ide_prefix, value, powershell_only)` — L191

```
Script : useful-codes/runner_main_ws.py
Value  : "ptb" → Photobooth project
         "tool" → GDrive tool project
Chức năng: Mở terminal tabs + IDE + Chrome tabs theo workspace preset
```

#### `open_runner_files_in_vscode(ide_prefix)` — L223

```
Lệnh : <ide_prefix> <RUNNER_ROOT_FOLDER>
```

#### `open_testing_folder_in_vscode(ide_prefix)` — L120

```
Lệnh : <ide_prefix> D:/D-Documents/Testing
```

#### `open_testing_javascript_typescript_folder_in_vscode(ide_prefix)` — L263

```
Lệnh : <ide_prefix> D:/D-Documents/Testing/js-ts
```

#### `open_testing_python_folder_in_vscode(ide_prefix)` — L268

```
Lệnh : <ide_prefix> D:/D-Documents/Testing/py
```

#### `open_typescript_template_in_cursor(ide_prefix)` — L256

```
Lệnh : <ide_prefix> D:/D-Documents/Templates/standard-express-server-ts
```

#### `open_template_nestjs_folder_in_vscode(ide_prefix)` — L228

```
Lệnh : <ide_prefix> D:/D-Documents/Code_VCN/nestjs
```

#### `open_vscode_extensions_in_vscode(ide_prefix)` — L109

```
Lệnh : <ide_prefix> D:/D-Documents/Browser-Extensions
```

### 4.5 — Nhóm `git`

#### `run_git_command(git_type, user_message)` — L134

```
Script : system-codes/runner_git.py
Hỗ trợ: "commit" → mở Windows Terminal tab mới, chạy:
         git add . && git commit -m "..." && git push origin main
```

### 4.6 — Nhóm `run` (thực thi script)

#### `run_test_bat(*args)` — L233

```
Script : src/runner_test.py (test file)
```

#### `run_Unikey_app()` — L251

```
Lệnh : start C:/Users/dell/Downloads/UniKeyNT.exe
```

#### `create_files_in_folder()` — L273

```
Script : useful-codes/create_files_in_folder.py
Dùng   : contents/files_source.txt làm template
```

#### `set_download_path_in_chrome(folder_name)` — L281

```
Script : useful-codes/set_download_path_in_chrome.py
Params : folder_name (tùy chọn)
```

#### `convert_txt_to_srt(value)` — L292

```
Script : useful-codes/sub-youtube-video/format_subtitle_txt_to_srt.py
Params : value = đường dẫn file .txt
```

#### `edit_prompts()` — L304

```
Script : <TEMPLATE_REPLACER_FOLDER_PATH>/edit-prompts.cmd
```

#### `rename_files(folder_path, prefix)` — L312

```
Script : useful-codes/rename_files.py
Params : folder_path (bắt buộc), prefix (tùy chọn)
```

#### `delete_files(folder_path, ext_list)` — L325

```
Script : useful-codes/delete_files.py
Params : folder_path, ext_list (vd: "txt,jpg,png")
```

#### `keep_files(folder_path, ext)` — L338

```
Script : useful-codes/keep_files_with_ext.py
Params : folder_path, ext (1 extension duy nhất)
```

### 4.7 — Nhóm tiện ích / init

#### `print_feature_description(cmd_type, action)` — L351

```
Script : useful-codes/print_feature_description.py
Dùng   : contents/app_features.yml
Flag   : --des (có thể gắn vào bất kỳ lệnh nào)
```

#### `cmd_init()` — L365

```
Script : src/cmd/init.cmd
```

#### `py_setup_venv()` — L373

```
Script : useful-codes/setup_venv_in_project.py
```

#### `warn_user_error(warning_message)` — L114

```
Mục đích : In cảnh báo >>> Warn: <message> rồi sys.exit(0)
Dùng bởi : khối except cuối
```

---

## 5. Luồng Dispatcher (`__main__`)

### 5.1 — Sơ đồ luồng xử lý

```
argparse.parse_args()
        │
        ├─ --des?  ──► print_feature_description(type, action)
        │
        ├─ resolve ide_prefix:
        │     "-a" flag → "anti"
        │     default  → "code"
        │
        ├─ type == None  ──► print_help()
        │
        ├─ type == "py"
        │     action == "env"  ──► py_setup_venv()
        │     else             ──► raise MISSING-ACTION
        │
        ├─ type == "init"  ──► cmd_init()
        │
        ├─ type == "gdrive"
        │     build gdrive_args + flags (-d, --file)
        │     ──► gdrive_execute(action, *args)
        │
        ├─ type == "code"
        │     None          ──► open_runner_files_in_vscode
        │     "ws"          ──► open_working_vscode(ide, value, ps_only)
        │     "test"        ──► open_testing_folder_in_vscode
        │     "ts-template" ──► open_typescript_template_in_cursor
        │     "js"/"ts"     ──► open_testing_javascript_typescript_folder_in_vscode
        │     "nestjs"      ──► open_template_nestjs_folder_in_vscode
        │     "py"          ──► open_testing_python_folder_in_vscode
        │     "ext"         ──► open_vscode_extensions_in_vscode
        │     else          ──► raise WRONG-ACTION
        │
        ├─ type == "git"
        │     "commit" yêu cầu -m flag
        │     ──► run_git_command(action, message)
        │
        ├─ type == "run"
        │     "test-bat"    ──► run_test_bat()
        │     "unikey"      ──► run_Unikey_app()
        │     "cr-files"    ──► create_files_in_folder()
        │     "dld-path"    ──► set_download_path_in_chrome(value)
        │     "fm-sub"      ──► convert_txt_to_srt(value)
        │     "proms"       ──► edit_prompts()
        │     "rn-files"    ──► rename_files(value, extra)
        │     "del-files"   ──► delete_files(value, extra)
        │     "keep-files"  ──► keep_files(value, extra)
        │     None          ──► raise MISSING-ACTION
        │     else          ──► raise WRONG-ACTION
        │
        ├─ type == "open"
        │     None    ──► open_runner_files_in_vscode
        │     "env"   ──► open_environment_variables_panel()
        │     "proms" ──► open_prompts_folder()
        │     "ws"    ──► open_vscode_workspaces_in_system_folder()
        │     else    ──► raise WRONG-ACTION
        │
        ├─ type == "print"
        │     "os"    ──► print_os_info()
        │     "ws"    ──► print_vscode_workspaces(...)
        │     "dir"   ──► print_runner_files_root_dir()
        │     "cmds"  ──► print_useful_commands()
        │     "curl"  ──► print_cURL()
        │     "stts"  ──► print_statuses_info()
        │     None    ──► raise MISSING-ACTION
        │     else    ──► raise WRONG-ACTION
        │
        └─ else  ──► raise WRONG-TYPE
```

### 5.2 — CLI Arguments (argparse)

| Argument                 | Loại                  | Mô tả                                                     |
| ------------------------ | --------------------- | --------------------------------------------------------- |
| `type`                   | positional (optional) | Loại lệnh (open/code/run/print/git/gdrive/py)             |
| `action`                 | positional (optional) | Hành động cụ thể                                          |
| `value`                  | positional (optional) | Giá trị cho action (vd: tên workspace, đường dẫn thư mục) |
| `extra`                  | positional (optional) | Giá trị phụ (vd: prefix cho `rn-files`)                   |
| `-m / --message`         | optional              | Message cho git commit                                    |
| `-a / --antigravity-IDE` | flag                  | Dùng Antigravity IDE thay vì VSCode                       |
| `-p / --powershell-only` | flag                  | Chỉ mở PowerShell, không mở IDE                           |
| `--des`                  | flag                  | Xem mô tả feature từ `app_features.yml`                   |
| `-d / --deep`            | flag                  | Liệt kê đệ quy sâu (cho gdrive list)                      |
| `-f / --file`            | flag                  | Liệt kê file thay vì folder (cho gdrive list)             |

### 5.3 — IDE Prefix Resolution

```python
# Xác định IDE dùng để mở code
antigravity_included = args.antigravity_IDE  # True nếu có flag -a
default_ide_prefix = "anti" if antigravity_included else "code"
```

Logic này cho phép chạy cùng lệnh nhưng mở trong IDE khác nhau:

- `runner code ws ptb` → mở bằng VSCode (`code`)
- `runner code ws ptb -a` → mở bằng Antigravity IDE (`anti`)

### 5.4 — Xử lý lỗi

```python
try:
    # ...toàn bộ logic dispatch...
except KeyboardInterrupt:
    print(">>> Tiến trình đã bị hủy bởi người dùng (KeyboardInterrupt).")
    sys.exit(0)
except Exception as e:
    warn_user_error(str(e))  # in >>> Warn: <message>
    sys.exit(1)
```

Lỗi được raise qua `raise Exception(RUNNER_WARNING_*)` và được bắt ở cùng khối `try/except`.

---

## 6. Kiến trúc hệ thống file đầy đủ

```
runner/                             ← ROOT_FOLDER_PATH
├── .env                            ← Config biến môi trường
├── runner.cmd                      ← Entry point (gọi src/runner.py)
├── requirements.txt                ← python-dotenv, PyYAML
│
└── src/
    ├── runner.py                   ◄── FILE PHÂN TÍCH NÀY (dispatcher chính)
    │
    ├── cmd/
    │   └── init.cmd                ← Script batch khởi tạo môi trường
    │
    ├── contents/                   ← Nội dung tĩnh in ra terminal
    │   ├── app_features.yml        ← Mô tả đầy đủ tất cả features (29+ actions)
    │   ├── help.txt                ← Hướng dẫn sử dụng
    │   ├── list_useful_commands.txt← Danh sách lệnh hữu ích
    │   ├── cURL.txt                ← Tham chiếu cú pháp cURL
    │   ├── files_source.txt        ← Template tạo file
    │   └── statuses.txt            ← Mô tả các status code
    │
    ├── system-codes/               ← Scripts hệ thống nội bộ
    │   ├── runner_git.py           ← Thực thi git commit/push qua Windows Terminal
    │   ├── runner_print_content.py ← Đọc và in file từ contents/
    │   └── runner_statuses.py      ← In statuses.txt
    │
    └── useful-codes/               ← Scripts tiện ích mở rộng
        ├── runner_main_ws.py       ← Mở workspace environment phức tạp
        ├── runner_os_info.py       ← Thu thập thông tin hệ thống Windows
        ├── runner_cURL.py          ← In cURL reference
        ├── print_feature_description.py ← Parse app_features.yml và in ra
        ├── print_vcnbat_folder.py  ← In danh sách workspace files
        ├── create_files_in_folder.py ← Tạo file từ template
        ├── set_download_path_in_chrome.py ← Cấu hình Chrome download path
        ├── rename_files.py         ← Đổi tên file hàng loạt
        ├── delete_files.py         ← Xóa file theo extension
        ├── keep_files_with_ext.py  ← Giữ file theo extension
        ├── setup_venv_in_project.py ← Cài đặt Python venv
        ├── convert_png_to_svg.py   ← Chuyển đổi định dạng ảnh
        └── sync-to-gdrive/
            └── sync_to_gdrive.py   ← Đồng bộ GDrive qua rclone
```

---

## 7. Design Patterns và Nguyên tắc

### Pattern 1: Dispatcher / Command Router

`runner.py` triển khai pattern **Command Router** — nhận input, phân tích, rồi gọi hàm tương ứng. Không có logic nghiệp vụ nào nằm trong file này.

### Pattern 2: Subprocess Delegation

Mọi tác vụ thực sự đều được thực hiện bởi subprocess riêng biệt. Điều này giúp:

- Tách bạch trách nhiệm (Separation of Concerns)
- Dễ dàng thêm script mới mà không sửa dispatcher
- Script con có thể chạy độc lập

### Pattern 3: Constants-Driven Routing

Toàn bộ routing dùng string constants thay vì hardcode string literal trong if/elif, giúp tránh typo và dễ refactor.

### Pattern 4: Always Exit

Mọi hàm handler đều kết thúc bằng `sys.exit(0)`. Nếu code "lọt" qua tất cả nhánh mà không exit, `RUNNER_STATUS` được set thành `"OUT-OF-MAIN-SECTION"` và exit code là 1.

---

## 8. Luồng thực thi ví dụ

### Ví dụ 1: `runner git commit -m "fix bug"`

```
runner.cmd
  → py runner.py git commit -m "fix bug"
  → argparse: type="git", action="commit", user_message="fix bug"
  → type == RUNNER_TYPE_GIT
  → action == RUNNER_GIT_COMMIT_AND_PUSH ✓
  → user_message = "fix bug" ✓ (không raise exception)
  → run_git_command("commit", "fix bug")
    → subprocess.run(["python", "system-codes/runner_git.py", "commit", "fix bug"])
      → runner_git.py nhận sys.argv = ["commit", "fix bug"]
        → cmd = 'wt nt -d "<ROOT>" cmd /k "git add . && git commit -m \"fix bug\" && git push origin main"'
        → subprocess.run(cmd, shell=True)
  → sys.exit(0)
```

### Ví dụ 2: `runner code ws ptb -a -p`

```
runner.cmd
  → py runner.py code ws ptb -a -p
  → argparse: type="code", action="ws", value="ptb", antigravity_IDE=True, powershell_only=True
  → default_ide_prefix = "anti"
  → type == RUNNER_TYPE_CODE
  → action == RUNNER_CODE_VSCODE_WORKSPACE
  → open_working_vscode("anti", "ptb", True)
    → subprocess.run(["python", "useful-codes/runner_main_ws.py", "anti", "ptb", "-p"])
      → runner_main_ws.py: value="ptb" → open_working_workspace_photobooth("anti", powershell_only=True)
        → wt -w _blank -d "D:/D-Documents/Code_VCN/Photobooth/code/ptm" --title "PTM"
           ; nt -d "D:/D-Documents/Code_VCN/Photobooth/recover-image" --title "recover-image"
  → sys.exit(0)
```

### Ví dụ 3: `runner run del-files --des`

```
runner.cmd
  → py runner.py run del-files --des
  → argparse: type="run", action="del-files", des=True
  → args.des == True → print_feature_description("run", "del-files")
    → subprocess.run(["python", "useful-codes/print_feature_description.py", "--type", "run", "--action", "del-files"])
      → đọc app_features.yml → in mô tả ACTION 21
  → sys.exit(0)
```

---

## 9. Giới hạn & Lưu ý

| Vấn đề                     | Mô tả                                                                                                             |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Hardcoded paths**        | Nhiều đường dẫn như `D:/D-Documents/...` và `C:/Users/dell/...` được hardcode trong code, không phải trong `.env` |
| **Windows-only**           | Tool phụ thuộc hoàn toàn vào Windows (`wt`, `rundll32`, `tasklist`, `start`)                                      |
| **Shell=True**             | Nhiều subprocess dùng `shell=True` → tiềm ẩn rủi ro injection nếu input từ user không được sanitize               |
| **sys.exit(0) pattern**    | Mọi handler đều exit ngay sau khi chạy — không có cơ chế callback hay chain lệnh                                  |
| **`RUNNER_STATUS` global** | Biến `RUNNER_STATUS` được khai báo global nhưng chỉ được dùng ở cuối để detect "out of flow"                      |
