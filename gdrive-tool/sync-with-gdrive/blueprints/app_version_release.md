Dưới đây là cách **tự động generate `build/version_info.txt` + cập nhật `CHANGELOG.md`** theo kiểu “đúng nghiệp vụ” nhưng vẫn **đơn giản** (hợp project SynRive của bạn).

Mục tiêu tư duy:

* **1 nguồn version duy nhất** trong code (`__version__`)
* `version_info.txt` là **file sinh ra** (không sửa tay)
* `CHANGELOG.md` theo **Keep a Changelog** (có `[Unreleased]`)
* Release = chạy 1–2 lệnh: *bump version → update changelog → generate version_info → (tuỳ chọn) git tag*

---

# 1) Single source of truth: đặt version trong code

Tạo / sửa file: `app/src/__init__.py`

```py
__app_name__ = "SynRive"
__version__ = "0.1.0"
__author__ = "CodeVCN"
__exe_name__ = "sync-with-gdrive.exe"
__description__ = "App dong bo file tu local len Google Drive"
```

> Bạn chỉ cần sửa `__version__` (và nội dung changelog) khi release.

---

# 2) Tạo CHANGELOG.md chuẩn “nghiệp vụ”

Tạo file `CHANGELOG.md` ở root project:

```md
# Changelog
All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [Unreleased]
### Added
- Initial release of SynRive (local -> Google Drive sync)

### Changed

### Fixed
```

Khi bạn release, `[Unreleased]` sẽ được “chốt” thành `[0.1.0] - YYYY-MM-DD` và tạo lại một `[Unreleased]` rỗng cho vòng sau.

---

# 3) Script tự generate build/version_info.txt từ **version**

Tạo file: `scripts/gen_version_info.py`

```py
from __future__ import annotations

import re
from pathlib import Path
from datetime import date

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
        "description": pick("__description__", "App dong bo file tu local len Google Drive"),
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
```

Chạy:

```bat
py scripts\gen_version_info.py
```

---

# 4) Script “chốt changelog” theo version (Keep a Changelog)

Tạo file: `scripts/release_changelog.py`

```py
from __future__ import annotations

import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"

UNRELEASED_HEADER = "## [Unreleased]"

def main(version: str) -> None:
    if not CHANGELOG.exists():
        raise FileNotFoundError("CHANGELOG.md not found at project root")

    text = CHANGELOG.read_text(encoding="utf-8")

    if UNRELEASED_HEADER not in text:
        raise ValueError("CHANGELOG.md must contain '## [Unreleased]' section")

    today = date.today().isoformat()

    # Find Unreleased section block
    # It starts at ## [Unreleased] and ends right before the next ## [X] section or EOF
    pattern = r"(?s)## \[Unreleased\]\s*(.*?)(?=\n## \[|\Z)"
    m = re.search(pattern, text)
    if not m:
        raise ValueError("Could not parse [Unreleased] section")

    unreleased_body = m.group(1).rstrip()

    # Create release section
    release_section = f"## [{version}] - {today}\n{unreleased_body}\n"

    # Replace Unreleased body with a fresh empty template
    new_unreleased = (
        "## [Unreleased]\n"
        "### Added\n\n"
        "### Changed\n\n"
        "### Fixed\n"
    )

    # Build new changelog:
    # Keep everything before Unreleased header,
    # then new Unreleased template,
    # then release section,
    # then the rest after the original Unreleased block.
    start_idx = text.find(UNRELEASED_HEADER)
    before = text[:start_idx]

    # Remove the whole old Unreleased block from the text
    after = re.sub(pattern, "", text, count=1).lstrip("\n")

    new_text = (before.rstrip() + "\n\n" + new_unreleased + "\n\n" + release_section + "\n\n" + after).rstrip() + "\n"
    CHANGELOG.write_text(new_text, encoding="utf-8")
    print(f"Updated: {CHANGELOG} -> released {version}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python scripts/release_changelog.py <version>")
        raise SystemExit(2)
    main(sys.argv[1])
```

Chạy:

```bat
py scripts\release_changelog.py 0.1.0
```

---

# 5) Quy trình release “đúng chuẩn nhưng vẫn ít bước”

Mỗi lần release:

### Bước A — đổi version (source of truth)

Sửa `app/src/__init__.py`:

```py
__version__ = "0.1.1"
```

### Bước B — chốt changelog theo version

```bat
py scripts\release_changelog.py 0.1.1
```

### Bước C — generate version_info.txt

```bat
py scripts\gen_version_info.py
```

### Bước D — build PyInstaller (ví dụ)

```bat
pyinstaller --noconfirm --onefile --windowed ^
  --name sync-with-gdrive ^
  --icon app\src\assets\app.ico ^
  --version-file build\version_info.txt ^
  run_app.py
```

### Bước E (khuyến nghị) — commit + tag

```bat
git add -A
git commit -m "release: v0.1.1"
git tag v0.1.1
git push --follow-tags
```

---

## Tại sao đây là “đúng nghiệp vụ”?

* Bạn có **SemVer** (version rõ ràng)
* Có **Keep a Changelog** với `[Unreleased]` (luồng làm việc chuẩn)
* `version_info.txt` là **build artifact** sinh từ version thật (không lệch)
* Có tag để trace release
