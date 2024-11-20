import sys
import os
import keyboard
import time
import threading
import re


def read_input(text):
    for line in sys.stdin:
        if line.strip():
            text.append(line.strip())
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
    parse(text)


def parse(text):
    dict = {}
    for line in text:
        line = line.strip()  # учебный язык не позволяет заглавную первую
        if re.fullmatch("\S+\.\s*=\s*\S+", line):
            print("Empty bare keys are not allowed")
            break
        if re.fullmatch(".+\s?=", line):
            print("Empty value")
            break
        if re.fullmatch("[\w][_a-zA-Z0-9]*(\s*\"?\.\s*\"?[_a-zA-Z0-9]+)*\s*=\s*[^=]+", line):  # объявление переменной
            name, key = line.split("=")
            while " " in name:
                name = name.replace(" ", "")
            key = key.strip()
            print(name)
            print(key)
            if key in dict:
                print("Can't redefine existing key")
                break
        else:
            print("INVALIDE CHARACTER")
            break
        # комментарии
        # for symbol in range(len(line)):
        #     if symbol == "'":
        #
        #     print(symbol)


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
