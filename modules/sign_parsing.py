import re
from datetime import datetime
from modules.extract_between import extract_between


def parse_sign(sign_data):
    date_format = '%d/%m/%Y  %H:%M:%S %Z'
    keys_eng = ["Issuer", "Subject", "SHA1 Hash",
            "Not valid before", "Not valid after", "Container"]
    keys_rus = ["Издатель", "Субъект", "SHA1 отпечаток", "Выдан", "Истекает", "Контейнер"]
    keys = zip(keys_eng, keys_rus)
    structured_data = {}

    ru = False

    for key_eng, key_ru in keys:
        start_index = sign_data.find(key_eng)
        if start_index == -1:
            start_index = sign_data.find(key_ru)
            ru = True
        if start_index != -1:
            end_index = sign_data.find("\n", start_index)
            line = sign_data[start_index:end_index] if end_index != -1 else sign_data[start_index:]
            if not ru:
                key = key_eng
                if key in ("Issuer", "Subject"):
                    matches = re.findall(r"(\w+)=([^,]+)", line)
                    structured_data[key] = dict(matches)
                else:
                    if key in ("Not valid before", "Not valid after"):
                        structured_data[key] = datetime.strptime(line.split(" : ")[-1].strip(), date_format)
                    else:
                        structured_data[key] = line.split(" : ")[-1].strip()
            else:
                key = key_ru
                if key in ("Издатель", "Субъект"):
                    matches = re.findall(r"(\w+)=([^,]+)", line)
                    structured_data[key_eng] = dict(matches)
                else:
                    if key in ("Not valid before", "Not valid after"):
                        structured_data[key_eng] = datetime.strptime(line.split(" : ")[-1].strip(), date_format)
                    else:
                        structured_data[key_eng] = line.split(" : ")[-1].strip()
    return structured_data


def parse_sings_to_array(data):
    return list(filter(lambda text: text, map(lambda text: text.strip("\n") if text else None, re.split("\d+-------", data))))


def parse_error_code(data):
    error_code = data.strip().strip('[]').split(":")[-1].strip()
    return error_code


def is_error(error_code):
    return error_code != "0x00000000"


def parse(out, err):
    full_data = out.split("=============================================================================")

    error_code_raw = full_data[-1]
    error_code = parse_error_code(error_code_raw)

    isError = is_error(error_code)

    if isError:
        return err.strip(), isError
    else:
        return [parse_sign(part_data) for part_data in parse_sings_to_array(full_data[1])], isError


def parse_find_text(find_text):
    if find_text:
        find_text_splited = list(map(lambda s: s.strip(), find_text.split(',')))
        return find_text_splited
    else:
        return []


def is_error_in_exec(text):
    error_code = extract_between(text, "[ErrorCode: ", "]")
    return is_error(error_code)


def parse_config_py(data):
    hash = re.findall(r"PASSWORD_MO = u'(\w+)'\n", data)
    if hash:
        return hash[0], "hash"
    snils = re.findall(r"CERT_MO = u'(\d+)'\n", data)
    if snils:
        return snils[0], "snils"
    return "", None



if __name__=="__main__":
    pass