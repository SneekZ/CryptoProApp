import mariadb
from modules.decrypt_password import decrypt_password
from modules.load_global_parameters import load_global_parameters


def get_connection(data):
    if ("dbhost" in data or "host" in data) and ("dbport" in data) and ("dbuser" in data) and ("dbpassword" in data) and ("database" in data):
        if "host" in data:
            host = data["host"]
        elif "dbhost" in data:
            host = data["dbhost"]
        else:
            msg = "Нет поля dbhost или host"
            return msg, True
        port = data["dbport"]
        user = data["dbuser"]
        password = data["dbpassword"]
        database = data["database"]

        try:
            connection = mariadb.connect(host=host, port=port, user=user, password=password, database=database)
        except Exception as e:
            return str(e), True
        return connection, False
    else:
        msg = "Нет необходимых полей в файле ЛПУ"
        return msg, True


def get_passwords_by_snils(connection_data, snils):
    connection, is_error = get_connection(connection_data)
    if is_error:
        return connection, is_error

    cursor = connection.cursor()

    query = f"select ecp_password from Person where SNILS = {snils} and ecp_password is not null order by createDatetime"
    query_global = "select value from GlobalPreferences where code = 1050"

    cursor.execute(query)
    data = cursor.fetchall()
    global_parameters = load_global_parameters()
    passwords = []
    if data:
        for password in data:
            if password:
                decrypted_password = decrypt_password(password[0])
                if not str(decrypted_password) in passwords:
                    passwords.append(str(decrypted_password))
    cursor.execute(query_global)
    global_password = cursor.fetchone()
    if global_password:
        try:
            passwords.append(global_password[0])
        except Exception:
            pass
    if "DEFAULT_PASSWORD" in global_parameters:
        passwords.append(global_parameters["DEFAULT_PASSWORD"]["value"])

    if passwords:
        return passwords, False
    else:
        return "Не найден ни один пароль", True


if __name__ == "__main__":
    data = {"host": "dp68vm", "dbport": 3306, "dbuser": "dbuser", "dbpassword": "dbpassword", "database": "s11"}
    connection, is_error = get_connection(data)
    if is_error:
        print(connection)
    print(get_passwords_by_snils(connection, "17394991427"))
    connection.close()