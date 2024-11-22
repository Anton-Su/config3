import sys
import os
import time
import threading
import re
from pprint import pformat
import keyboard


error_perechod = False
massiv_var = []


def read_input(buffer):
    for line in sys.stdin:
        if line.strip():
            buffer.append(line.strip())
        time.sleep(0.1)


def parse_array(value):
    global error_perechod
    value = value.strip()[1:-1]  # Убираем внешние квадратные скобки
    elements = []
    buffer = ""
    level = 0
    for char in value:
        if char == "[":
            level += 1
        elif char == "]":
            level -= 1
        if char == "," and level == 0:
            elements.append(buffer.strip())
            buffer = ""
        else:
            buffer += char
    if buffer.strip():
        elements.append(buffer.strip())
    parsed_elements = []
    for element in elements:
        element = element.strip()
        if re.fullmatch(r'^".*"$', element):  # Строки
            parsed_elements.append(element.strip('"'))
            error_perechod = True
        elif element in {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}:  # Специальные значения
            parsed_elements.append(float(element.replace("+", "")))
            error_perechod = True
        elif re.fullmatch(r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$", element):  # Числа
            parsed_elements.append(float(element) if '.' in element or 'e' in element.lower() else int(element))
        elif element in ["true", "false"]:  # Булевы значения
            parsed_elements.append(element == "true")
            error_perechod = True
        elif re.fullmatch(r'^\[.*\]$', element):  # Вложенные массивы
            parsed_elements.append(parse_array(element))
        elif re.fullmatch(r'^\{.*\}$', element):  # словарь
            parsed_value = parse_dict(element)
            if parsed_value is None:
                return None
            parsed_elements.append(parsed_value)
        else:
            print(f"INVALID ELEMENT IN ARRAY: {element}")
            return None
    return parsed_elements


def parse_dict(value):
    global massiv_var
    global error_perechod
    if not value.startswith("{") or not value.endswith("}"):
        print(f"INVALID DICTIONARY FORMAT: {value}")
        return None
    value = value.strip()[1:-1]  # Убираем внешние скобки
    elements = []
    buffer = ""
    level = 0
    for char in value:
        if char == "[":
            level += 1
        elif char == "]":
            level -= 1
        if char == "," and level == 0:
            elements.append(buffer.strip())
            buffer = ""
        else:
            buffer += char
    if buffer.strip():
        elements.append(buffer.strip())
    parsed_dict = {}
    for element in elements:
        if "=" not in element:
            print(f"INVALID DICTIONARY ENTRY: {element}")
            return None
        key, val = map(str.strip, element.split("=", 1))
        if not re.fullmatch(r"[_a-zA-Z][_a-zA-Z0-9]*", key):
            print(f"INVALID DICT KEY: {key}")
            return None
        if re.fullmatch(r'^".*"$', val):  # Строка
            parsed_value = val.strip('"')
            error_perechod = False
        elif val in {"true", "false"}:  # Булевы значения
            parsed_value = val == "true"
            error_perechod = False
        elif re.fullmatch(r"^[+-]?\d*(\.\d+)?([eE][+-]?\d+)?$", val):  # Числа
            parsed_value = f"![{key}]"
            massiv_var.append("var " + key + " := " + str(float(val)) if '.' in val or 'e' in val.lower() else "var " + key + " := " + str(int(val)))
        elif re.fullmatch(r'^\[.*\]$', val):  # Массив
            parsed_value = parse_array(val)
            if parsed_value is None:
                return None
            massiv_var.append("var " + key + " := " + parsed_value)
            parsed_value = f"![{key}]"
        elif re.fullmatch(r'^\{.*\}$', val):  # Вложенный словарь
            parsed_value = parse_dict(val)
            if parsed_value is None:
                return None
        else:
            print(f"INVALID DICT VALUE: {val}")
            return None
        parsed_dict[key] = parsed_value
    return parsed_dict


def parse(lines):
    global error_perechod
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
    parsed_data = {"Root": {}}
    current_table = parsed_data["Root"]
    defined_tables = set()
    commentaries = []
    for line in lines:
        line = line.strip()
        if "#" in line:
            line, comment = line.split("#", 1)
            commentaries.append(comment.strip())
            line = line.strip()
        if not line:
            continue
        if re.fullmatch(patterns["table"], line):
            table_name = line.strip()[1:-1]
            keys = table_name.split(".")
            current_table = parsed_data
            for key in keys:
                current_table = current_table.setdefault(key, {})
            if table_name in defined_tables:
                print(f"INVALID REDEFINITION OF TABLE '{table_name}'")
                return
            defined_tables.add(table_name)
            continue
        if re.fullmatch(patterns["key_value"], line):
            key, value = map(str.strip, line.split("=", 1))
            keys = key.split(".")
            target = current_table
            for k in keys[:-1]:
                target = target.setdefault(k, {})
            final_key = keys[-1]
            if final_key in target:
                print(f"INVALID REDEFINITION OF KEY '{final_key}'")
                return
            if re.fullmatch(patterns["string"], value):
                target[final_key] = value.strip('"')
                error_perechod = True
            elif value in {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}:
                target[final_key] = float(value.replace("+", ""))
                error_perechod = True
            elif re.fullmatch(patterns["digit"], value):
                target[final_key] = float(value) if '.' in value or 'e' in value.lower() else int(value)
            elif value in ["true", "false"]:
                target[final_key] = value == "true"
            elif re.fullmatch(patterns["datetime"], value) or re.fullmatch(patterns["date"], value) or re.fullmatch(patterns["time"], value):
                target[final_key] = value
                error_perechod = True
            elif re.fullmatch(patterns["array"], value):
                parsed_array = parse_array(value)
                if parsed_array is None:
                    return
                target[final_key] = parsed_array
            elif re.fullmatch(patterns["dictionary"], value):
                parsed_dict = parse_dict(value)
                if parsed_dict is None:
                    return
                target[final_key] = parsed_dict
            else:
                print(f"INVALID VALUE FOR KEY '{key}'")
                return
            continue
        print(f"INVALID LINE: {line}")
        return
    return parsed_data, commentaries


def write_output(path, data, commentaries):
    with open(path, mode="w", encoding="utf-16") as f:
        f.write("|#\n")
        for comment in commentaries:
            f.write(comment + "\n")
        f.write("#|\n")
        for var in massiv_var:
            f.write(var + "\n")
        f.write("{\n")
        formatted = pformat(data).replace(": ", " = ").replace("[", "(").replace("]", ")")
        f.write(formatted)
        f.write("\n}")


def main(output_path):
    directory = os.path.dirname(output_path)
    if not os.path.isdir(directory):
        print("Invalid directory")
        return
    lines = []
    input_thread = threading.Thread(target=read_input, args=(lines,))
    input_thread.start()
    while not keyboard.is_pressed("ctrl+d"):
        time.sleep(0.1)
    result = parse(lines)
    if result:
        parsed_data, commentaries = result
        print("TOML файл корректен")
        if error_perechod:
            print("Ошибка в значениях, конвертация невозможна")
            return
        write_output(output_path, parsed_data, commentaries)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Неверные аргументы")
        exit(1)
    main(sys.argv[1])