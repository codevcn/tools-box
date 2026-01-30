import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/TOOLs/runner/.env")

CONTENTS_FOLDER_PATH = os.getenv("CONTENTS_FOLDER_PATH")
curl_file = f"{CONTENTS_FOLDER_PATH}/cURL.txt"

if __name__ == "__main__":
    try:
        with open(curl_file, "r") as f:
            print(f.read())
    except Exception as e:
        print(">>> Error reading cURL file:", e)
