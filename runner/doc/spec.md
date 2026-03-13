Để một AI coding agent (như Cursor, Cline, hay GitHub Copilot) không chỉ "viết code chạy được" mà còn "viết code đúng ý đồ kiến trúc", bạn cần một tệp tin đóng vai trò là **Nguồn sự thật duy nhất (Single Source of Truth)**. Tệp này thường được đặt tên là `CONTEXT.md`.
Việc chuẩn bị file này giúp giảm tới **70%** thời gian bạn phải giải thích lại yêu cầu cho AI mỗi khi bắt đầu một phiên làm việc mới.

Dưới đây là cấu trúc chuẩn để viết một file mô tả dự án giúp AI "thấu thị" dự án của bạn chỉ trong vài giây.

---

# 🏗 Cấu trúc tệp Context chuẩn cho AI Agent

## 1. Tổng quan dự án (Project Vision)

Đừng chỉ nói "Dự án web". Hãy nói về mục đích và đối tượng sử dụng. AI sẽ dựa vào đây để đưa ra các gợi ý về trải nghiệm người dùng (UX).

- **Tên dự án:** (Ví dụ: vnote.io.vn)
- **Mục tiêu:** Một ứng dụng ghi chú bảo mật, tối giản, tập trung vào tốc độ.
- **Đối tượng:** Lập trình viên cần lưu trữ snippet code nhanh.
- **Mô tả**: Vnote là một ứng dụng ghi chú bảo mật, tối giản, tập trung vào tốc độ. Người dùng có thể tạo, chỉnh sửa và quản lý ghi chú dưới dạng markdown, với khả năng mã hóa dữ liệu ngay trên trình duyệt trước khi lưu trữ trên server.

## 2. Sơ đồ tư duy dự án (Project Mapping)

Đây là phần quan trọng nhất để AI không tạo file lung tung. Hãy mô tả cấu trúc thư mục quan trọng.

```text
/src
  /components  -> UI tái sử dụng (Atomic Design)
  /hooks       -> Logic xử lý dữ liệu từ API
  /services    -> Cấu hình Axios/Fetch cho backend
  /store       -> Quản lý trạng thái toàn cục

```

## 3. Quy tắc nghiệp vụ (Core Business Logic)

Mô tả những quy trình phức tạp mà code không nói lên hết được.

- **Ví dụ:** "Mỗi ghi chú phải được mã hóa ở phía Client trước khi gửi lên Server."
- **Ví dụ:** "Admin có quyền xem log nhưng không được xem nội dung ghi chú của người dùng."

## 4. "Từ điển" dự án (Glossary)

Nếu bạn có những thuật ngữ riêng, hãy định nghĩa chúng để AI không hiểu nhầm khi bạn yêu cầu.

- **V-Note:** Là đơn vị lưu trữ cơ bản nhất.
- **Admin-Gate:** Tên gọi của hệ thống middleware kiểm tra quyền truy cập.

## 5. Sử dụng File `.ai-ignore` (nếu có):

Nếu dự án quá lớn, hãy yêu cầu AI bỏ qua các thư mục không quan trọng (như `dist`, `build`, `node_modules`) để nó tập trung tài nguyên vào code logic.
