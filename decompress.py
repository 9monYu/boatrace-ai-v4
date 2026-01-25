import os

import lhafile


def main():
    # race
    directory_path = os.path.join(os.getcwd(), "official_data", "race")
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(file_path) and file_name.endswith(".lzh"):
            file = lhafile.LhaFile(file_path)
            for info in file.infolist():
                with open(os.path.join(directory_path, info.filename), "wb") as newfile:
                    newfile.write(file.read(info.filename))
            del file
            os.remove(file_path)

    # result
    directory_path = os.path.join(os.getcwd(), "official_data", "result")
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(file_path) and file_name.endswith(".lzh"):
            file = lhafile.LhaFile(file_path)
            for info in file.infolist():
                with open(os.path.join(directory_path, info.filename), "wb") as newfile:
                    newfile.write(file.read(info.filename))
            del file
            os.remove(file_path)

    # period stats
    directory_path = os.path.join(os.getcwd(), "official_data", "period_stats")
    for file_name in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file_name)
        if os.path.isfile(file_path) and file_name.endswith(".lzh"):
            file = lhafile.LhaFile(file_path)
            for info in file.infolist():
                with open(os.path.join(directory_path, info.filename), "wb") as newfile:
                    newfile.write(file.read(info.filename))
            del file
            os.remove(file_path)


if __name__ == "__main__":
    main()
