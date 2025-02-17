
# time_str = "06:57" || "16'" || "19+35'"
def time_to_seconds(time_str):
    # Подумать над проверкой, может быть что то не так
    if time_str is None:
        return 0

    # Проверка для случая "19+35'"
    if "+" in time_str and "'" in time_str:
        time_str = time_str.replace("+", ":").replace("'", "")

    # Проверяем, содержит ли строка только минуты (например, "16'", "1", "2")
    if "'" in time_str or len(time_str) <= 2:
        minutes = int(time_str.replace("'", ""))
        seconds = 0
    else:
        minutes, seconds = map(int, time_str.split(':'))

    total_seconds = minutes * 60 + seconds
    return total_seconds
