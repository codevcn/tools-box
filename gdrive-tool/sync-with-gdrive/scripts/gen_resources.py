from __future__ import annotations

from pathlib import Path


def generate_qrc() -> None:
    svg_dir = Path("app/src/assets/images/svg")
    ico_file = Path("app/src/assets/app.ico")
    out_qrc = Path("resources.qrc")

    qrc_lines: list[str] = [
        '<!DOCTYPE RCC><RCC version="1.0">',
        '  <qresource prefix="/icons">',
    ]

    # 1) Add app icon (.ico) vào QRC (nếu tồn tại)
    if ico_file.exists():
        # alias để gọi: :/icons/app.ico
        qrc_lines.append(f'    <file alias="app.ico">{ico_file.as_posix()}</file>')
    else:
        print(f"[WARN] Không tìm thấy icon: {ico_file}")

    # 2) Add tất cả .svg trong thư mục svg
    if not svg_dir.exists():
        print(f"[ERROR] Không tìm thấy thư mục SVG: {svg_dir}")
        return

    svg_files = sorted(
        [p for p in svg_dir.iterdir() if p.is_file() and p.suffix == ".svg"]
    )
    if not svg_files:
        print(f"[WARN] Không có file .svg trong: {svg_dir}")

    for p in svg_files:
        # alias để gọi: :/icons/<filename>.svg
        qrc_lines.append(f'    <file alias="{p.name}">{p.as_posix()}</file>')

    qrc_lines.append("  </qresource>")
    qrc_lines.append("</RCC>")

    out_qrc.write_text("\n".join(qrc_lines), encoding="utf-8")

    print(f"Đã tạo xong file '{out_qrc}'.")
    print("Biên dịch QRC -> resources_rc.py bằng lệnh:")
    print("  pyside6-rcc resources.qrc -o app/src/resources_rc.py")


if __name__ == "__main__":
    generate_qrc()
