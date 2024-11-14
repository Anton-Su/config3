import sys
import os


def main(path_to_itog_file):
    directory = os.path.dirname(path_to_itog_file)
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return
    with open(path_to_itog_file, mode="w") as f:
        f.write("12331")
    pass








if __name__ == "__main__":
    # # if len(sys.argv) != 2:
    # #     print("Аргументы указаны неверно")
    # #     exit()
    # path_to_itog_file = sys.argv[1]
    path_to_itog_file = r'C:\Users\Antua\PycharmProjects\config3\testfile.txt'
    main(path_to_itog_file)
