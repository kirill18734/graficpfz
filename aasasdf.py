import os
import json

# Путь к папке с HTML-файлами
folder_path = r"C:\Users\kiraf\PycharmProjects\graficpvz\browser"

# Получаем список всех HTML-файлов
files = sorted([f for f in os.listdir(folder_path) if f.endswith(".html")])

# Записываем в JSON
json_path = os.path.join(folder_path, "files.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(files, f)

print(f"Файл {json_path} создан!")
