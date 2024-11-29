import paramiko
import sys

from modules.lpu_service import *
from modules.load_global_parameters import load_global_parameters
from modules.sign_parsing import parse, parse_find_text, is_error_in_exec, parse_config_py
from modules.get_ecp_password_from_db import get_passwords_by_snils
from datetime import datetime
import time


class SshConnection:
    def __init__(self, data):
        self.parameters = load_global_parameters()

        self.name = data['name']
        self.host = data['host']
        self.port = data['port']
        self.user = data['user']
        self.password = data['password']

        self.__data = data

        self.__signs = []

        self.__doubles = []

        self.__mo = []

        self.__table = []

    def connect(self):
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(self.host, self.port, self.user, self.password, look_for_keys=False, allow_agent=False)

        except Exception as e:
            return e

    def __exec_command(self, command):
        stdin, stdout, stderr = self.ssh_client.exec_command(command)

        exit_status = stdout.channel.recv_exit_status()

        out = stdout.read().decode('utf-8', errors="ignore")
        err = stderr.read().decode('utf-8', errors="ignore")
        is_error = exit_status != 0

        return out, err, is_error

    def update_parameters(self):
        self.parameters = load_global_parameters()

    def __get_sign(self, find_text=''):
        command = f"/opt/cprocsp/bin/amd64/certmgr -list -dn='{find_text}'"
        out, err, is_error = self.__exec_command(command)

        if is_error:
            return err.strip(), is_error
        else:
            parsed_out, is_error = parse(out, err)
            return parsed_out, is_error

    def __get_doubles(self):
        signs = {}
        for sign in self.__signs:
            snils = 0
            try:
                snils = self.get_snils_from_sign(sign)
            except Exception:
                continue
            if snils in list(signs.keys()):
                signs[snils] += 1
            else:
                signs[snils] = 1
        doubles = [key for key, value in signs.items() if value > 1]
        return doubles

    def update(self):
        signs, is_error = self.__get_sign()

        self.__signs = signs

        doubles = self.__get_doubles()
        self.__doubles = doubles

        mo = self.__get_mo()
        self.__mo = mo

        return is_error

    def test_sign(self, sign):
        if not isinstance(sign, dict):
            return "Подпись должна быть одним словарем", True
        snils = self.get_snils_from_sign(sign)
        if not snils:
            return "В подписи не найден снилс", True
        passwords, is_error = get_passwords_by_snils(self.__data, snils)
        if is_error:
            return passwords, is_error

        error_msg, is_error_global = "", False

        for password in passwords:
            command_touch = f"touch /home/converter/228.pdf"
            out, err, is_error = self.__exec_command(command_touch)
            if is_error:
                return err, is_error

            command_test = f"/opt/cprocsp/bin/amd64/cryptcp -signf -cert -nochain -pin '{password}' -dn='{snils}' /home/converter/228.pdf"
            out, err, is_error = self.__exec_command(command_test)
            if is_error:
                error_msg = out
                is_error_global = is_error
            else:
                return password, is_error

            # else:
            #     is_error = is_error_in_exec(out)
            #     if is_error:
            #         error_msg = out
            #         is_error_global = is_error
            #     else:
            #         return "Подписывается успешно", is_error
        if is_error_global:
            return error_msg, is_error_global
        else:
            return "Подписывается успешно", False

    def delete_sign(self, sign, sha=None):
        if not sha:
            sha = self.get_sha_from_sign(sign)
        command = None
        if sha:
            command = f"/opt/cprocsp/bin/amd64/certmgr -delete -thumbprint {sha}"
        else:
            return "Не удалось получить SHA1", True
        if command:
            out, err, is_error = self.__exec_command(command)
            if is_error:
                return err.strip(), is_error
            if not is_error:
                is_error = is_error_in_exec(out)
                if is_error:
                    return out.strip(), is_error
                else:
                    return "Подпись была удалена успешно", False
        return "Неизвестная ошибка при удалении документа", True

    def get_signs(self):
        return self.__signs

    def get_signs_amount(self):
        return len(self.__signs)
    
    def get_doubles(self):
        doubles = self.__doubles
        signs = []
        if self.__signs:
            for snils in doubles:
                for sign in self.__signs:
                    if "SNILS" in sign["Subject"]:
                        if snils == sign["Subject"]["SNILS"]:
                            signs.append(sign)
                    elif "СНИЛС" in sign["Subject"]:
                        if snils == sign["Subject"]["СНИЛС"]:
                            signs.append(sign)
        return signs
    
    def get_doubles_amount(self):
        return len(self.__doubles)

    def get_data(self):
        return self.__data

    def get_name(self):
        return self.name

    def get_mo(self):
        return self.__mo

    def get_table(self):
        return self.__table

    def get_signs_by_string(self, find_text=''):
        if not find_text:
            return self.__signs
        parsed_find_text = parse_find_text(find_text)
        signs = []
        for sign in self.__signs:
            for text in parsed_find_text:
                snils = self.get_snils_from_sign(sign)
                if snils and text == snils:
                    signs.append(sign)
                    break
                else:
                    text = text.lower()
                    if "SN" in sign["Subject"] and "G" in sign["Subject"]:
                        if text in f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]}'.lower():
                            signs.append(sign)
                            break
                    elif "SN" in sign["Subject"]:
                        if text in sign["Subject"]["SN"].lower():
                            signs.append(sign)
                            break
                    elif "G" in sign["Subject"]:
                        if text in sign["Subject"]["SN"].lower():
                            signs.append(sign)
                            break
        return signs

    def get_sign_by_hash(self, hash: str):
        for sign in self.__signs:
            if "SHA1 Hash" in sign:
                if sign["SHA1 Hash"] == hash:
                    return sign
        return None

    def __get_mo(self):
        value, type = self.__get_mo_data()
        if type:
            if type == "hash":
                sign = self.get_sign_by_hash(value)
                if sign:
                    return [sign]
            elif type == "snils":
                signs = self.get_signs_by_string(value)
                if signs:
                    return signs
        signs = []
        for sign in self.__signs:
            if self.is_mo(sign):
                signs.append(sign)
        return signs

    def __get_mo_data(self):
        value, type, data = "", None, []

        try:
            sftp = self.ssh_client.open_sftp()
            with sftp.file("/var/www/html/iemkService/config.py", 'r') as config_file:
                config_data = config_file.read().decode("utf-8")
            sftp.close()
        except Exception:
            pass

        if data:
            value, type = parse_config_py(data)
        return value, type

    def create_table(self, doubles=False, mo=False):
        signs = self.__signs

        table = []

        if not mo and not doubles:
            for sign in signs:
                table.append(self.__create_table_record(sign, doubles))
        if doubles:
            for sign in self.get_doubles():
                table.append(self.__create_table_record(sign, doubles))
        if mo:
            signs_mo = self.__mo
            for sign in signs_mo:
                table.append(self.__create_table_record(sign, False))
        self.__table = table

    def __create_table_record(self, sign, doubles=False):
        sign_record = {}

        snils = self.get_snils_from_sign(sign)
        if not snils:
            return {}
        sign_record["snils"] = snils

        name = self.__format_sign_name(sign, doubles)
        sign_record["name"] = name

        is_active = self.is_sign_expired(sign)
        if is_active:
            active = "Активна"
        else:
            active = "Истекла"

        sign_record["active"] = active

        sign_record["sign"] = sign
        return sign_record

    def __format_sign_name(self, sign, doubles):
        if doubles:
            if self.__is_old_double(sign):
                text = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (старый)'
            else:
                text = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (новый)'

        else:
            if sign in self.get_doubles():
                text = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]} (дубль)'
            else:
                text = f'{sign["Subject"]["SN"]} {sign["Subject"]["G"]}'
        if sign in self.get_mo():
            text += " (МО)"
        return text

    def __is_old_double(self, my_sign):
        signs = self.__signs

        my_snils = self.get_snils_from_sign(my_sign)
        my_date = my_sign["Not valid before"]
        sign_dates = []
        for sign in signs:
            snils = self.get_snils_from_sign(sign)
            if snils == my_snils:
                sign_dates.append(sign["Not valid before"])
        sign_dates = list(sorted(sign_dates))
        if my_date == sign_dates[-1]:
            return True
        else:
            return False


    @staticmethod
    def get_snils_from_sign(sign):
        if "Subject" in sign:
            if "SNILS" in sign["Subject"]:
                return sign["Subject"]["SNILS"]
            elif "СНИЛС" in sign["Subject"]:
                return sign["Subject"]["СНИЛС"]
        return ""

    @staticmethod
    def get_sha_from_sign(sign):
        if "SHA1 Hash" in sign:
            return sign["SHA1 Hash"]
        else:
            return ""

    @staticmethod
    def is_mo(sign):
        if "T" in sign["Subject"]:
            return "главный врач" in sign["Subject"]["T"].lower()
        return False

    @staticmethod
    def is_sign_expired(sign):
        if "Not valid after" in sign:
            date = datetime.strptime(sign["Not valid after"], '%d/%m/%Y  %H:%M:%S %Z')
            return date > datetime.now()


if __name__ == "__main__":
    data, is_error = get_connection_data_from_json([data for data in get_files_list()][0])
    if is_error:
        print(data)
        sys.exit()
    print([data for data in get_files_list()][0])
    lpu = SshConnection(data)
    lpu.connect()
    lpu.update()

