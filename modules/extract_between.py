def extract_between(text, start, end):
    # Ищем подстроки с конца
    end_index = text.rfind(end)  # Индекс конца второй подстроки
    start_index = text.rfind(start, 0, end_index)  # Индекс начала первой подстроки
    if start_index == -1 or end_index == -1:
        return None  # Если подстроки не найдены
    start_index += len(start)  # Смещаем индекс к концу найденной подстроки start
    return text[start_index:end_index]