import sys
import os
import time
import threading
import re
from pprint import pformat
import keyboard

commentaries = []
error_perechod = []
massiv_var = []
patterns = {
        "datetime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,9})?(Z|([+-]\d{2}:\d{2}))?$",
        "date": r"^\d{4}-\d{2}-\d{2}$",
        "time": r"^\d{2}:\d{2}:\d{2}(\.\d{1,9})?Z?$",
        "digit": r'^[+-]?\d+(\.\d+)?([eE][+-]?\d+)?$',
        "string": r'^".*"$',
        "array": r'^\[.*\]$',
        "table": r"^\s*\[[^\s\[\].]+(\s*\.\s*[^\s\[\].]+)*\]\s*$",
        "key_value": r'^[a-zA-Z_"-][\w"_.-]*\s*=\s*.+$',
        "dictionary": r'^\{.*\}$',
        "ucheb": r"[_A-Z][_a-zA-Z0-9]*",
    }


def read_input(text: list):
    for line in sys.stdin:
        line = line.strip()
        if line:
            commentary = ''
            index = 0
            while line.find("#", index, len(line) - 1) != -1:  # Кавычки и комментарии
                kavishi_count = 0
                if (line.find("#", index, len(line) - 1) < line.find('"', index, len(line) - 1) or line.find('"', index, len(line) - 1) == -1) and kavishi_count % 2 == 0:
                    commentary = line[line.find("#", index, len(line) - 1) + 1:]
                    line = line[:line.find("#", index, len(line) - 1)].strip()
                    break
                else:
                    if line.find('"', index + 1, len(line) - 1) == -1:
                        index = index + 1
                    else:
                        index = line.find('"', index + 1, len(line) - 1)
                        kavishi_count += 1
            if commentary:
                commentaries.append(commentary)
            if line:
                text.append(line)


def read_input_after(text: list):
    count_massiv = 0
    count_slovar = 0
    new_massiv = []
    for i in range(len(text)):
        count_massiv_2 = text[i].count("[") - text[i].count("]")
        count_slovar_2 = text[i].count("{") - text[i].count("}")
        if count_slovar == 0 and count_massiv == 0:  # свободная линия
            new_massiv.append(text[i])
        else:
            new_massiv[-1] += text[i]
        count_massiv += count_massiv_2
        count_slovar += count_slovar_2
    return new_massiv


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


def key_split(value):
    elements = []
    buffer = ""
    kavishi_count = 0
    for char in value:
        if char == '"':
            kavishi_count += 1
        if char == "." and kavishi_count % 2 == 0:
            elements.append(buffer.strip())
            buffer = ""
        else:
            buffer += char
    if buffer.strip():
        elements.append(buffer.strip())
    return elements


def point_key(dict, table_name):
    if table_name.count('""'):
        print('"" Is not allowed')
        return
    keys = key_split(table_name)
    current_target = dict
    for k in keys[:-1]:
        if not re.fullmatch(patterns["ucheb"], k):
            error_perechod.append(f"{k} cannot convert to ucheb")
        if re.fullmatch(patterns["digit"], k):
            print(f"{k} CAN NOT BE INT")
            return
        current_target = current_target.setdefault(k, {})
    final_key = keys[-1]
    if not re.fullmatch(patterns["ucheb"], final_key):
        error_perechod.append(f"{final_key} cannot convert to ucheb")
    if re.fullmatch(patterns["digit"], final_key):
        print(f'BARE KEY SUCH AS {final_key} CAN NOT BE DIGIT, USE DIGITS WITH "" instead')
        return
    if final_key in current_target:
        print(f"INVALID REDEFINITION OF KEY '{final_key}'")
        return
    return current_target, final_key


def parse_array(value, dict):
    elements = prepare(value)
    parsed_elements = []
    for element in elements:
        if re.fullmatch(patterns["string"], element):
            parsed_elements.append(element.strip('"'))
            error_perechod.append(f"{element} - stroka_error")
        elif element in {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}:
            parsed_elements.append(float(element.replace("+", "")))
            error_perechod.append(f"{element} - special_elements_error")
        elif re.fullmatch(patterns["digit"], element):
            parsed_elements.append(float(element) if '.' in element or 'e' in element.lower() else int(element))
        elif element in ["true", "false"]:
            parsed_elements.append(element == "true")
            error_perechod.append(f"{element} - boolean_error")
        elif re.fullmatch(patterns["datetime"], element) or re.fullmatch(patterns["date"], element) or re.fullmatch(patterns["time"], element):
            parsed_elements.append(element)
            error_perechod.append(f"{element} - date_time_error")
        elif re.fullmatch(patterns["array"], element):  # Вложенные массивы
            result = parse_array(element, dict)
            if result is None:
                return
            parsed_elements.append(result)
        elif re.fullmatch(patterns["dictionary"], element):  # словарь, но в массиве нет разницы, повторялось ли что-то!
            novii = {}
            parsed_value = parse_dict(element, novii)
            if parsed_value is None:
                return
            parsed_elements.append(parsed_value)
        else:
            print(f'INVALID ELEMENT IN ARRAY: "{element}"')
            return
    return parsed_elements


def parse_dict(value, dict):
    elements = prepare(value)
    for element in elements:
        if not re.fullmatch(patterns["key_value"], element):
            print(f"INVALID DICT: {element}")
            return
        key, val = map(str.strip, element.split("=", 1))
        result = point_key(dict, key)
        if not result:
            return
        current_target, final_key = result[0], result[1]
        if re.fullmatch(patterns["string"], val):
            parsed_value = val.strip('"')
            error_perechod.append(f"{val} - stroka_error")
        elif val in {"true", "false"}:
            parsed_value = val == "true"
            error_perechod.append(f"{val} - boolean_error")
        elif re.fullmatch(patterns["digit"], val):
            parsed_value = f'!"{final_key}"!'
            massiv_var.append("var " + final_key + " := " + str(float(val)) if '.' in val or 'e' in val.lower() else "var " + final_key + " := " + str(int(val)))
        elif re.fullmatch(patterns["datetime"], val) or re.fullmatch(patterns["date"], val) or re.fullmatch(patterns["time"], val):
            parsed_value = val
            error_perechod.append(f"{val} - date_time_error")
        elif re.fullmatch(patterns["array"], val):  # Массив
            parsed_value = parse_array(val, current_target)
            if parsed_value is None:
                return
            massiv_var.append("var " + final_key + " := " + str(parsed_value))
            parsed_value = f'!"{final_key}"!'
        elif re.fullmatch(patterns["dictionary"], val):  # Вложенный словарь
            if parse_dict(val, current_target.setdefault(final_key, {})) is None:
                return
            continue
        else:
            print(f'INVALID DICT VALUE: "{val}"')
            return
        if final_key not in current_target:
            current_target[final_key] = parsed_value
        else:
            print(f'INVALID REDEFINITION OF TABLE "{final_key}"')
            return
    return dict


def parse(lines):
    lines = read_input_after(lines)
    dict = {"Root": {}}
    current_table = dict["Root"]
    for line in lines:
        if re.fullmatch(patterns["table"], line):
            table_name = line.strip()[1:-1]
            result = point_key(dict, table_name)
            if not result:
                return
            result[0][result[1]] = {}
            continue
        if re.fullmatch(patterns["key_value"], line):
            key, value = map(str.strip, line.split("=", 1))
            result = point_key(current_table, key)
            if not result:
                return
            current_target, final_key = result[0], result[1]
            if re.fullmatch(patterns["string"], value):
                current_target[final_key] = value.strip('"')
                error_perechod.append(f"{value} - stroka_error")
            elif value in {"inf", "+inf", "-inf", "nan", "+nan", "-nan"}:
                current_target[final_key] = float(value.replace("+", ""))
                error_perechod.append(f"{value} - inf_error")
            elif re.fullmatch(patterns["digit"], value):
                current_target[final_key] = float(value) if '.' in value or 'e' in value.lower() else int(value)
            elif value in ["true", "false"]:
                current_target[final_key] = value == "true"
                error_perechod.append(f"{value} - boolean_error")
            elif re.fullmatch(patterns["datetime"], value) or re.fullmatch(patterns["date"], value) or re.fullmatch(patterns["time"], value):
                current_target[final_key] = value
                error_perechod.append(f"{value} - date_time_error")
            elif re.fullmatch(patterns["array"], value):
                parsed_array = parse_array(value, current_target)
                if parsed_array is None:
                    return
                current_target[final_key] = parsed_array
            elif re.fullmatch(patterns["dictionary"], value):
                if parse_dict(value, current_target.setdefault(final_key, {})) is None:
                    return
            else:
                print(f'INVALID VALUE FOR KEY "{key}"')
                return
            continue
        print(f'INVALID LINE: "{line}"')
        return
    print(dict)
    return dict


def write_output(path, data):
    with open(path, mode="w", encoding="utf-16") as f:
        if len(commentaries) > 0:
            f.write("|#\n")
            for comment in commentaries:
                f.write(comment + "\n")
            f.write("#|\n\n")
        for var in massiv_var:
            f.write(var.replace(": ", " = ").replace("[", "(").replace("]", ")").replace("'", "").replace('!"', '![').replace('"!', ']') + "\n")
        if len(massiv_var) > 0:
            f.write('\n')
        f.write("{\n")
        formatted = pformat(data).replace(": ", " = ").replace("[", "(").replace("]", ")").replace("'", "").replace('!"', '![').replace('"!', ']')
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
    dict = parse(text)
    if dict:
        print("Файл TOML верный, перехожу к переводу в учебный язык->")
        if len(error_perechod) > 0:
            print(f"Возникли следующие ошибки при переводе из TOML в учебный язык:")
            for i in range(len(list(dict.fromkeys(error_perechod))) - 1):
                print(f'{i + 1}) {list(dict.fromkeys(error_perechod))[i]};')
            print(f'{len(list(dict.fromkeys(error_perechod)))}) {list(dict.fromkeys(error_perechod))[-1]}.')
            print("Преобразование в учебный язык невозможно!")
            return
        write_output(path_to_itog_file, dict)
        print("Успешное преобразование!")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Неверные аргументы")
        exit(1)
    main(sys.argv[1])