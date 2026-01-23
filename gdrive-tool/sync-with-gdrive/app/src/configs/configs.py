from typing import Literal
from enum import Enum

PathType = Literal["file", "folder", "not_exists", "invalid"]

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


class SyncError(Enum):
    NONE = 1
    COMMON = 2
    NEED_LOGIN = 3
