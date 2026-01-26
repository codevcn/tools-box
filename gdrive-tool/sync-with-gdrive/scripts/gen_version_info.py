from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_INIT = ROOT / "app" / "src" / "__init__.py"
OUT_FILE = ROOT / "build" / "version_info.txt"


def read_meta(init_py: Path) -> dict[str, str]:
    text = init_py.read_text(encoding="utf-8")

    def pick(name: str, default: str = "") -> str:
        m = re.search(rf'^{name}\s*=\s*["\'](.+?)["\']\s*$', text, flags=re.M)
        return m.group(1) if m else default

    return {
        "app_name": pick("__app_name__", "SynRive"),
        "version": pick("__version__", "0.1.0"),
        "author": pick("__author__", "CodeVCN"),
        "exe_name": pick("__exe_name__", "sync-with-gdrive.exe"),
        "description": pick(
            "__description__", "App dong bo file tu local len Google Drive"
        ),
    }


def parse_semver(v: str) -> tuple[int, int, int]:
    m = re.match(r"^\s*(\d+)\.(\d+)\.(\d+)\s*$", v)
    if not m:
        raise ValueError(f"Version must be MAJOR.MINOR.PATCH (got: {v!r})")
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def render_version_info(meta: dict[str, str]) -> str:
    major, minor, patch = parse_semver(meta["version"])
    # Windows wants 4-part tuple; we keep the 4th as 0
    return f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major},{minor},{patch},0),
    prodvers=({major},{minor},{patch},0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', '{meta["author"]}'),
          StringStruct('FileDescription', '{meta["description"]}'),
          StringStruct('FileVersion', '{meta["version"]}'),
          StringStruct('ProductName', '{meta["app_name"]}'),
          StringStruct('ProductVersion', '{meta["version"]}'),
          StringStruct('OriginalFilename', '{meta["exe_name"]}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main() -> None:
    meta = read_meta(APP_INIT)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(render_version_info(meta), encoding="utf-8")
    print(f"Wrote: {OUT_FILE}")
    print(f"Version: {meta['version']}")


if __name__ == "__main__":
    main()
