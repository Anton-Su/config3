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





def parse_array(value):
    value = value.strip()[1:-1]  # минус внешние квадратные скобки
    elements = []
    cont = ""
    level = 0
    for char in value:
        if char == "[":
            level += 1
        elif char == "]":
            level -= 1
        if char == "," and level == 0:
            elements.append(cont.strip())
            cont = ""
        else:
            cont += char
    if cont.strip():
        elements.append(cont.strip())
    parsed_elements = []
    for element in elements:
        element = element.strip()
        if re.fullmatch(r'^".*"$', element):  # Строки
            parsed_value = element.strip('"')
            parsed_elements.append(parsed_value)
        elif element in {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}:  # Специальные значения
            parsed_elements.append(float(element.replace("+", "")))
        elif re.fullmatch(r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$", element):  # Числа (целые и с плавающей запятой)
            if '.' in element or 'e' in element.lower():  # Число с плавающей запятой
                parsed_elements.append(float(element))
            else:  # Целое число
                parsed_elements.append(int(element))
        elif element in ["true", "false"]:  # Булевы значения
            parsed_elements.append(element == "true")
        elif re.fullmatch(r'^\[.*\]$', element):  # Вложенные массивы
            parsed_value = parse_array(element)
            parsed_elements.append(parsed_value)
        else:
            print(f"INVALID ELEMENT IN ARRAY: {element}")
            return None
    return parsed_elements


def parse(text):
    date_time_sm = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?(Z|([+-])\d{2}:\d{2})$"
    date_time = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z?$"
    date = r"^\d{4}-\d{2}-\d{2}$"
    time = r"^\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z?$"
    digit = r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$"
    special_values = {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}
    stroka = r'^".*"$'
    array_pattern = r'^\[.*\]$'
    base = r"^[\w\"'_-][\w\"'_.-]*\s*=\s*.+"
    parsed_data = {}
    defined_tables = set()
    current_table = None
    commentary_massiv = []
    error_perechod = False
    for line in text:
        line = line.strip()
        commentary = ''
        index = 0
        while line.find("#", index, len(line) - 1) != -1:
            kavishi_count = 0
            if ((line.find("#", index, len(line) - 1) < line.find('"', index, len(line) - 1)
                 or line.find('"', index, len(line) - 1) == -1) or (
                        line.find("#", index, len(line) - 1) < line.find("'", index, len(line) - 1)
                        or line.find("'", index, len(line) - 1) == -1)) and kavishi_count % 2 == 0:
                commentary = line[line.find("#", index, len(line) - 1) + 1:]
                line = line[:line.find("#", index, len(line) - 1)].strip()
                break
            else:
                if line.find('"', index + 1, len(line) - 1) == -1 or line.find("'", index + 1, len(line) - 1):
                    index = index + 1
                else:
                    index = min(line.find("'", index + 1, len(line) - 1), line.find('"', index + 1, len(line) - 1))
                    kavishi_count += 1
        if commentary:
            commentary_massiv.append(commentary)
        if len(line) == 0:
            continue
        if line.startswith("[") and line.endswith("]"):
            if not (line.count("[") == 1 and line.count("]") == 1 and line.find("]") == len(line) - 1):
                print("too many operations")
                return
            table_name = line[1:-1].strip()
            if not table_name:
                print("INVALID TABLE NAME")
                return
            if table_name in defined_tables:
                print(f"Table '{table_name}' already defined")
                return
            defined_tables.add(table_name)
            parsed_data[table_name] = {}
            current_table = parsed_data[table_name]
            continue
        if re.fullmatch(base, line):
            name, value = line.split("=", 1)
            if not re.fullmatch(r"[_A-Z][_a-zA-Z0-9]*", name):
                error_perechod = True
            name = name.strip()
            value = value.strip()
            keys = name.split(".")
            target = current_table if current_table is not None else parsed_data
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                elif not isinstance(target[key], dict):
                    print(f"INVALID REDEFINITION OF KEY '{key}'")
                    return
                target = target[key]
            final_key = keys[-1]
            if final_key in target:
                print(f"Key '{final_key}' already exists")
                return
            if re.fullmatch(stroka, value):
                target[final_key] = value.strip('"')
            elif value in special_values:
                target[final_key] = float(value.replace("+", ""))
            elif re.fullmatch(digit, value):
                target[final_key] = float(value) if '.' in value or 'e' in value.lower() else int(value)
            elif value in ["true", "false"]:
                target[final_key] = value == "true"
            elif re.fullmatch(date_time_sm, value) or re.fullmatch(date_time, value) or re.fullmatch(date, value) or re.fullmatch(time, value):
                target[final_key] = value
            elif re.fullmatch(array_pattern, value):
                parsed_array = parse_array(value)
                if parsed_array is None:
                    return
                target[final_key] = parsed_array
            else:
                print(f"INVALID VALUE FOR KEY '{name}'")
                return
            continue
        print("INVALID LINE:", line)
        return
    return parsed_data, commentary_massiv, error_perechod


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
    if parse(text):
        dict, commentaries, error = parse(text)
        print("файл toml верный")
        if error:
           print("ошибка записи, конвертирование невозможно")
           return
        write(path_to_itog_file, dict, commentaries)


def write(path_to_itog_file, text, commentaries):  # где-то уже в конце
    with open(path_to_itog_file, mode="w") as f:
        f.write("|#\n")
        for i in commentaries:
            f.write(i + "\n")
        f.write("#|\n")
        f.write("var top_table := " + str(text).replace(": ", " = ").replace("'", "").replace("[", "(").replace("]", ")"))


if __name__ == "__main__":
     if len(sys.argv) != 2:
         print("Аргументы указаны неверно")
         exit()
     path_to_itog_file = sys.argv[1]
     # path_to_itog_file = r'C:\Users\Antua\PycharmProjects\config3\testfile.txt'
     main(path_to_itog_file)
