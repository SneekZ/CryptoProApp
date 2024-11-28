import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QLineEdit,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QWhatsThis
)
from PyQt6.QtCore import QSize
from PyQt6.QtGui import QIcon
from functools import partial
from typing import cast

from ssh_connection_service import SshConnection

from modules.lpu_service import *
from modules.is_old_double import *
from modules.load_global_parameters import load_global_parameters


class MainWindow(QMainWindow):
    def __init__(self, connection):
        super().__init__()

        self.lpu = cast(SshConnection, connection)

        # Настройка главного окна
        self.setWindowTitle(self.lpu.get_name())
        self.setGeometry(100, 100, 800, 600)

        self.setMinimumSize(QSize(1400, 800))

        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Основной вертикальный макет
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Строка с Text Input и кнопкой
        text_input_layout = QHBoxLayout()
        text_input_label = QLabel("Фильтр:")
        self.text_input = QLineEdit()
        self.update_lpu_button = QPushButton("Обновить список подписей")
        # self.update_lpu_button.setToolTip("Загрузить список подписей с сервера")
        self.text_input.textChanged.connect(self.update_table)
        self.update_lpu_button.clicked.connect(partial(self.update_lpu))
        text_input_layout.addWidget(text_input_label)
        text_input_layout.addWidget(self.text_input)
        text_input_layout.addWidget(self.update_lpu_button)
        main_layout.addLayout(text_input_layout)

        # Три текстовых метки под Text Input
        text_row_layout = QHBoxLayout()
        signs_text = QLabel("Подписи:")
        self.signs_amount_text = QLabel(f"Подписи: {self.lpu.get_signs_amount()}")
        self.doubles_amount_text = QLabel(f"Дубли: {self.lpu.get_doubles_amount()}")
        doubles_show_button = QPushButton("Показать дубли")
        doubles_show_button.setToolTip("Показать подписи с одинаковым СНИЛС")
        doubles_show_button.clicked.connect(partial(self.see_doubles))
        mo_show_button = QPushButton("Показать МО")
        mo_show_button.setToolTip("Показать подпись МО\n(Поиск просходит по:\n1) SHA1 Hash в config.py\n2) СНИЛС в config.py\n3) 'главный врач' в Subject -> T)")
        mo_show_button.clicked.connect(partial(self.see_mo))
        text_row_layout.addWidget(signs_text)
        text_row_layout.addWidget(self.signs_amount_text)
        text_row_layout.addWidget(self.doubles_amount_text)
        text_row_layout.addWidget(doubles_show_button)
        text_row_layout.addWidget(mo_show_button)
        main_layout.addLayout(text_row_layout)

        self.table = QTableWidget(self.lpu.get_signs_amount(), 4)

        main_layout.addWidget(self.table)

        button_settings = QPushButton("Настройки")
        button_settings.setToolTip("Изменить глобальные константы")
        button_settings.clicked.connect(self.settings)
        main_layout.addWidget(button_settings)

        button_back = QPushButton("Вернуться к выбору")
        button_back.setToolTip("Вернуться к окну выбора ЛПУ")
        button_back.clicked.connect(partial(self.back))
        main_layout.addWidget(button_back)

        self.table.setHorizontalHeaderLabels(["ФИ", "СНИЛС", "Срок действия", "Действия"])

        self.update_lpu()
        self.update_table()

        stylesheet_file = "themes/" + self.lpu.parameters["STYLESHEET_FILE"]["value"]
        self.set_style(filename=stylesheet_file)

        self.doubles = False
        self.mo = False

    def update_lpu(self):
        is_error = self.lpu.update()
        if is_error:
            error_text = self.lpu.get_signs()
            QMessageBox.warning(self, "Ошибка", error_text)
        else:
            self.signs_amount_text.setText(f"Подписи: {self.lpu.get_signs_amount()}")
            self.doubles_amount_text.setText(f"Дубли: {self.lpu.get_doubles_amount()}")

    def check_sign(self, sign):
        answer, is_error = self.lpu.test_sign(sign)
        answer = answer.decode("utf-8", errors="replace") if isinstance(answer, bytes) else answer

        if is_error:
            QMessageBox.warning(self, "Ошибка", answer)
        else:
            if not answer:
                answer = "без пароля"
            QMessageBox.information(self, "Проверка подписи", f"Успешно подписано\nПароль: {answer}")

    def delete_sign(self, sign):
        self.lpu.update_parameters()

        ask = self.lpu.parameters["ASK_BEFORE_DELETE"]["value"]

        if ask:
            reply = QMessageBox.question(
                self,
                'Удаление подписи',
                'Вы уверены, что хотите удалить подпись?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            # Обработка ответа пользователя
            if reply == QMessageBox.StandardButton.Yes:
                msg, is_error = self.lpu.delete_sign(sign)
                QMessageBox.information(self, "Удаление подписи", msg)
            else:
                pass
        else:
            msg, is_error = self.lpu.delete_sign(sign)
            QMessageBox.information(self, "Удаление подписи", msg)

    def see_doubles(self):
        self.update_table(doubles=not self.doubles, mo=False)

    def see_mo(self):
        self.update_table(doubles=False, mo=not self.mo)

    def update_table(self, text="", doubles=False, mo=False):
        self.table.blockSignals(True)  # Блокируем сигналы таблицы для ускорения
        self.table.setUpdatesEnabled(False)  # Отключаем обновления интерфейса

        # Очистка таблицы
        self.table.clearContents()
        self.table.setRowCount(0)

        if mo:
            signs = self.lpu.get_mo()
            self.mo = True
            self.doubles = False
        elif doubles:
            signs = self.lpu.get_doubles()
            self.mo = False
            self.doubles = True
        else:
            signs = self.lpu.get_signs_by_string(text)
            self.mo = False
            self.doubles = False

        signs_amount = len(signs)
        if signs:
            self.table.setRowCount(signs_amount)

            for i in range(signs_amount):
                sign = signs[i]
                snils = SshConnection.get_snils_from_sign(sign)
                if not snils:
                    # snils = "Нет снилса("
                    continue

                name = self.format_sign_name(sign, doubles)
                self.table.setItem(i, 0, QTableWidgetItem(name))
                self.table.setItem(i, 1, QTableWidgetItem(snils))
                is_active = self.lpu.is_sign_expired(sign)
                if is_active:
                    active_text = "Активна"
                else:
                    active_text = "Истекла"
                self.table.setItem(i, 2, QTableWidgetItem(active_text))

                # Создание виджетов для кнопок
                cell_widget = self.create_action_buttons(sign)
                self.table.setCellWidget(i, 3, cell_widget)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.set_table_row_height(50)

        self.table.setUpdatesEnabled(True)  # Включаем обновления интерфейса
        self.table.blockSignals(False)  # Включаем сигналы таблицы

    def settings(self):
        from SettingsWindow import SettingsWindow
        self.settings_window = SettingsWindow(self.lpu)
        self.settings_window.show()

    def back(self):
        from SelectLPUWindow import SelectLPU
        self.back_window = SelectLPU()
        self.back_window.show()
        self.close()

    def set_style(self, filename="themes/dark.qss"):
        try:
            parameters = load_global_parameters()
            if "STYLESHEET_FILE" in parameters:
                filename = "themes/" + parameters["STYLESHEET_FILE"]["value"]
            with open(filename, "r") as file:
                stylesheet = file.read()
                self.setStyleSheet(stylesheet)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка при смене стиля", str(e).strip())

    def format_sign_name(self, sign, doubles):
        if doubles:
            if is_old_double(self.lpu.get_doubles(), sign):
                text = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (старый)'
            else:
                text = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (новый)'
        else:
            if sign in self.lpu.get_doubles():
                text = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (дубль)'
            else:
                text = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]}'
        if sign in self.lpu.get_mo():
            text += " (МО)"
        return text

    def create_action_buttons(self, sign):
        sign_check_button = QPushButton(f"Проверить подпись")
        sign_check_button.setToolTip("Попробовать подписать пустой документ локально")
        sign_check_button.clicked.connect(partial(self.check_sign, sign))

        sign_delete_button = QPushButton(f"Удалить подпись")
        sign_delete_button.setToolTip("Удалить подпись с сервера\n(Удаление происходит по thumbprint)")
        sign_delete_button.clicked.connect(partial(self.delete_sign, sign))

        # Создаём контейнер для кнопок
        cell_widget = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(sign_check_button)
        row_layout.addWidget(sign_delete_button)
        cell_widget.setLayout(row_layout)

        return cell_widget

    def set_table_row_height(self, height):
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, height)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    data = [get_connection_data_from_json(file) for file in get_files_list()][1]
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
