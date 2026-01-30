import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="D:/D-Documents/runner/.env")

folder_path = os.getenv("ROOT_FOLDER_PATH")
file_extension = ".bat"
contains_string = "runners"

if __name__ == "__main__":
    if folder_path is None:
        raise ValueError("ROOT_FOLDER_PATH environment variable is not set")
    for f in os.listdir(folder_path):
        if f.endswith(file_extension) and f.startswith(contains_string):
            old_name = f
            new_name = "runner" + f[len(contains_string) :]
            old_full_path = os.path.join(folder_path, old_name)
            new_full_path = os.path.join(folder_path, new_name)
            os.rename(old_full_path, new_full_path)
            print(f"Renamed: {old_name} -> {new_name}")
