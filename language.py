import sys
import os
import keyboard
import time
import threading


def read_input(text):
    for line in sys.stdin:
        if line.strip():
            text.append(line)
        time.sleep(0.1)


def main(path_to_itog_file):
    directory = os.path.dirname(path_to_itog_file)
    if not os.path.exists(directory) or not os.path.isdir(directory):
        return
    text = []
    input_thread = threading.Thread(target=read_input, args=(text,))
    input_thread.daemon = True
    input_thread.start()
    while not keyboard.is_pressed("ctrl+d"):
        time.sleep(0.1)
    do_something(text)


def do_something(text):
    print(text)
    print(1111)

















def write(path_to_itog_file, text):  # где-то уже в конце
    with open(path_to_itog_file, mode="w") as f:
        f.write(text)


if __name__ == "__main__":
    # # if len(sys.argv) != 2:
    # #     print("Аргументы указаны неверно")
    # #     exit()
    # path_to_itog_file = sys.argv[1]
    path_to_itog_file = r'C:\Users\Antua\PycharmProjects\config3\testfile.txt'
    main(path_to_itog_file)
