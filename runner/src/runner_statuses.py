import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/runner/.env")

CONTENTS_FOLDER_PATH = os.getenv("CONTENTS_FOLDER_PATH")
statuses_file = rf"{CONTENTS_FOLDER_PATH}/statuses.txt"

if __name__ == "__main__":
    try:
        with open(statuses_file, "r") as f:
            print(f.read())
    except Exception as e:
        print(">>> Error reading statuses file:", e)
