import os
from dotenv import load_dotenv
import sys

content_filename = sys.argv[1]
if not content_filename:
    print(">>> Error: No content filename provided.")
    sys.exit(1)

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/runner/.env")
CONTENTS_FOLDER_PATH = os.getenv("CONTENTS_FOLDER_PATH")
help_file = f"{CONTENTS_FOLDER_PATH}/{content_filename}"

if __name__ == "__main__":
    try:
        with open(help_file, "r") as f:
            print(f.read())
    except Exception as e:
        print(">>> Error reading help file:", e)
