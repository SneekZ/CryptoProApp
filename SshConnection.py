import paramiko
from paramiko.ssh_exception import AuthenticationException, SSHException, NoValidConnectionsError
import logging
from datetime import datetime

from modules import get_ecp_password_from_db


class SshConnection:
    def __init__(self, data):
        logging.basicConfig(
            filename=f"log/ssh/log_{datetime.now()}",
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        self._data = data

        try:
            self._name = data["name"]
            self._host = data["host"]
            self._port = data["port"]
            self._user = data["user"]
            self._password = data["password"]
        except KeyError as e:
            msg = f"Ошибка инициализации: {e}"
            logging.error(msg)
            return msg

        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self._connected = False

    def connect(self):
        try:
            self._client.connect(
                host = self._host,
                port = self._port,
                user = self._user,
                password = self._password
            )
            self._connected = True
            logging.info(f"Подключено успешно к {self._name}")

        except AuthenticationException as auth_error:
            msg = f"Ошибка аутентификации: {auth_error}"
            logging.error(msg)
            return msg
        
        except NoValidConnectionsError as conn_error:
            msg = f"Не удается подключиться к серверу: {conn_error}"
            logging.error(msg)
            return msg
        
        except SSHException as ssh_error:
            msg = f"Ошибка SSH: {ssh_error}"
            logging.error(msg)
            return msg
        
        except Exception as e:
            msg = f"Произошла непредвиденная ошибка: {e}"
            logging.error(msg)
            return msg
        
    def _exec_command(self, command):
        if self._connected:
            stdin, stdout, stderr = self._client.exec_command(command)
            logging.info(f"Была выполнена команда {stdin.read().decode("utf-8")}")

            out = stdout.read().decode("utf-8").strip()
            err = stderr.read().decode("utf-8").strip()

            if err:
                return err, False
            
            if out:
                return out, True
            
        else:
            msg = "Клиент не был подключен"
            logging.error(msg)
            return msg, False
    
    def get_signs(self, key=""):
        command = f"/opt/cprocsp/bin/amd64/certmgr -list -dn {key}" if key else "/opt/cprocsp/bin/amd64/certmgr -list"
        out, ok = self._exec_command(command)
        return out, ok
    
    def check_sign(self, sign: dict):
        if not self._connected:
            msg = "Клиент не был подключен"
            logging.error(msg)
            return msg, False
        
        if not isinstance(sign, dict):
            msg =  "Подпись представлена в неверном формате"
            logging.error(msg)
            return msg, False
        
        if not "snils" in sign:
            msg = "В подписи нет снилса"
            logging.error(msg)
            return msg, False
        
        snils = sign["snils"]

        command = "touch /home/converter/228.pdf"
        out, ok = self._exec_command(command)
        logging.info(f"Выполнена команда {command}")
        
        if not ok:
            msg = f"Ошибка при создании 228.pdf: {out}"
            logging.error(msg)
            return msg, False
        
        passwords = get_ecp_password_from_db(self._data)

        errors = []

        for password in passwords:
            command = f'/opt/cprocsp/bin/amd64/cryptcp -signf -cert -nochain -dn="{snils}" /home/converter/228.pdf -pin {password}'
            out, ok = self._exec_command(command)
            logging.info(f"Выполнена команда {command}")

            if ok:
                return password, True
            
            errors.append(out)
        
        if errors:
            if len(errors) > 1:
                msg = errors[-2]
                logging.error(msg)
                return msg, False
            
            else:
                msg = errors[0]
                logging.error(msg)
                return msg, False
            
        else:
            msg = "Не найдено ни одного пароля"
            logging.error(msg)
            return msg, False
            


