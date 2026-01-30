import os
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(">>> Missing folder path.")
        sys.exit(1)
    folder_path = sys.argv[1]
    if folder_path.endswith("\\"):
        folder_path = folder_path[:-1]
    last_folder = os.path.basename(folder_path)
    print("============================")
    print("Path: " + folder_path)
    print("============================")
    print(last_folder + "\\")
    if not os.path.exists(folder_path):
        print(">>> Folder or file destination doesn't exist")
    else:
        for f in os.listdir(folder_path):
            full_path = os.path.join(folder_path, f)
            if os.path.isfile(full_path):
                print("    |---\\" + f)
    print("============================")
