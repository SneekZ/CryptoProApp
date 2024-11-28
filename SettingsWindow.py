import sys
import json
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QLineEdit, QCheckBox, QPushButton, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


from ssh_connection_service import SshConnection
from typing import cast

from modules.load_global_parameters import load_global_parameters


class SettingsWindow(QMainWindow):
    def __init__(self, lpu, json_file="modules/default_parameters.json"):
        super().__init__()

        self.lpu = cast(SshConnection, lpu)

        self.json_file = json_file
        self.parameters = self.load_parameters()

        self.setWindowTitle("Редактирование параметров")
        self.setGeometry(100, 100, 500, 300)

        self.init_ui()

        self.set_style()

    def load_parameters(self):
        """Загружает параметры из JSON-файла."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить параметры:\n{e}")
            sys.exit(1)

    def save_parameters(self):
        """Сохраняет параметры в JSON-файл."""
        try:
            with open(self.json_file, "w", encoding="utf-8") as file:
                json.dump(self.parameters, file, indent=4, ensure_ascii=False)
            self.lpu.update_parameters()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить параметры:\n{e}")

    def init_ui(self):
        """Создаёт интерфейс окна."""
        central_widget = QWidget()
        layout = QVBoxLayout()

        self.fields = {}  # Хранилище для виджетов параметров

        for key, param in self.parameters.items():
            row_layout = QHBoxLayout()
            label = QLabel(param["name"])
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            if param["type"] == "bool":  # Переключатель для булевых значений
                widget = QCheckBox()
                widget.setChecked(param["value"])
                widget.stateChanged.connect(lambda state, key=key: self.update_parameter(key, state == 2))

            elif param["type"] == "file":  # Выпадающее меню для выбора файла
                widget = QComboBox()
                path = param.get("path", ".")  # Директория из параметра, по умолчанию текущая
                try:
                    files = os.listdir(path)  # Список файлов в директории
                    for file in files:
                        widget.addItem(file)  # Добавляем файлы в выпадающее меню
                    widget.setCurrentText(param["value"])  # Устанавливаем текущее значение
                except FileNotFoundError:
                    QMessageBox.warning(self, "Ошибка", f"Директория {path} не найдена.")
                widget.currentTextChanged.connect(lambda text, key=key: self.update_parameter(key, text))

            else:  # Текстовое поле для int или string
                widget = QLineEdit(str(param["value"]))
                widget.textChanged.connect(lambda text, key=key: self.update_parameter(key, text))

            row_layout.addWidget(label, 2)
            row_layout.addWidget(widget, 3)

            layout.addLayout(row_layout)
            self.fields[key] = widget

        # Кнопки сохранения и выхода
        button_layout = QHBoxLayout()
        save_button = QPushButton("Сохранить и выйти")
        save_button.clicked.connect(self.save_and_exit)

        exit_button = QPushButton("Выйти без сохранения")
        exit_button.clicked.connect(self.close)

        button_layout.addWidget(save_button)
        button_layout.addWidget(exit_button)
        layout.addLayout(button_layout)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_parameter(self, key, value):
        """Обновляет параметр в словаре."""
        param_type = self.parameters[key]["type"]
        if param_type == "int":
            try:
                value = int(value)
            except ValueError:
                return
        elif param_type == "bool":
            value = bool(value)
        elif param_type == "file":
            value = str(value)  # Убедимся, что значение преобразовано в строку
        self.parameters[key]["value"] = value

    def save_and_exit(self):
        """Сохраняет параметры и закрывает окно."""
        self.save_parameters()
        self.close()

    def set_style(self, filename="themes/dark.qss"):
        try:
            parameters = load_global_parameters()
            if "STYLESHEET_FILE" in parameters:
                stylesheet_file = "themes/" + self.lpu.parameters["STYLESHEET_FILE"]["value"]
            with open(filename, "r") as file:
                stylesheet = file.read()
                self.setStyleSheet(stylesheet)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка при смене стиля", str(e).strip())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Путь к вашему JSON-файлу
    json_file_path = "modules/default_parameters.json"
    window = SettingsWindow(json_file_path)
    window.show()

    sys.exit(app.exec())
