import json, os


def get_files_list(directory="lpu_ssh_configs"):
    for filename in os.listdir(directory):
        yield f"{directory}/{filename}"


def get_connection_data_from_json(filepathname):
    try:
        with open(filepathname, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data, False
    except Exception as e:
        return str(e), True


if __name__ == "__main__":
    for i in get_files_list():
        print(get_connection_data_from_json(i))