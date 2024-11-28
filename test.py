from modules.lpu_service import *

for filename in get_files_list():
    data = get_connection_data_from_json(filename)
print('.'.join(['a', 'b', 'c']))