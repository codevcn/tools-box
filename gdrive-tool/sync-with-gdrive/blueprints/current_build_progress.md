Ok, mình **tổng kết lại toàn bộ trạng thái hiện tại của bạn**, theo đúng tiến trình build production mà ta đang đi — để bạn nhìn **1 phát là biết mình đã chốt tới đâu**.

---

# 🧭 TỔNG KẾT TIẾN TRÌNH BUILD PRODUCTION – SYNRIVE

## ✅ BƯỚC 0 — CHỐT ĐỊNH HƯỚNG RELEASE (DONE)

Bạn đã chốt rất rõ:

- ✅ **Kiểu release:** `one-folder`
- ✅ **Thư mục data user:** `%AppData%/SynRive`
- ✅ **Điều kiện chạy:** máy **không cài Python** vẫn chạy được
- ✅ **Đối tượng sử dụng:** user thao tác qua **Windows context menu**

👉 Đây là nền tảng đúng cho app desktop thực tế.

---

## ✅ BƯỚC 1 — MÔI TRƯỜNG BUILD SẠCH (DONE)

- ✅ Tạo `.venv-build` riêng
- ✅ Cài dependency cần thiết
- ✅ App chạy OK trong môi trường build
- ✅ Đã lock dependency bằng `requirements.lock.txt`

👉 Build sau này **lặp lại y hệt**, không lệch phiên bản.

---

## ✅ BƯỚC 2 — QUÉT & LOẠI DEV-ONLY (DONE)

### 2.1. Path & CWD

- ✅ **Không dùng `os.getcwd()`** cho asset / tool
- ✅ Dùng `sys._MEIPASS` khi frozen
- ✅ Có `project_root_dir()` + `resolve_from_root_dir()`

### 2.2. Tool ngoài – rclone (DONE & CHỐT)

- ✅ **Chọn Option A:** bundle `rclone.exe`
- ✅ Vị trí nguồn: `app/build/bin/rclone.exe`
- ✅ Build đưa `rclone.exe` ra **root bundle** (`dist/SynRive/rclone.exe`)
- ✅ Sync worker **không dùng PATH**, dùng absolute path
- ✅ Authorize worker **không dùng PATH**, dùng absolute path

👉 App **không phụ thuộc máy user**.

---

## ✅ BƯỚC 2.4 — CHỐT RCLONE CONFIG PATH (DONE)

- ✅ **Không dùng config hệ thống** `%AppData%\rclone`
- ✅ Chốt config riêng cho app:

  ```
  %AppData%/SynRive/rclone/rclone.conf
  ```

- ✅ Cả **login (authorize)** và **sync** đều prepend:

  ```
  --config <path>
  ```

- ✅ Không “ăn ké” config của máy dev hay user

👉 App **portable, clean, dễ debug**.

---

## ✅ BƯỚC 3 — ASSET & RESOURCE (ĐANG Ở ĐÂY – GẦN XONG)

### 3.1. SVG & Icon UI

- ✅ SVG icon dùng **QRC**
- ✅ Prefix chuẩn: `:/icons/...`
- ✅ `helpers.py` gọi icon qua QRC → **CWD-safe**

### 3.2. App icon (.ico)

- ✅ `app.ico` đã được **đưa vào QRC**
- ✅ Script `gen_resources.py` đã sửa để:
  - add `.svg`
  - add `app.ico`

- ✅ `setWindowIcon(QIcon(":/icons/app.ico"))`

👉 Không còn asset nào phụ thuộc path thật.

⏳ **Việc còn lại nhỏ trong bước 3:**

- [ ] Regenerate `resources_rc.py`
- [ ] Đảm bảo `import resources_rc` được load ít nhất 1 lần (entrypoint)

---

## 🟡 BƯỚC 4 — PYINSTALLER BUILD (CHƯA LÀM, SẮP TỚI)

Bạn **chưa build chính thức**, nhưng đã sẵn sàng.

Dự kiến:

```bat
pyinstaller --onedir --name SynRive ^
  --add-binary "app\build\bin\rclone.exe;." ^
  run_app.py
```

(Có thể thêm `--icon`, `--noconsole`, `--version-file` sau)

---

## 🟡 BƯỚC 5 — CONTEXT MENU PRODUCTION (CHƯA LÀM)

Hiện tại:

- Context menu dev → gọi Python + `.py`

Cần làm:

- `.reg` production gọi:

  ```
  "...\SynRive.exe" "%1"
  ```

- Hỗ trợ file / folder / background / multi-select

👉 **Đây là bước cuối cùng để “ra user thật”**.

---

## 🧩 TÓM TẮT NGẮN GỌN (1 DÒNG / BƯỚC)

| Bước                     | Trạng thái  |
| ------------------------ | ----------- |
| 0. Định hướng release    | ✅ DONE     |
| 1. Môi trường build      | ✅ DONE     |
| 2. Dev-only & rclone exe | ✅ DONE     |
| 2.4 Rclone config path   | ✅ DONE     |
| 3. Asset & QRC           | 🟡 GẦN XONG |
| 4. PyInstaller build     | ⏳ CHƯA     |
| 5. Context menu prod     | ⏳ CHƯA     |

---

## 👉 Bước hợp lý tiếp theo là gì?

**Bạn đang ở cuối BƯỚC 3.**

👉 Lựa chọn tiếp theo:

1. **Mình chốt nốt Bước 3** (check kỹ không sót asset nào, rồi chuyển build)
2. **Hoặc nhảy thẳng sang Bước 4**: mình viết **lệnh PyInstaller final** cho bạn
3. **Hoặc làm Bước 5**: viết **file `.reg` production hoàn chỉnh**

Bạn chỉ cần nói **số bước muốn làm tiếp**.
