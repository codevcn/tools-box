from __future__ import annotations
from pathlib import Path
import os
import json
from typing import Iterable, Optional, Any
from configs.configs import PathType, CODE_EXTENSIONS, MEDIA_EXTENSIONS
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt, QRectF, QFile, QIODevice
import re
import sys


def app_data_dir() -> Path:
    appdata = os.getenv("APPDATA")  # Windows
    if not appdata:
        # fallback hiếm
        appdata = str(Path.home() / "AppData" / "Roaming")
    path = Path(appdata) / "SynRive"
    path.mkdir(parents=True, exist_ok=True)
    return path


def project_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[3]


def resolve_from_root_dir(*parts: str) -> str:
    return str(project_root_dir().joinpath(*parts))


def rclone_executable_path() -> str:
    """
    Trả về đường dẫn tuyệt đối đến rclone.exe:
    - Frozen (PyInstaller): nằm ở root bundle (cạnh exe)
    - Dev: lấy từ 1 vị trí bạn đặt rclone trong repo (gợi ý: app/dev/bin/rclone.exe)
    """
    path = ""
    if getattr(sys, "frozen", False):
        path = resolve_from_root_dir("rclone.exe")

    path = resolve_from_root_dir("app", "build", "bin", "rclone.exe")
    if not Path(path).exists():
        raise RuntimeError(f"Không tìm thấy rclone.exe tại: {path}")
    return path


def ensure_rclone_exists() -> bool:
    p = Path(rclone_executable_path())
    return p.exists()


def rclone_config_path() -> Path:
    # %AppData%/SynRive/rclone/rclone.conf
    p = app_data_dir() / "rclone"
    p.mkdir(parents=True, exist_ok=True)
    return p / "rclone.conf"


def _normalize_qrc_path(path: str) -> str:
    if not path:
        return path
    if path.startswith(":/"):
        return path
    if path.startswith(":"):
        return f":/{path[1:].lstrip('/')}"
    return path


def extract_common_folder(paths: Iterable[str]) -> Path:
    # Chuẩn hoá và bỏ phần file name nếu là file
    normed: list[Path] = []
    for p in paths:
        s = os.path.expandvars(os.path.expanduser(p.strip().strip('"')))
        pp = Path(s)
        # Nếu có đuôi (file) thì lấy parent, còn folder thì giữ nguyên
        normed.append(pp.parent if pp.suffix else pp)

    if not normed:
        raise ValueError("No paths provided")

    # Tìm common path theo string (ổn cho Windows drive)
    common = os.path.commonpath([str(p) for p in normed])
    return Path(common)


def extract_common_folder_str(paths: Iterable[str]) -> str:
    return extract_common_folder(paths).as_posix()


def detect_path_type(path_str: str) -> PathType:
    """
    Phát hiện loại của path:
    - "not_exists": nếu path không tồn tại
    - "file": nếu là file
    - "folder": nếu là folder
    - "invalid": nếu không xác định được (symlink đặc biệt, socket, ...)
    """
    try:
        path = Path(path_str)

        if not path.exists():
            return PathType.NOT_EXISTS
        if path.is_file():
            return PathType.FILE
        if path.is_dir():
            return PathType.FOLDER

        return PathType.INVALID  # symlink đặc biệt, socket, ...
    except Exception:
        return PathType.INVALID


def detect_file_extension(path_str: str) -> Optional[str]:
    """
    Trả về extension của file (không có dấu chấm).
    - 'image.png'  -> 'png'
    - 'archive.tar.gz' -> 'gz'
    - 'README' -> None
    """
    path = Path(path_str)

    if path.suffix:
        return path.suffix[1:].lower()

    return None


def detect_content_type_by_file_extension(file_extension: str) -> str:
    """
    Dựa vào đuôi file để đoán content type (MIME type).
    Trả về chuỗi rỗng nếu không xác định được.
    """
    content_type = "file"  # default icon

    if file_extension:
        if file_extension in CODE_EXTENSIONS:
            content_type = f"{CODE_EXTENSIONS[file_extension]}"
        elif file_extension in MEDIA_EXTENSIONS:
            content_type = f"{MEDIA_EXTENSIONS[file_extension]}"

    return content_type


def extract_filename_with_ext(path: str) -> str:
    return Path(path).name


def get_json_field_value(
    field_path: str, json_file_path: Path, ensure_json_path_exists: bool = False
) -> Any:
    """
    Lấy giá trị của một field từ file json_file_path.

    Args:
        field_path: Đường dẫn đến field, phân cách bởi dấu chấm.
            VD: "sync_settings.include_patterns"

    Returns:
        Giá trị của field hoặc None nếu không tìm thấy.

    Examples:
        - get_json_field_value("active_remote") -> "codevoicainay-mydrive"
        - get_json_field_value("sync_settings.include_patterns") -> ["*"]
    """
    try:
        if not ensure_json_path_exists and not json_file_path.exists():
            return None

        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Navigate through nested keys
        keys = field_path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value
    except Exception as e:
        print(f">>> Error getting JSON field '{field_path}': {e}")
        return None


def set_json_field_value(
    field_path: str,
    value: Any,
    json_file_path: Path,
    ensure_json_path_exists: bool = True,
) -> bool:
    """
    Set giá trị cho một field trong file json_file_path.

    Args:
        field_path: Đường dẫn đến field, phân cách bởi dấu chấm.
            VD: "sync_settings.include_patterns"
        value: Giá trị cần set (có thể là bất kỳ kiểu dữ liệu nào: str, int, list, dict, etc.)
        json_file_path: Path đến file JSON
        ensure_json_path_exists: Nếu True, tạo file mới nếu chưa tồn tại. Nếu False và file không tồn tại, return False.

    Returns:
        True nếu set thành công, False nếu có lỗi.

    Examples:
        - set_json_field_value("active_remote", "my-drive", path) -> True
        - set_json_field_value("sync_settings.include_patterns", ["*"], path) -> True
        - set_json_field_value("user.preferences.theme", "dark", path) -> True
    """
    try:
        data: dict = {}

        # Nếu ko tham số ensure_json_path_exists và file ko tồn tại thì return False
        if not ensure_json_path_exists and not json_file_path.exists():
            raise FileNotFoundError("JSON file does not exist.")

        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Navigate và tạo nested structure nếu cần
        keys = field_path.split(".")
        current = data

        # Traverse đến key cuối cùng, tạo nested dict nếu cần
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                # Key đã tồn tại nhưng không phải dict -> không thể nested tiếp
                return False
            current = current[key]

        # Set giá trị cho key cuối cùng
        last_key = keys[-1]
        current[last_key] = value

        # Save lại file
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return True

    except Exception as e:
        print(f">>> Error setting JSON field '{field_path}': {e}")
        return False


def svg_to_pixmap(
    svg_path: str,
    size: int,
    fill_color: str | None = None,
    stroke_color: str | None = None,
    stroke_width: float | None = None,
    margins: int | tuple[int, int, int, int] = 0,  # <--- Tham số mới
) -> QPixmap:
    """
    Chuyển đổi SVG thành QPixmap với tùy chọn đổi màu và thêm margin.

    Args:
        svg_path: Đường dẫn file SVG.
        size: Kích thước của nội dung icon (không bao gồm margin).
        fill_color: Màu fill mới (VD: "#ffffff").
        stroke_color: Màu stroke mới.
        margins: Khoảng cách bao quanh.
                 Nhập int (VD: 5) để áp dụng 4 phía.
                 Nhập tuple (left, top, right, bottom) (VD: (0, 0, 8, 0)).
    """

    # 1. Đọc và xử lý nội dung SVG (giữ nguyên logic của bạn)
    svg_path = _normalize_qrc_path(svg_path)
    svg_content = ""
    if svg_path.startswith(":/"):
        qfile = QFile(svg_path)
        if not qfile.open(QIODevice.OpenModeFlag.ReadOnly):
            print(f"Error reading SVG: {qfile.errorString()} ({svg_path})")
            return QPixmap()
        raw_data = qfile.readAll().data()
        svg_content = bytes(raw_data).decode("utf-8", errors="replace")
        qfile.close()
    else:
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
        except Exception as e:
            print(f"Error reading SVG: {e}")
            return QPixmap()

    # Thay thế màu sắc
    if fill_color:
        svg_content = svg_content.replace('fill="currentColor"', f'fill="{fill_color}"')
        # Regex thay thế mạnh tay hơn nếu cần
        if "currentColor" not in svg_content:
            svg_content = re.sub(r'fill="[^"]*"', f'fill="{fill_color}"', svg_content)
            svg_content = re.sub(
                r"<path(?![^>]*fill=)", f'<path fill="{fill_color}"', svg_content
            )

    if stroke_color:
        svg_content = svg_content.replace(
            'stroke="currentColor"', f'stroke="{stroke_color}"'
        )
        if "currentColor" not in svg_content:
            svg_content = re.sub(
                r'stroke="[^"]*"(?!\s*stroke-width)',
                f'stroke="{stroke_color}"',
                svg_content,
            )

    if stroke_width:
        if re.search(r'stroke-width="[^"]*"', svg_content):
            svg_content = re.sub(
                r'stroke-width="[^"]*"',
                f'stroke-width="{stroke_width}"',
                svg_content,
            )
        else:
            # 2. Nếu chưa có → inject vào thẻ <svg ...>
            svg_content = re.sub(
                r"<svg\b",
                f'<svg stroke-width="{stroke_width}"',
                svg_content,
                count=1,
            )

    # 2. Xử lý logic Margin
    if isinstance(margins, int):
        left = top = right = bottom = margins
    elif isinstance(margins, (tuple, list)) and len(margins) == 4:
        left, top, right, bottom = margins
    else:
        left = top = right = bottom = 0

    # Tính toán kích thước tổng thể của QPixmap (Icon + Margins)
    total_width = size + left + right
    total_height = size + top + bottom

    # 3. Render
    renderer = QSvgRenderer(svg_content.encode("utf-8"))

    # Tạo Pixmap với kích thước tổng
    pixmap = QPixmap(total_width, total_height)
    pixmap.fill(Qt.GlobalColor.transparent)  # Nền trong suốt

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Vẽ icon vào vị trí đã tính toán (dịch chuyển theo left, top)
    # Kích thước vẽ vẫn là `size` gốc
    renderer.render(painter, QRectF(left, top, size, size))

    painter.end()

    return pixmap


def get_svg_file_path(svg_name: str) -> tuple[str, str]:
    """Lấy đường dẫn đầy đủ đến file SVG trong thư mục assets."""
    prefix_path = f":/icons"
    svg = f"{prefix_path}/{svg_name}.svg"
    return svg, prefix_path


def get_svg_as_icon(
    svg_name: str,
    size: int,
    fill_color: str | None = None,
    stroke_color: str | None = None,
    stroke_width: float | None = None,
    margins: int | tuple[int, int, int, int] = 0,
) -> QPixmap:
    """Lấy QPixmap từ file SVG trong thư mục assets."""
    return svg_to_pixmap(
        get_svg_file_path(svg_name)[0],
        size,
        fill_color,
        stroke_color,
        stroke_width,
        margins,
    )
