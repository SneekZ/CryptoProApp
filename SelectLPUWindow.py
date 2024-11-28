import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QMessageBox, QProgressBar, QLabel
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon

from functools import partial
from modules.lpu_service import get_files_list, get_connection_data_from_json
from ssh_connection_service import SshConnection
from modules.load_global_parameters import load_global_parameters


class ConnectionThread(QThread):
    connection_result = pyqtSignal(str)  # Сигнал для передачи результата подключения

    def __init__(self, connection):
        super().__init__()
        self.connection = connection

    def run(self):
        connection_error = self.connection.connect()
        self.connection_result.emit(connection_error)  # Передаём результат подключения


class SelectLPU(QMainWindow):
    def __init__(self):
        super().__init__()

        self.parameters = load_global_parameters()
        stylesheet_file = self.parameters["STYLESHEET_FILE"]["value"]
        self.set_style(stylesheet_file=stylesheet_file)

        self.setWindowTitle("Выбор ЛПУ")
        self.setGeometry(100, 100, 300, 250)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        self.combo_box = QComboBox()
        self.combo_box.setEditable(True)
        self.combo_box.lineEdit().textEdited.connect(self.filter_items)

        self.lpu_data = {}

        for lpu in get_files_list():
            data, is_error = get_connection_data_from_json(lpu)
            if not is_error:
                self.lpu_data[data["name"]] = data

        self.combo_box.addItems(self.lpu_data.keys())
        layout.addWidget(self.combo_box)

        self.button = QPushButton("Открыть сервис подписей")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Устанавливаем бесконечную анимацию
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def on_button_click(self):
        name = self.combo_box.currentText()
        data = self.lpu_data[name]

        connection = SshConnection(data)

        # Отображаем индикатор загрузки
        self.progress_bar.setVisible(True)
        self.button.setEnabled(False)  # Отключаем кнопку во время подключения

        # Создаём поток для подключения
        self.connection_thread = ConnectionThread(connection)
        self.connection_thread.connection_result.connect(self.on_connection_finished)
        self.connection_thread.start()

    def on_connection_finished(self, connection_error):
        """Обрабатывает завершение подключения."""


        if connection_error:
            QMessageBox.information(self, "Ошибка", f"{connection_error}")
        else:
            from LPUSignesWindow import MainWindow
            main_window = MainWindow(self.connection_thread.connection)
            main_window.show()

            # Скрываем индикатор загрузки
            self.progress_bar.setVisible(False)

            self.close()

    def set_style(self, stylesheet_file="themes/dark.qss"):
        try:
            parameters = load_global_parameters()
            if "STYLESHEET_FILE" in parameters:
                stylesheet_file = "themes/" + parameters["STYLESHEET_FILE"]["value"]
            with open(stylesheet_file, "r") as file:
                stylesheet = file.read()
                self.setStyleSheet(stylesheet)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка при смене стиля", str(e).strip())

    def filter_items(self, text):
        """Фильтрует элементы в выпадающем списке по тексту"""
        data = self.lpu_data.keys()
        self.combo_box.clear()  # Очищаем список
        filtered_items = [item for item in data if text.lower() in item.lower()]
        self.combo_box.addItems(filtered_items)  # Добавляем отфильтрованные элементы
        self.combo_box.setEditText(text)  # Сохраняем ввод пользователя



if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icons/app_icon.png"))
    window = SelectLPU()
    window.show()
    sys.exit(app.exec())
