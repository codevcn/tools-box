import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/runner/.env")
RUNNER_ROOT_FOLDER = os.getenv("ROOT_FOLDER_PATH")


def warn_user_error(warning_message: str):
    print(">>> Warn: " + warning_message)
    sys.exit(0)


def print_feature_description(cmd_type: str | None, action: str | None):
    yaml_path = os.path.join(
        RUNNER_ROOT_FOLDER or "", "src", "contents", "app_features.yml"
    )
    if not os.path.exists(yaml_path):
        warn_user_error(f"Cannot find feature definitions: {yaml_path}")

    try:
        import yaml

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        types = data.get("runner_tool", {}).get("types", [])

        for t in types:
            if cmd_type and t.get("name") != cmd_type:
                continue

            for a in t.get("actions", []):
                cmd_raw = a.get("command", "")
                cmds = [c.strip() for c in cmd_raw.split("|")]

                for cmd in cmds:
                    cmd_parts = cmd.split()

                    if cmd_parts and cmd_parts[0] == "runner":
                        cmd_parts = cmd_parts[1:]

                    yaml_type = cmd_parts[0] if len(cmd_parts) > 0 else None
                    yaml_action = (
                        cmd_parts[1]
                        if len(cmd_parts) > 1
                        and not cmd_parts[1].startswith("<")
                        and not cmd_parts[1].startswith("[")
                        and not cmd_parts[1].startswith("-")
                        else None
                    )

                    target_found = False
                    if cmd_type is None and action is None:
                        if yaml_type is None or yaml_type.startswith("-"):
                            target_found = True
                    elif cmd_type is not None and action is None:
                        if yaml_type == cmd_type and yaml_action is None:
                            target_found = True
                    elif cmd_type is not None and action is not None:
                        if yaml_type == cmd_type and yaml_action == action:
                            target_found = True

                    if target_found:
                        print(f"\n--- Tính năng: {a.get('title')} ---")
                        print(f"+) Lệnh:\t{a.get('command')}")
                        print(f"+) Tóm tắt:\t{a.get('summary')}")
                        print(f"+) Chi tiết:\t{a.get('details')}")
                        print(f"+) Điều kiện:\t{a.get('conditions')}\n")
                        sys.exit(0)

        cmd_str = f"runner {cmd_type or ''} {action or ''}".strip()
        warn_user_error(f"Không tìm thấy mô tả cho lệnh: `{cmd_str}`")

    except ImportError:
        warn_user_error(
            "Chưa cài đặt thư viện 'pyyaml'. Vui lòng chạy `pip install pyyaml` hoặc `pip install -r requirements.txt`"
        )
    except Exception as e:
        warn_user_error(f"Lỗi khi đọc file mô tả YAML: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print feature description.")
    parser.add_argument("--type", type=str, default=None, help="Command type")
    parser.add_argument("--action", type=str, default=None, help="Command action")
    args = parser.parse_args()

    print_feature_description(args.type, args.action)
