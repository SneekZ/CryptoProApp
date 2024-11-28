import json


def load_global_parameters(file_path="modules/default_parameters.json"):
    try:
        with open(file_path, "r") as file:
            parameters = json.load(file)  # Читаем JSON
        return parameters

    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")
    except json.JSONDecodeError:
        print(f"Ошибка при разборе JSON в {file_path}.")
