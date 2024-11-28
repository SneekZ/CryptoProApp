def update_table(self, text="", doubles=False):
    self.table.setRowCount(0)

    if doubles:
        signs = self.lpu.get_doubles()
    else:
        signs = self.lpu.get_signs_by_string(text)
    signs_amount = len(signs)

    if signs:
        self.table.setRowCount(signs_amount)

        self.table.setVerticalHeaderLabels([f"{i + 1}" for i in range(10)])

        # Добавление элементов в таблицу
        for i in range(signs_amount):
            sign = signs[i]

            snils = SshConnection.get_snils_from_sign(sign)

            if not snils:
                continue

            if doubles:
                if is_old_double(signs, sign):
                    name = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (старый)'
                else:
                    name = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (новый)'
            else:
                if sign in self.lpu.get_doubles():
                    name = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (дубль)'
                else:
                    name = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]}'

            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(snils))

            sign_check_button = QPushButton(f"Проверить подпись")
            sign_check_button.clicked.connect(partial(self.check_sign, sign))

            sign_delete_button = QPushButton(f"Удалить подпись")
            sign_delete_button.clicked.connect(partial(self.delete_sign, sign))

            # Добавляем кнопки как виджет в столбец 2
            cell_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(sign_check_button)
            row_layout.addWidget(sign_delete_button)
            cell_widget.setLayout(row_layout)
            self.table.setCellWidget(i, 2, cell_widget)

        # Растягиваем столбцы и строки
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)