def format_days(values):
    formatted_string = ', '.join([f'day_{i + 1} = {value}' for i, value in enumerate(values)])
    return formatted_string

# Пример использования
values = [0.0] * 30  # Ваш список значений (может быть любой длины)
formatted_result = format_days(values)

print(formatted_result)