import paramiko
from modules.get_ecp_password_from_db import get_cursor
from modules.lpu_service import *
import base64
import zlib
from modules.extract_between import extract_between
from modules.load_global_parameters import load_global_parameters

class SshConnection:
    def __init__(self, data):
        self.parameters = load_global_parameters()
        self.name = data['name']
        self.host = data['host']
        self.port = data['port']
        self.user = data['user']
        self.password = data['password']

        self.data = data

        self.signes = []
        self.signes_amount = 0

        self.doubles = []
        self.doubles_amount = 0

    def update_parameters(self):
        self.parameters = load_global_parameters()

    def connect(self):
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(self.host, self.port, self.user, self.password)

            self.cursor = get_cursor(self.data)
        except Exception as e:
            return e

    def get_sign(self, find_text=''):
        stdin, stdout, stderr = self.ssh_client.exec_command(f"/opt/cprocsp/bin/amd64/certmgr -list -dn='{find_text}'")

        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            error = stderr.read().decode('utf-8')
            return f"Ошибка {exit_status}: {error}"

        out = stdout.read().decode('utf-8')
        return parse_all(out)

    def get_several_signes(self, find_text=''):
        signes = []
        find_text = find_text.split(',')
        if find_text:
            for text in find_text:
                text = text.strip()
                answer = self.get_sign(text)
                if isinstance(answer, tuple):
                    for sign in answer[:-1][0]:
                        signes.append(sign)
        if signes:
            self.signes = signes
            self.signes_amount = len(self.signes)
        else:
            self.signes = []
            self.signes_amount = 0

    def find_doubles(self, signes=[]):
        if not signes:
            signes = self.signes
        if isinstance(signes, str):
            return signes
        snils_list, doubles_list = [], []
        for sign in signes:
            snils = sign["Subject"]["SNILS"]
            if snils in snils_list:
                doubles_list.append(snils)
            else:
                snils_list.append(snils)
        return doubles_list

    def test_sign(self, snils):
        for password, isLast in self.get_password(snils):
            self.ssh_client.exec_command(f"touch /home/converter/228.pdf")

            command = f"/opt/cprocsp/bin/amd64/cryptcp -signf -cert -nochain -pin '{password}' -dn='{snils}' /home/converter/228.pdf"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            exit_status = stdout.channel.recv_exit_status()

            if exit_status != 0:
                error = stderr.read().decode('utf-8')
                out = stdout.read().decode('utf-8')
                if isLast:
                    return exit_status, error, out
                else:
                    continue

            out = stdout.read().decode('utf-8')
            answer = extract_between(out, "\n", "\n[ErrorCode")
            return answer

    def get_all_signes(self, text=""):
        signes = self.get_sign(text)
        if isinstance(signes, str):
            return signes
        elif isinstance(signes, tuple):
            self.signes = signes[0]
            self.signes_amount = len(self.signes)

    def get_all_doubles(self):
        doubles = self.find_doubles(self.signes)
        if isinstance(doubles, str):
            self.doubles = doubles
            self.doubles_amount = "Error"
        elif isinstance(doubles, list):
            self.doubles = doubles
            self.doubles_amount = len(self.doubles)

    def get_password(self, snils):
        self.update_parameters()
        query = f"select ecp_password from Person where SNILS = {snils} and ecp_password is not null order by createDatetime"
        self.cursor.execute(query)
        encrypted_passwords = [pwd[0] for pwd in self.cursor.fetchall()]

        for i in range(len(encrypted_passwords)):
            encrypted_password = encrypted_passwords[i]

            decoded_data = zlib.decompress(base64.b64decode(encrypted_password[4:]))
            decoded_text = decoded_data.decode('utf-8')
            result = decoded_text.split('\n', 1)[-1]
            if i == len(encrypted_passwords) - 1:
                yield result, False
                yield self.parameters["DEFAULT_PASSWORD"], True
                break

            yield result, False


if __name__ == "__main__":
    data = get_connection_data_from_json([data for data in get_files_list()][1])
    lpu = SshConnection(data)
    lpu.connect()
    lpu.get_all_signes()
    data = lpu.signes
    lpu.get_several_signes('')
    print(lpu.test_sign('15017601217'))
