from pathlib import Path


def print_tree(
    root_path: Path,
    file_handle,
    prefix: str = "",
    exclude_dirs: set[str] | None = None,
):
    if exclude_dirs is None:
        exclude_dirs = set()

    entries = sorted(root_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))

    entries = [e for e in entries if not (e.is_dir() and e.name in exclude_dirs)]

    for index, entry in enumerate(entries):
        connector = "└── " if index == len(entries) - 1 else "├── "
        file_handle.write(f"{prefix}{connector}{entry.name}\n")

        if entry.is_dir():
            extension = "    " if index == len(entries) - 1 else "│   "
            print_tree(entry, file_handle, prefix + extension, exclude_dirs)


if __name__ == "__main__":
    # 📌 Xác định ROOT PROJECT (scripts/..)
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    excluded_dirs = {
        ".git",
        ".github",
        "__pycache__",
        "node_modules",
        ".venv",
        ".venv-build",
        "dist",
        "build",
    }

    output_file = PROJECT_ROOT / "scripts" / "project_tree.txt"

    with output_file.open("w", encoding="utf-8") as f:
        f.write(f"Tree view of: {PROJECT_ROOT}\n\n")
        print_tree(PROJECT_ROOT, f, exclude_dirs=excluded_dirs)

    print(f"✔ Project tree written to: {output_file}")
