# подключаем SQLite
import sqlite3 as sl
from datetime import datetime
import calendar

weekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']
list_months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май',
               'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь',
               'Декабрь']
list_months_eng = ['January', 'February', 'March', 'April', 'May',
                   'June', 'July', 'August', 'September', 'October', 'November',
                   'December']


def data_months():
    now = datetime.now()
    next_year, next_month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)

    return [next_month - 1, calendar.monthrange(next_year, next_month)[0]]


def get_result_count(month):
    #
    # формируем html страницу для нужного месяца

    # Подключение к базе данных
    con = sl.connect('DB/data_grafic.db')
    cursor = con.cursor()

    # Получение списка столбцов
    cursor.execute(f"PRAGMA table_info({month});")
    count = 1
    query_1 = []
    query_2 = []
    query_3 = []
    query_4 = []
    for row in cursor.fetchall()[1:]:
        if count < 16:
            # считаем количество смен
            query_1.append(f'''case 
when  CAST({row[1]} AS INTEGER) <= 1 then CAST({row[1]} AS INTEGER)
else 0 
end
''')
        query_3.append(f'''case 
        when  CAST({row[1]} AS INTEGER) > 1 then CAST({row[1]} AS INTEGER)
        else 0 
        end
        ''')
        # Добавляем второй элемент строки в список
        if count > 15:
            query_2.append(f'''
case 
when  CAST({row[1]} AS INTEGER) <= 1 then CAST({row[1]} AS INTEGER)
else 0 
end
''')
            query_4.append(f'''case 
                    when  CAST({row[1]} AS INTEGER) > 1 then CAST({row[1]} AS INTEGER)
                    else 0 
                    end
                    ''')
        count += 1
    # # Формирование запроса
    query = f'''
        SELECT '<tr class="data_result"><td>' || name || '</td>' 
        ,'<td>',{'+ '.join(query_1)},'</td>' 
        ,'<td>',{'+ '.join(query_2)},'</td>'
        ,'<td>',{'+ '.join(query_3)},'</td>'
        ,'<td>',{'+ '.join(query_4)},'</td>'
        ,'</tr>' FROM {month};
        '''

    # query = f'''select '<tr class="data_result"><td>' || name || '</td>' from {month}'''
    employee = ''
    # # Выполнение запроса и вывод результатов

    with con:
        data = con.execute(query)
        for row in data:
            res = tuple(str(r) for r in row)
            employee = employee + ''.join(res)
    return employee


# get_result_count('February')


# получаем количество дней в нужном месяце
def get_count_days(month):
    # Открываем файл с базой данных
    con = sl.connect('DB/data_grafic.db')
    with con:
        data = con.execute(f'''
        SELECT COUNT(*) FROM pragma_table_info('{month}');

        ''')
        for i in data:
            return (i[0] - 1)


def get_empoyee(month):
    #
    # формируем html страницу для нужного месяца

    # Подключение к базе данных
    con = sl.connect('DB/data_grafic.db')
    cursor = con.cursor()
    cursor.execute(f'select count(*) from {month}')
    t = [row[0] for row in cursor.fetchall()]
    # если в новом месяце нет, сотрудников, то копируем из предыдущего
    if t[0] == 0 :
        cursor.execute(f'''
        INSERT INTO {month} (name)
SELECT name FROM {list_months_eng[data_months()[0]-1]};
''')
    # Получение списка столбцов
    cursor.execute(f"PRAGMA table_info({month});")
    query_1 = [f'''
    case when {row[1]} = 1.0 then  \'<td class="work ">\' ||  {row[1]}  || \'</td>\' 
     when {row[1]} = 0.0 then  \'<td class="weekend ">\' ||  {row[1]}  || \'</td>\' 
     when {row[1]} = 1.1 then  \'<td class="invent">\' ||  {row[1]}  || \'</td>\' 
     when {row[1]} > 1.1 then  \'<td class="dop_smens">\' ||  {row[1]}  || \'</td>\' end

    '''
               for row in cursor.fetchall()][1:]

    # Формирование запроса
    query = f'''
    SELECT '<tr><td class="header">' || name || '</td>' || {', '.join(query_1)} || '</tr>' FROM {month};
    '''

    employee = ''
    # Выполнение запроса и вывод результатов
    with con:
        data = con.execute(query)
        for row in data:
            employee = employee + ''.join(row)

    return employee


def creat_html(month, index_weekday, count_days, empoyee, result_count):
    result_text = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="style.css">
    <title>График смен</title>
</head>
<body>
<table>
    <tr class="header_winter">
        <th colspan="'''+str(count_days+1)+'''">''' + month + '''</th>
    </tr>   
    <tr class="header">
        <th rowspan="2">Сотрудник</th>
        <script>
const days = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'];
const index_weekday = ''' + index_weekday + '''/* здесь должен быть ваш индекс */;

for (let i = 0; i < 4; i++) { // 4 недели
    for (let j = 0; j < 7; j++) {
        const dayIndex = (index_weekday + j) % 7; // вычисляем индекс дня
        document.write('<th>' + days[dayIndex] + '</th>');
    }
}
</script>
    </tr>
    <tr class="header">
        <script>
        for (let i = 1; i < ''' + str(count_days+1) + '''; i++) {
            document.write('<th>' + i + '</th>');
        }
        </script>
    </tr>
''' + empoyee + '''
</table>
<div class="table-container">
    <table class="table_info">
        <tr class="summarywork">  <th>Работа//смена</th>  </tr>
        <tr class="summaryweekend"><th>Выходной</th></tr>
        <tr class="summaryinvent"> <th>Инвентаризация</th></tr>
        <tr class="summarydop"><th>Подработка/ч</th> </tr>
    </table>
<table class="result_table">
<tr class="header_winter">
    <th colspan="5">Итоги (''' + month + ''')</th>
</tr>
<tr>
            <th rowspan="2">Сотрудник</th>
            <th colspan="2">Смены</th>
            <th colspan="2">Подработки/ч</th>
        </tr>
        <tr class="smens_or_dop">
            <th >1/2</th>
            <th>2/2</th>
            <th>1/2</th>
            <th >2/2</th>
        </tr>
        
        ''' + result_count + '''
</table>
</div>
</body>
</html>

'''

    with open(f'browser/{list_months_eng[data_months()[0]]}.html', 'w', encoding='UTF-8') as w:
        t = w.write(result_text)


creat_html(list_months[data_months()[0]], weekdays[data_months()[1]], get_count_days(list_months_eng[data_months()[0]]),
get_empoyee(list_months_eng[data_months()[0]]), get_result_count(list_months_eng[data_months()[0]]))
