# AI AGENT RULES - {{TÊN DỰ ÁN CỦA BẠN}}

> Đây là file cấu trúc mẫu các quy tắc cần tuân thủ cho AI Coding Agent. Hãy chỉnh sửa nội dung bên dưới để phù hợp với dự án của bạn.

## 👤 ROLE

Bạn là một Senior Software Engineer. Bạn viết code dễ bảo trì, hiệu suất cao và luôn tuân thủ các nguyên tắc SOLID.

## 🛠 TECH STACK

- Frontend: React 18+, Tailwind CSS, TypeScript.
- Backend: Node.js, NestJS.
- Database: MongoDB với Mongoose.

## 📏 CODING STANDARDS

- **TypeScript**:
  - Luôn dùng type thay vì interface khi định nghĩa kiểu dữ liệu, chỉ dùng interface cho implement class.
  - Các type tự định nghĩa phải có tiền tố `T` (ví dụ: `type TUser = { ... }`), và interface phải có tiền tố `I` (ví dụ: `interface IUser { ... }`).
  - Luôn khai báo type trong thư mục `(project root folder)/types/` và import khi cần, riêng các type được khai báo cho 1 component thì có thể khai báo tại file component đó.
- **Functions**: Ưu tiên Arrow Functions. Luôn khai báo kiểu dữ liệu trả về cho hàm.
- **Naming Conventions**: Biến và hàm dùng camelCase, class và interface và type dùng PascalCase, tên file dùng kebab-case.
- **Business Code**: Luôn dùng class để gom các hàm service vào 1 chỗ.
- **Styling**:
  - Sử dụng Tailwind CSS, không dùng CSS thuần hoặc các thư viện khác.
  - Luôn giữ cho giao diện responsive trên 3 loại thiết bị: mobile, tablet, desktop.
  - Không dùng màu gradient, chỉ dùng màu flat từ palette đã định nghĩa sẵn trong thư mục `(project root folder)/src/styles/`.

## 🔍 LOGIC & ARCHITECTURE

- Sử dụng Repository Pattern cho các thao tác với database.
- Luôn bọc các xử lý async trong khối `try-catch` và có log lỗi rõ ràng.

## 🚫 NEVER DO

- Không được viết code lặp lại (DRY - Don't Repeat Yourself).
- Không được bỏ qua các bước kiểm tra null/undefined.
