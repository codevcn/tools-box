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
    new_unreleased = "## [Unreleased]\n\n" "### Added\n\n" "### Changed\n\n" "### Fixed"

    # Build new changelog:
    # Keep everything before Unreleased header,
    # then new Unreleased template,
    # then release section,
    # then the rest after the original Unreleased block.
    start_idx = text.find(UNRELEASED_HEADER)
    before = text[:start_idx]

    # Remove the whole old Unreleased block from the text
    after = re.sub(pattern, "", text, count=1).lstrip("\n")

    new_text = (
        before.rstrip()
        + "\n\n"
        + new_unreleased
        + "\n\n"
        + release_section
        + "\n\n"
        + after
    ).rstrip() + "\n"
    CHANGELOG.write_text(new_text, encoding="utf-8")
    print(f"Updated: {CHANGELOG} -> released {version}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python scripts/release_changelog.py <version>")
        raise SystemExit(2)
    main(sys.argv[1])
