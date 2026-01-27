Dưới đây là **checklist “đi từ hướng dẫn build → ra bản production chạy ổn”**

---

## 0) Chốt “đầu ra” bản production

- [ ] Xác định kiểu phát hành: **1 file .exe** hay **thư mục (one-folder)**.
- [ ] Xác định nơi đặt dữ liệu user: **%AppData%/YourApp** (không để cạnh exe).
- [ ] Xác định “điều kiện chạy”: máy **không cài Python** vẫn chạy được.

---

## 1) Dọn & khóa môi trường build (để build nhanh, ít lỗi vặt)

- [ ] Tạo venv sạch cho build (không build bằng môi trường dev lộn xộn).
- [ ] `pip freeze`/lock versions (tối thiểu ghi lại phiên bản các lib chính).
- [ ] Dọn imports/unused deps để giảm rác khi bundle.

---

## 2) Quét các thứ “dev-only” sẽ chết ở production

- [ ] Không hard-code path kiểu `C:\Users\...` / path theo máy bạn.
- [ ] Mọi resource (svg/icon/json/template/…) phải có **cơ chế resolve path khi đã bundle**.
- [ ] Không phụ thuộc biến môi trường do bạn tự set thủ công (nếu có thì auto tạo/auto fallback).

---

## 3) Asset & resource: đóng gói chắc chắn

- [ ] Lập danh sách asset cần mang theo: icon app, svg, fonts, file config mẫu, templates…
- [ ] Kiểm tra code đang load asset bằng path tương đối → OK khi chạy từ exe.
- [ ] Nếu dùng PyInstaller: add assets vào spec / `--add-data` đầy đủ.

---

## 4) Logging & xử lý lỗi kiểu “người dùng đọc được”

- [ ] Thay `print()` bằng logger ghi file (ví dụ log vào `%AppData%/YourApp/logs/...`).
- [ ] Bọc các điểm dễ crash: file not found, permission, network, rclone fail…
- [ ] Khi lỗi: hiện thông báo “ngôn ngữ người” + nút copy log (nếu có).

---

## 5) Dữ liệu người dùng “sống sót qua update”

- [ ] Config/token/cache → lưu trong `%AppData%/YourApp` (hoặc thư mục tương đương).
- [ ] Có cơ chế tạo file mặc định nếu chưa tồn tại (first run).
- [ ] Không ghi dữ liệu user vào thư mục cài đặt/exe (dễ lỗi permission).

---

## 6) PyInstaller build (nhanh + đúng)

- [ ] Chạy build thử “one-folder” trước (dễ debug) → ổn rồi mới cân nhắc “one-file”.
- [ ] Set icon exe + metadata version (file properties) nếu có.
- [ ] Nếu app dùng subprocess/tool ngoài (vd rclone): quyết định **bundle kèm** hay **yêu cầu cài sẵn**, và test theo đúng quyết định đó.

---

## 7) Test kiểu “tôi là người dùng ngu nhất”

- [ ] Copy bản build sang **folder khác** (không nằm trong project).
- [ ] Test trên máy/Windows user khác **không có Python**.
- [ ] Xóa/đổi tên folder project gốc để chắc chắn app không “ăn ké” file dev.
- [ ] Test các flow chính: mở app, chọn file/folder, sync, cancel, mở settings, thoát app.
- [ ] Test quyền admin/non-admin (nhất là nếu đụng registry / context menu).

---

## 8) Versioning & phát hành

- [ ] Cập nhật `CHANGELOG.md` + bump version (ít nhất: `0.1.0 → 0.1.1`…).
- [ ] Đặt tên artifact rõ ràng: `YourApp-0.1.1-win-x64.exe` (hoặc zip folder).
- [ ] Lưu lại 1 bản “build notes”: commit hash + ngày build + các thay đổi chính.

---

## 9) “Nice-to-have” nếu bạn muốn chuyên nghiệp hơn (không bắt buộc)

- [ ] Code signing (giảm cảnh báo SmartScreen) _(làm sau cũng được)_.
- [ ] Auto-update / installer (MSI/Inno Setup) _(để phase 2)_.
