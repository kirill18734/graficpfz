# подключаем SQLite
import calendar
import sqlite3 as sl
import threading
from datetime import datetime

from config.auto_search_dir import path_to_project_folder, path_db

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

def generate_weekdays_html(count_days):
    html_output = ''
    for i in range(1, count_days + 1):
        html_output += f'<th class="days">{i}</th>'
    return html_output

def first_weekday(month_index):
    today = datetime.today().date()
    current_month = today.month - 1  # Приводим к индексу с 0
    previous_month = current_month - 1  # Определяем предыдущий месяц

    # Проверяем, если месяц после предыдущего в текущем году
    if month_index >= previous_month:
        year = today.year
    else:
        year = today.year + 1

    # Создаем дату для первого дня месяца
    first_day = datetime(year, month_index + 1, 1)

    # Получаем индекс дня недели (0 - понедельник, 6 - воскресенье)
    return first_day.weekday()

def get_weekdays(index_weekday, count_days):

    html_output = ''
    for i in range(count_days):
        dayIndex = (index_weekday + i) % len(weekdays)  # Определяем индекс дня недели
        html_output += f'<th class="weekdays">{weekdays[dayIndex]}</th>'
    return html_output

def clear_months():
    # Получаем текущий месяц (индекс)
    now = datetime.now().month - 1

    # Индексы предыдущего и следующего месяцев
    previous_month = (now - 1) % 12
    next_month = (now + 1) % 12

    # Получаем индексы всех месяцев, кроме текущего, предыдущего и следующего
    excluded_months = {now, previous_month, next_month}
    all_months_indices = [list_months_eng[i] for i in range(12) if i not in excluded_months]
    for month in all_months_indices:
        con = sl.connect(path_db)
        cursor = con.cursor()

        # Получение списка столбцов
        cursor.execute(f"PRAGMA table_info({month});")
        t = [row[1] for row in cursor.fetchall()[1:]]
        formatted_string = ', '.join([f'{value} = 0.0' for value in t])
        con = sl.connect(path_db)
        cursor = con.cursor()
        test_query = f'''
                UPDATE {month}
                SET {formatted_string}
                '''
        cursor.execute(test_query)  # Выполняем запрос
        con.commit()  # Фиксируем изменения
        cursor.close()  # Закрываем курсор
        con.close()  # Закрываем соединение
    return all_months_indices


def get_result_count(month):
    # формируем html страницу для нужного месяца

    # Подключение к базе данных
    con = sl.connect(path_db)
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
        SELECT '<tr><td class="data_result">' || name || '</td>' 
        ,'<td class="smens_color">',{'+ '.join(query_1)},'</td>' 
        ,'<td class="smens_color">',{'+ '.join(query_2)},'</td>'
        ,'<td class="dopsmens_color">',{'+ '.join(query_3)},'</td>'
        ,'<td class="dopsmens_color">',{'+ '.join(query_4)},'</td>'
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


def get_empoyee(month):
    # формируем html страницу для нужного месяца

    # Подключение к базе данных
    con = sl.connect(path_db)
    cursor = con.cursor()
    # Получение списка столбцов
    cursor.execute(f"PRAGMA table_info({month});")
    current_year = datetime.now().year

    # Проверяем, является ли текущий год високосным
    is_leap_year = calendar.isleap(current_year)

    query_1 = [
                  f'''
case when {row[1]} = 1.0 then  \'<td class="work ">\' ||  CAST({row[1]} AS INTEGER)  || \'</td>\' 
when {row[1]} = 0.0 then  \'<td class="weekend ">\' ||  CAST({row[1]} AS INTEGER)  || \'</td>\' 
when {row[1]} = 1.1 then  \'<td class="invent">\' ||  CAST({row[1]} AS INTEGER)  || \'</td>\' 
when {row[1]} > 1.1 then  \'<td class="dop_smens">\' ||  CAST({row[1]} AS INTEGER)  || \'</td>\' end
    ''' for row in cursor.fetchall()][1:]

    if not is_leap_year and month == 'February':
        con = sl.connect(path_db)
        cursor = con.cursor()
        # Получение списка столбцов
        cursor.execute(f"PRAGMA table_info({month});")
        query_1 = [
                      f'''
        case when {row[1]} = 1.0 then  \'<td class="work ">\' ||  CAST({row[1]} AS INTEGER)  || \'</td>\' 
        when {row[1]} = 0.0 then  \'<td class="weekend ">\' ||  CAST({row[1]} AS INTEGER)  || \'</td>\' 
        when {row[1]} = 1.1 then  \'<td class="invent">\' ||  CAST({row[1]} AS INTEGER)  || \'</td>\' 
        when {row[1]} > 1.1 then  \'<td class="dop_smens">\' ||  CAST({row[1]} AS INTEGER)  || \'</td>\' end
            ''' for row in cursor.fetchall()][1:-1]
    # Формирование запроса
    query = f'''
    SELECT '<tr><td class="employees">' || name || '</td>' || {', '.join(query_1)} || '</tr>' FROM {month};
    '''

    employee = ''
    # Выполнение запроса и вывод результатов
    with con:
        data = con.execute(query)
        for row in data:
            employee = employee + ''.join(row)

    return employee


# название основной и дополнительной таблицы, индекс первого дня недели месяца, количество дней месяца, сотрудник, дополнительная таблица
def creat_html(month, index_weekday, empoyee, result_count):
    # Открываем файл с базой данных
    con = sl.connect(path_db)
    with con:
        data = con.execute(f'''
            SELECT COUNT(*) FROM pragma_table_info('{month}');

            ''')
        for i in data:
            current_year = datetime.now().year

            # Проверяем, является ли текущий год високосным
            is_leap_year = calendar.isleap(current_year)
            count_days = str(i[0])
            if not is_leap_year and month == 'February':
                count_days = str(i[0]-1)

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
<table class="main_table">
    <tr >
        <th colspan="''' + count_days + '''" class="main_header">''' + list_months[list_months_eng.index(month)] + '''</th>
    </tr>   
    <tr>
        <th rowspan="2" class="header_employee">Сотрудник</th>
        '''+get_weekdays(index_weekday, int(count_days)-1)+'''
    </tr>
    <tr class="days">
''' + generate_weekdays_html(int(count_days)-1) + '''
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
<tr >
    <th colspan="5" class="main_header">Итоги (''' + list_months[list_months_eng.index(month)]  + ''')</th>
</tr>
<tr>
            <th rowspan="2" class="header_employee_result">Сотрудник</th>
            <th colspan="2" class="header_smens_result">Смены</th>
            <th colspan="2" class="header_dopsmens_result">Подработки/ч</th>
        </tr>
        <tr class="smens_or_dop">
            <th class="smens_color">1/2</th>
            <th class="smens_color">2/2</th>
            <th class="dop_smens_color">1/2</th>
            <th class="dop_smens_color">2/2</th>
        </tr>
        
        ''' + result_count + '''
</table>
</div>

    <div class="navigation">
    <button onclick="navigate(-1)">Назад</button>
    <span id="currentMonthText"></span>
    <button onclick="navigate(1)">Вперед</button>
</div>

<script>
    const months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ];
    
    const monthsRus = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ];

    const currentMonth = window.location.pathname.split('/').pop().replace('.html', '');
    const monthIndex = months.indexOf(currentMonth);
    
    if (monthIndex !== -1) {
        const currentMonthText = (new Date().toLocaleString('en', { month: 'long' }) === currentMonth)
            ? `Текущий месяц: ${monthsRus[monthIndex]}`
            : monthsRus[monthIndex];
        
        document.getElementById("currentMonthText").textContent = currentMonthText;

        function navigate(direction) {
            let newIndex = monthIndex + direction;
            if (newIndex < 0) newIndex = 11;  // Декабрь -> Январь
            if (newIndex > 11) newIndex = 0;  // Январь -> Декабрь
            window.location.href = months[newIndex] + ".html";
        }
    }
</script>

</body>
</html>

'''

    with open(f'{path_to_project_folder}/browser/{month}.html', 'w', encoding='UTF-8') as w:
        t = w.write(result_text)

def run_update_html():
    clear_months()
    for month in list_months_eng:
        creat_html(month, first_weekday(list_months_eng.index(month)), get_empoyee(month), get_result_count(month))