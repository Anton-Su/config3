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

    def parse_array(value):
        value = value.strip()[1:-1]
        elements = []
        nested_level = 0
        buffer = ""
        for char in value:
            if char == "[":
                nested_level += 1
            elif char == "]":
                nested_level -= 1
            if char == "," and nested_level == 0:
                elements.append(buffer.strip())
                buffer = ""
            else:
                buffer += char
        if buffer:
            elements.append(buffer.strip())
        parsed_elements = []
        for element in elements:
            if re.fullmatch(stroka, element):  # Строки
                parsed_elements.append(element.strip('"'))
            elif element in special_values:  # Специальные значения
                parsed_elements.append(float(element.replace("+", "")))
            elif re.fullmatch(digit, element):  # Числа
                parsed_elements.append(float(element) if '.' in element or 'e' in element.lower() else int(element))
            elif element in ["true", "false"]:  # Булевы значения
                parsed_elements.append(element == "true")
            elif re.fullmatch(array_pattern, element):  # Вложенные массивы
                parsed_elements.append(parse_array(element))
            else:
                print(f"INVALID ARRAY ELEMENT: {element}")
                return None
        return parsed_elements
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
                commentary = line[line.find("#", index, len(line) - 1):]
                line = line[:line.find("#", index, len(line) - 1)].strip()
                break
            else:
                if line.find('"', index + 1, len(line) - 1) == -1 or line.find("'", index + 1, len(line) - 1):
                    index = index + 1
                else:
                    index = min(line.find("'", index + 1, len(line) - 1), line.find('"', index + 1, len(line) - 1))
                    kavishi_count += 1
        if len(line) == 0:  # Пропускаем пустые строки
            continue
        print("Комментарий:", commentary)
        if line.startswith("[") and line.endswith("]"):
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
            if re.fullmatch(stroka, value):  # Строка
                target[final_key] = value.strip('"')
            elif value in special_values:  # Специальные значения
                target[final_key] = float(value.replace("+", ""))
            elif re.fullmatch(digit, value):  # Число
                target[final_key] = float(value) if '.' in value or 'e' in value.lower() else int(value)
            elif value in ["true", "false"]:  # Булевы значения
                target[final_key] = value == "true"
            elif re.fullmatch(date_time_sm, value) or re.fullmatch(date_time, value) or re.fullmatch(date, value) or re.fullmatch(time, value):
                target[final_key] = value
            elif re.fullmatch(array_pattern, value):  # Массивы
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
    print(parsed_data)
    return parsed_data


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
