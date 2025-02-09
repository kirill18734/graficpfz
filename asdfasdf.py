# подключаем SQLite
import sqlite3 as sl

# Устанавливаем соединение с базой данных
con = sl.connect('DB/data_grafic.db')
cursor = con.cursor()

# Обновление значения в таблице March
cursor.execute("UPDATE March SET day_18 = 0 WHERE name = 'Кирилл';")

# Сохраняем изменения
con.commit()