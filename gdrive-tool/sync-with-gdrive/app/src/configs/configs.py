from typing import Literal
from enum import Enum

PATH_TYPE = Literal["file", "folder", "not_exists", "invalid"]

CODE_EXTENSIONS = {
    "py": "code",
    "js": "code",
    "java": "code",
    "c": "code",
    "cpp": "code",
    "cs": "code",
    "rb": "code",
    "go": "code",
    "php": "code",
    "rs": "code",
    "ts": "code",
    "html": "code",
    "css": "code",
    "swift": "code",
    "kotlin": "code",
    "xml": "code",
    "json": "json",
    "md": "markdown",
}

MEDIA_EXTENSIONS = {
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "webp": "image",
    "svg": "image",
    "ico": "image",
    "pdf": "pdf",
    "doc": "word",
    "docx": "word",
    "xls": "excel",
    "xlsx": "excel",
    "ppt": "ppt",
    "pptx": "ppt",
    "mp4": "video",
    "mkv": "video",
    "avi": "video",
    "mp3": "audio",
    "wav": "audio",
    "flac": "audio",
    "zip": "archive",
    "rar": "archive",
    "7z": "archive",
    "txt": "txt",
}


class SyncError(int, Enum):
    NONE = 1
    COMMON = 2
    NEED_LOGIN = 3
    INTERNAL = 4


class ThemeColors:
    MAIN = "#00ddca"
    LIGHT_MAIN = "#74e5db"
    DARK_MAIN = "#21c1b3"
    GRAY_BACKGROUND = "#303030"
    GRAY_BORDER = "#525252"
    GRAY_HOVER = "#5e5e5e4d"
    STRONG_GRAY = "#c4c4c4"
    SUCCESS = "#4BB543"
    ERROR = "#FF3333"
    WARNING = "#FFAA00"
    INFO = "#3399FF"
