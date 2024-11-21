import sys
import os
from pprint import pformat
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
    error = False
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
            error = True
        elif element in {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}:  # Специальные значения
            parsed_elements.append(float(element.replace("+", "")))
            error = True
        elif re.fullmatch(r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$", element):  # Числа (целые и с плавающей запятой)
            if '.' in element or 'e' in element.lower():  # Число с плавающей запятой
                parsed_elements.append(float(element))
            else:  # Целое число
                parsed_elements.append(int(element))
        elif element in ["true", "false"]:  # Булевы значения
            parsed_elements.append(element == "true")
            error = True
        elif re.fullmatch(r'^\[.*\]$', element):  # Вложенные массивы
            parsed_value = parse_array(element)
            parsed_elements.append(parsed_value)
        else:
            print(f"INVALID ELEMENT IN ARRAY: {element}")
            return None
    return parsed_elements, error


def parse(text):
    date_time_sm = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?(Z|([+-])\d{2}:\d{2})$"
    date_time = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z?$"
    date = r"^\d{4}-\d{2}-\d{2}$"
    time = r"^\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z?$"
    digit = r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$"
    special_values = {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}
    stroka = r'^".*"$'
    array_pattern = r'^\[.*\]$'
    table_name_pattern = r"^\s*\[[^\s\[\].]+(\s*\.[^\s\[\].]+)*\]\s*$"
    base = r"^[\w\"'_-][\w\"'_.-]*\s*=\s*.+"
    parsed_data = {"Root": {}}  # Инициализируем с таблицей по умолчанию 'Root'
    current_table = parsed_data["Root"]  # По умолчанию используем таблицу 'Root'
    commentary_massiv = []
    error_perechod = False
    defined_tables = set()
    for line in text:
        line = line.strip()
        commentary = ''
        index = 0
        while line.find("#", index, len(line) - 1) != -1:  # кавычки и комментарии
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
        if re.fullmatch(table_name_pattern, line):
            table_name = line.strip()[1:-1]
            if not table_name:
                print("INVALID TABLE NAME")
                return
            keys = table_name.split(".")  # Вложенные таблицы
            target = parsed_data
            for key in keys:
                if key not in target:
                    target[key] = {}
                    if not re.fullmatch(r"[_A-Z][_a-zA-Z0-9]*", key):
                        error_perechod = True
                elif not isinstance(target[key], dict):
                    print(f"INVALID REDEFINITION OF TABLE '{key}'")
                    return
                target = target[key]
            if table_name in defined_tables:  # Проверяем, не была ли таблица уже объявлена ранее
                print(f"INVALID REDEFINITION OF TABLE '{table_name}'")
                return
            if not re.fullmatch(r"[_A-Z][_a-zA-Z0-9]*", keys[-1]):
                error_perechod = True
            defined_tables.add(table_name)
            current_table = target
            continue
        if re.fullmatch(base, line):
            name, value = line.split("=", 1)
            name = name.strip()
            value = value.strip()
            keys = name.split(".")
            target = current_table if current_table is not None else parsed_data
            for key in keys[:-1]:
                if key not in target:
                    if not re.fullmatch(r"[_A-Z][_a-zA-Z0-9]*", key):
                        error_perechod = True
                    target[key] = {}
                elif not isinstance(target[key], dict):
                    print(f"INVALID REDEFINITION OF KEY '{key}'")
                    return
                target = target[key]
            final_key = keys[-1]
            if final_key in target:
                print(f"INVALID REDEFINITION OF KEY '{final_key}'")
                return
            if not re.fullmatch(r"[_A-Z][_a-zA-Z0-9]*", final_key):
                error_perechod = True
            if re.fullmatch(stroka, value):  # обрабатываем.значения
                target[final_key] = value.strip('"')
                error_perechod = True
            elif value in special_values:
                target[final_key] = float(value.replace("+", ""))
                error_perechod = True
            elif re.fullmatch(digit, value):
                target[final_key] = float(value) if '.' in value or 'e' in value.lower() else int(value)
            elif value in ["true", "false"]:
                target[final_key] = value == "true"
                error_perechod = True
            elif re.fullmatch(date_time_sm, value) or re.fullmatch(date_time, value) or re.fullmatch(date,
                                                                                                     value) or re.fullmatch(
                    time, value):
                target[final_key] = value
                error_perechod = True
            elif re.fullmatch(array_pattern, value):
                if parse_array(value) is None:
                    return
                parsed_array, error = parse_array(value)
                target[final_key] = parsed_array
                if error:
                    error_perechod = error
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


def write(path_to_itog_file, text, commentaries):
    with open(path_to_itog_file, mode="w", encoding="utf-16") as f:
        f.write("|#\n")
        for i in commentaries:
            f.write(i.strip() + "\n")
        beautiful = str(pformat(text))
        f.write("#|\n")
        f.write("var result := " + beautiful.replace(": ", " = ").replace("[", "(").replace("]", ")"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Аргументы указаны неверно")
        exit()
    path_to_itog_file = sys.argv[1]
    main(path_to_itog_file)
