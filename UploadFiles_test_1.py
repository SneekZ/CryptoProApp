import paramiko
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QVBoxLayout, QWidget, QPushButton, QMessageBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Qt


class SSHClient:
    def __init__(self, hostname, username, password, port=22):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sftp = None
        self.connect(hostname, username, password, port)

    def connect(self, hostname, username, password, port):
        try:
            self.ssh.connect(hostname, port, username, password)
            self.sftp = self.ssh.open_sftp()
        except Exception as e:
            raise Exception(f"Не удалось подключиться: {e}")

    def list_dir(self, path):
        try:
            return self.sftp.listdir_attr(path)
        except FileNotFoundError:
            return []

    def download_file(self, remote_path, local_path):
        self.sftp.get(remote_path, local_path)

    def upload_file(self, local_path, remote_path):
        self.sftp.put(local_path, remote_path)

    def remove_file(self, path):
        self.sftp.remove(path)

    def close(self):
        if self.sftp:
            self.sftp.close()
        self.ssh.close()


class FileManagerApp(QMainWindow):
    def __init__(self, ssh_client):
        super().__init__()
        self.ssh_client = ssh_client
        self.current_path = "/"  # Текущая директория на удалённом сервере
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Удалённый файловый менеджер")
        self.resize(800, 600)

        layout = QVBoxLayout()

        # Дерево каталогов
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Имя файла", "Размер", "Тип", "Дата изменения"])
        self.tree_view.setModel(self.model)
        self.tree_view.doubleClicked.connect(self.on_item_double_clicked)

        layout.addWidget(self.tree_view)

        # Кнопки
        self.upload_button = QPushButton("Загрузить файл")
        self.upload_button.clicked.connect(self.upload_file)
        layout.addWidget(self.upload_button)

        self.download_button = QPushButton("Скачать файл")
        self.download_button.clicked.connect(self.download_file)
        layout.addWidget(self.download_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Загрузка корневого каталога
        self.load_directory(self.current_path)

    def load_directory(self, path):
        """Загрузка содержимого указанной директории."""
        try:
            items = self.ssh_client.list_dir(path)
            self.current_path = path  # Обновляем текущую директорию
            self.model.clear()
            self.model.setHorizontalHeaderLabels(["Имя файла", "Размер", "Тип", "Дата изменения"])

            # Добавление ".." для возврата на уровень выше, если не в корневом каталоге
            if path != "/":
                parent_item = QStandardItem("..")
                parent_item.setEditable(False)
                parent_item.setData("..")
                size_item = QStandardItem("")
                type_item = QStandardItem("Папка")
                date_item = QStandardItem("")
                self.model.appendRow([parent_item, size_item, type_item, date_item])

            for item in items:
                file_item = QStandardItem(item.filename)
                file_item.setEditable(False)

                size_item = QStandardItem(str(item.st_size) if not item.st_mode & 0o40000 else "")
                size_item.setEditable(False)

                type_item = QStandardItem("Папка" if item.st_mode & 0o40000 else "Файл")
                type_item.setEditable(False)

                date_item = QStandardItem(str(item.st_mtime))
                date_item.setEditable(False)

                file_item.setData(item.filename)  # Храним имя файла/папки
                self.model.appendRow([file_item, size_item, type_item, date_item])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить директорию: {e}")

    def on_item_double_clicked(self, index):
        """Обработка двойного щелчка для перехода в папку."""
        item = self.model.itemFromIndex(index)
        if item:
            selected_name = item.data()  # Имя выбранного файла/папки

            # Если выбрана "..", поднимаемся на уровень выше
            if selected_name == "..":
                self.current_path = "/".join(self.current_path.rstrip("/").split("/")[:-1]) or "/"
            else:
                # Проверяем, является ли выбранный элемент папкой
                selected_path = f"{self.current_path}/{selected_name}".replace("//", "/")
                item_type = self.model.item(index.row(), 2).text()
                if item_type == "Папка":
                    self.current_path = selected_path
                else:
                    QMessageBox.information(self, "Файл", f"Вы выбрали файл: {selected_path}")
                    return

            # Загружаем новую директорию
            self.load_directory(self.current_path)

    def upload_file(self):
        # Реализация загрузки файла на сервер
        QMessageBox.information(self, "Загрузка файла", "Функция ещё не реализована.")

    def download_file(self):
        # Реализация скачивания файла с сервера
        QMessageBox.information(self, "Скачивание файла", "Функция ещё не реализована.")


if __name__ == "__main__":
    hostname = "dp63"
    username = "root"
    password = "shedF34A"

    try:
        ssh_client = SSHClient(hostname, username, password)
        app = QApplication([])

        window = FileManagerApp(ssh_client)
        window.show()

        app.exec()
        ssh_client.close()
    except Exception as e:
        print(f"Ошибка: {e}")
