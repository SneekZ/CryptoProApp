import base64
import zlib


def decrypt_password(encrypted_password):
    decoded_data = zlib.decompress(base64.b64decode(encrypted_password[4:]))
    decoded_text = decoded_data.decode('utf-8')
    result = decoded_text.split('\n', 1)[-1]
    return result

if __name__ == "__main__":
    print(repr(decrypt_password("#1##eNrTLEvlyswry8zLL0styixJLAYAN6cGoEVE")))