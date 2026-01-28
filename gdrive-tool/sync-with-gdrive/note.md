1. Tự viết 1 script commit & push riêng cho nhánh sync-with-gdrive
2. Tự viết 1 script commit & push riêng cho nhánh runner
3. **check với run_app_multi.py**
4. thêm code check xem path user nhập vào mục "Đường dẫn thư mục đích trên kho lưu trữ" có phải là 1 path hợp lệ không
5. kiểm tra xem các component sau có rò rỉ bộ nhớ không (memory leak):
- tooltip
- centered overlay

---

Hiện tại đang ở bước trong file blueprints/current_build_profile.md (đưa file rclone.exe vào app/build/bin)