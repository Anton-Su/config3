import sys
import os
import time
import threading
import re
from pprint import pformat
import keyboard

error_perechod = []
massiv_var = []


def read_input(text):
    for line in sys.stdin:
        if line.strip():
            text.append(line.strip())


def prepare(value):
    value = value.strip()[1:-1]
    elements = []
    buffer = ""
    level_slovar = 0
    level_massiv = 0
    kavishi_count = 0
    for char in value:
        if char == '"':
            kavishi_count += 1
        if char == "{" and kavishi_count % 2 == 0:
            level_slovar += 1
        elif char == "}" and kavishi_count % 2 == 0:
            level_slovar -= 1
        elif char == "[" and kavishi_count % 2 == 0:
            level_massiv += 1
        elif char == "]" and kavishi_count % 2 == 0:
            level_massiv -= 1
        if char == "," and level_slovar == 0 and level_massiv == 0 and kavishi_count % 2 == 0:
            elements.append(buffer.strip())
            buffer = ""
        else:
            buffer += char
    if buffer.strip():
        elements.append(buffer.strip())
    return elements


def parse_array(value):
    elements = prepare(value)
    parsed_elements = []
    for element in elements:
        element = element.strip()
        if re.fullmatch(r'^".*"$', element):  # Строки
            parsed_elements.append(element.strip('"'))
            error_perechod.append("Value_stroka_error")
        elif element in {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}:
            parsed_elements.append(float(element.replace("+", "")))
            error_perechod.append("Value_special_elements")
        elif re.fullmatch(r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$", element):
            parsed_elements.append(float(element) if '.' in element or 'e' in element.lower() else int(element))
        elif element in ["true", "false"]:
            parsed_elements.append(element == "true")
            error_perechod.append("Value_boolean_error")
        elif re.fullmatch(r'^\[.*\]$', element):  # Вложенные массивы
            result = parse_array(element)
            if not result:
                return
            parsed_elements.append(result)
        elif re.fullmatch(r'^\{.*\}$', element):  # словарь
            example = dict()
            parsed_value = parse_dict(element, example)
            if parsed_value is None:
                return
            parsed_elements.append(parsed_value)
        else:
            print(f"INVALID ELEMENT IN ARRAY: {element}")
            return
    return parsed_elements


def parse_dict(value, dict):
    elements = prepare(value)
    for element in elements:
        if not re.fullmatch(r"^[\w\"'_-][\w\"'_.-]*\s*=\s*.+", element):
            print(f"INVALID DICT: {element}")
            return
        key, val = map(str.strip, element.split("=", 1))
        if not re.fullmatch(r"[_A-Z][_a-zA-Z0-9]*", key):
            error_perechod.append("Key is not TOML")
        if re.fullmatch(r'^".*"$', val):
            parsed_value = val.strip('"')
            error_perechod.append("Value_stroka_error")
        elif val in {"true", "false"}:
            parsed_value = val == "true"
            error_perechod.append("Value_boolean_error")
        elif re.fullmatch(r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$", val):
            parsed_value = f"![{key}]"
            massiv_var.append("var " + key + " := " + str(float(val)) if '.' in val or 'e' in val.lower() else "var " + key + " := " + str(int(val)))
        elif re.fullmatch(r'^\[.*\]$', val):  # Массив
            parsed_value = parse_array(val)
            if parsed_value is None:
                return
            massiv_var.append("var " + key + " := " + str(parsed_value))
            parsed_value = f"![{key}]"
        elif re.fullmatch(r'^\{.*\}$', val):  # Вложенный словарь
            kusochek = dict[key] = {}
            if not parse_dict(val, kusochek):
                return
            continue
        else:
            print(f"INVALID DICT VALUE: {val}")
            return
        if key not in dict:
            dict[key] = parsed_value
        else:
            print(f"INVALID REDEFINITION OF TABLE '{key}'")
            return
    return dict


def parse(lines):
    patterns = {
        "datetime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?(Z|([+-]\d{2}:\d{2}))?$",
        "date": r"^\d{4}-\d{2}-\d{2}$",
        "time": r"^\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z?$",
        "digit": r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$",
        "string": r'^".*"$',
        "array": r'^\[.*\]$',
        "table": r"^\s*\[[^\s\[\].]+(\s*\.\s*[^\s\[\].]+)*\]\s*$",
        "key_value": r"^[\w\"'_-][\w\"'_.-]*\s*=\s*.+",
        "dictionary": r'^\{.*\}$',
    }
    dict = {"Root": {}}
    current_table = dict["Root"]
    defined_tables = set()
    commentaries = []
    for line in lines:
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
            commentaries.append(commentary)
        if not line:
            continue
        if re.fullmatch(patterns["table"], line):
            table_name = line.strip()[1:-1]
            keys = table_name.split(".")
            current_table = dict
            for key in keys:
                current_table = current_table.setdefault(key, {})
            if table_name in defined_tables:
                print(f"INVALID REDEFINITION OF TABLE '{table_name}'")
                return
            defined_tables.add(table_name)
            continue
        if re.fullmatch(patterns["key_value"], line):
            key, value = map(str.strip, line.split("=", 1))
            target = current_table
            keys = key.split(".")
            for k in keys[:-1]:
                if not re.fullmatch(r"[_A-Z][_a-zA-Z0-9]*", k):
                    error_perechod.append("Key is not TOML")
                target = target.setdefault(k, {})
            final_key = keys[-1]
            if not re.fullmatch(r"[_A-Z][_a-zA-Z0-9]*", final_key):
                error_perechod.append("Key is not TOML")
            if final_key in target:
                print(f"INVALID REDEFINITION OF KEY '{final_key}'")
                return
            if re.fullmatch(patterns["string"], value):
                target[final_key] = value.strip('"')
                error_perechod.append("Value_stroka_error")
            elif value in {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}:
                target[final_key] = float(value.replace("+", ""))
                error_perechod.append("Value_inf_error")
            elif re.fullmatch(patterns["digit"], value):
                target[final_key] = float(value) if '.' in value or 'e' in value.lower() else int(value)
            elif value in ["true", "false"]:
                target[final_key] = value == "true"
            elif re.fullmatch(patterns["datetime"], value) or re.fullmatch(patterns["date"], value) or re.fullmatch(patterns["time"], value):
                target[final_key] = value
                error_perechod.append("Value_date_time_error")
            elif re.fullmatch(patterns["array"], value):
                parsed_array = parse_array(value)
                if not parsed_array:
                    return
                target[final_key] = parsed_array
            elif re.fullmatch(patterns["dictionary"], value):
                if not parse_dict(value, target):
                    return
            else:
                print(f"INVALID VALUE FOR KEY '{key}'")
                return
            continue
        print(f"INVALID LINE: {line}")
        return
    return dict, commentaries


def write_output(path, data, commentaries):
    with open(path, mode="w", encoding="utf-16") as f:
        f.write("|#\n")
        for comment in commentaries:
            f.write(comment + "\n")
        f.write("#|\n")
        for var in massiv_var[:len(massiv_var) // 2]:
            f.write(var + "\n")
        f.write('\n')
        f.write("{\n")
        formatted = pformat(data).replace(": ", " = ").replace("[", "(").replace("]", ")")
        f.write(formatted)
        f.write("\n}")


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
    result = parse(text)
    if result:
        dict, commentaries = parse(text)
        print("Файл toml верный, перехожу к переводу в учебный язык")
        if len(error_perechod) > 0:
            print(f"Ошибка перевода в учебный язык: {list(dict.fromkeys(error_perechod))} - конвертирование невозможно")
            return
        write_output(path_to_itog_file, dict, commentaries)
        print("Успеx!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Неверные аргументы")
        exit(1)
    main(sys.argv[1])