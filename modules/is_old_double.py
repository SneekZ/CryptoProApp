from ssh_connection_service import SshConnection


def is_old_double(signs, my_sign):
    from ssh_connection_service import SshConnection
    my_snils = SshConnection.get_snils_from_sign(my_sign)
    my_date = my_sign["Not valid before"]
    sign_dates = []
    for sign in signs:
        snils = SshConnection.get_snils_from_sign(sign)
        if snils == my_snils:
            sign_dates.append(sign["Not valid before"])
    sign_dates = list(sorted(sign_dates))
    if my_date == sign_dates[-1]:
        return True
    else:
        return False