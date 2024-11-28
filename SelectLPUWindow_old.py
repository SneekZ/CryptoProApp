import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QMessageBox, QProgressBar
from PyQt6.QtCore import QThread, pyqtSignal

from modules.lpu_service import get_files_list, get_connection_data_from_json
from functools import partial

from ssh_connection_service import SshConnection
from modules.load_global_parameters import load_global_parameters


class SelectLPU(QMainWindow):
    def __init__(self):
        super().__init__()

        self.parameters = load_global_parameters()
        stylesheet_file = self.parameters["STYLESHEET_FILE"]["value"]
        self.set_style(filename=stylesheet_file)

        self.setWindowTitle("Выбор ЛПУ")
        self.setGeometry(100, 100, 300, 200)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        self.combo_box = QComboBox()

        self.lpu_data = {}
        for lpu in get_files_list():
            data, is_error = get_connection_data_from_json(lpu)
            if not is_error:
                self.lpu_data[data["name"]] = data

        self.combo_box.addItems(self.lpu_data.keys())
        layout.addWidget(self.combo_box)

        button = QPushButton("Открыть сервис подписей")
        button.clicked.connect(partial(self.on_button_click))
        layout.addWidget(button)

    def on_button_click(self):
        name = self.combo_box.currentText()
        data = self.lpu_data[name]

        connection = SshConnection(data)
        connection_error = connection.connect()
        if connection_error:
            QMessageBox.information(self, "Ошибка", f"{connection_error}")
        else:
            from LPUSignesWindow import MainWindow
            main_window = MainWindow(connection)
            main_window.show()
            self.close()

    def set_style(self, filename="themes/dark.qss"):
        try:
            with open(filename, "r") as file:
                stylesheet = file.read()
                self.setStyleSheet(stylesheet)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка при смене стиля", str(e).strip())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SelectLPU()
    window.show()
    sys.exit(app.exec())
