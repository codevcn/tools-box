from __future__ import annotations
from pathlib import Path
import os
import json
from typing import Iterable, Optional, Any
from configs.configs import PathType, CODE_EXTENSIONS, MEDIA_EXTENSIONS
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt, QRectF


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
    try:
        path = Path(path_str)

        if not path.exists():
            return "not_exists"
        if path.is_file():
            return "file"
        if path.is_dir():
            return "folder"

        return "invalid"  # symlink đặc biệt, socket, ...
    except Exception:
        return "invalid"


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


def get_json_field_value(field_path: str, json_file_path: Path) -> Any:
    """
    Lấy giá trị của một field từ file sync-with-gdrive.json.

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
        if not json_file_path.exists():
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
    except Exception:
        return None


def svg_to_pixmap(
    svg_path: str,
    size: int,
    fill_color: str | None = None,
    stroke_color: str | None = None,
) -> QPixmap:
    # Đọc và thay đổi màu trong SVG
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Thay thế các thuộc tính màu bằng màu mới
    # Thay fill="currentColor" hoặc stroke="currentColor" bằng màu cụ thể
    if fill_color:
        svg_content = svg_content.replace('fill="currentColor"', f'fill="{fill_color}"')
    if stroke_color:
        svg_content = svg_content.replace(
            'stroke="currentColor"', f'stroke="{stroke_color}"'
        )

    # Nếu không có currentColor, thêm fill vào các path/shape
    if "currentColor" not in svg_content:
        # Thay thế fill và stroke có sẵn
        import re

        svg_content = re.sub(r'fill="[^"]*"', f'fill="{fill_color}"', svg_content)
        svg_content = re.sub(
            r'stroke="[^"]*"(?!\s*stroke-width)',
            f'stroke="{stroke_color}"',
            svg_content,
        )
        # Thêm fill cho các path không có fill
        svg_content = re.sub(
            r"<path(?![^>]*fill=)", f'<path fill="{fill_color}"', svg_content
        )

    # Render SVG với màu đã thay đổi
    renderer = QSvgRenderer(svg_content.encode("utf-8"))

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    return pixmap
