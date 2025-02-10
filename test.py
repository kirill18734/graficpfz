import json
import os
import telebot
from telebot import types
import sqlite3 as sl
from config.auto_search_dir import data_config, path_to_img
from telebot.types import BotCommand, InlineKeyboardMarkup, \
    InlineKeyboardButton
# Создаем экземпляр бота
from edit_chart.get_img_xl import open_site
from main import data_months
import calendar
from datetime import datetime

bot = telebot.TeleBot(data_config['my_telegram_bot']['bot_token'],

                      parse_mode='HTML')
# -------------------------------------сохранение  новых пользователей --------------------------------
user_ids = set()
USER_IDS_FILE = 'user_ids.json'

list_months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май',
               'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь',
               'Декабрь']
list_months_eng = ['January', 'February', 'March', 'April', 'May',
                   'June', 'July', 'August', 'September', 'October', 'November',
                   'December']
weekdays = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']


def get_first_weekday_index(month_index):
    # Если год не указан, используем текущий год

    year = datetime.now().year

    # Проверяем, что индекс месяца в допустимом диапазоне
    if month_index < 0 or month_index > 11:
        raise ValueError("Индекс месяца должен быть от 0 до 11.")

    # Получаем индекс первого дня недели для указанного месяца
    first_weekday_index = calendar.monthrange(year, month_index + 1)[0]

    # Список названий дней недели

    return first_weekday_index


def load_user_ids():
    if os.path.exists(USER_IDS_FILE):
        with open(USER_IDS_FILE, 'r') as file:
            return set(json.load(file))
    return set()


def save_user_ids(userids):
    with open(USER_IDS_FILE, 'w') as file:
        json.dump(list(userids), file)


class Main:
    # дополнительный аргумент, для создания нового листа
    def __init__(self):
        self.selected_number = None
        self.status_dict = []
        self.select_invent = None
        self.smens = None
        self.image_message_id = None
        self.message_ids = []
        self.select_user = None
        self.select_new_invent = None
        self.select_n = None
        self.month = None
        self.select_smens = None
        self.key = None
        self.state_stack = {}  # Стек для хранения состояний
        self.selected_employees = getattr(self, 'selected_employees', set())
        self.user_id = None
        self.data_smens = None
        self.selected_month = None
        self.call = None
        self.markup = None
        self.actualy_months = None
        # если передался параметр на создание графика, то выполняем фукнцию, которая создаться график на новый месяц
        self.input_enabled = False  # Флаг для контроля ввода
        self.delete_user = None
        self.last_list = None
        self.start_main()
        self.index  = None

    # начальные кнопки, если нет, нового месяца, но используем текущий, или если он есть, то выводим 2 кнопки
    def get_months(self):

        self.last_list = [f'Прошлый месяц ({list_months[data_months()[0] - 2]})',
                          f'Текущий месяц ({list_months[data_months()[0] - 1]})',
                          f'Следующий месяц ({list_months[data_months()[0]]})']
        return self.last_list

    def start_main(self):
        commands = [
            BotCommand("start", "В начало"),
            BotCommand("back", "Назад")
        ]
        bot.set_my_commands(commands)

        @bot.message_handler(commands=['start'])
        def handle_start_main(message):
            self.user_id = message.chat.id
            user_ids.add(self.user_id)
            save_user_ids(user_ids)

            # Удаляем сообщения в диапазоне
            if message.message_id:
                for id_ in range(max(1, message.message_id - 10), message.message_id + 1):
                    try:
                        bot.delete_message(chat_id=message.chat.id, message_id=id_)
                    except Exception as error:
                        print(f"Ошибка при удалении сообщения в handle_start_main: {id_}: {error}")
                        # После завершения цикла и удаления сообщений вызываем метод выбора месяца
            self.show_month_selection()

        @bot.message_handler(commands=['back'])
        def handle_back(message):
            if message.message_id:
                try:
                    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                except Exception as error:
                    print(f"Ошибка при удалении сообщения в handle_back (1): {message.message_id}: {error}")
            # словарь где находятяться сохраненные сообщения для одной сесии
            while self.state_stack:
                last_key, last_function = self.state_stack.popitem()

                if message == 'get_image':
                    handle_start_main(message)
                    break  # Выход из цикла, если обработка завершена
                elif 'Текущий месяц' in str(last_key) or 'Следующий месяц' in str(last_key):
                    if message.message_id:
                        for id_ in range(max(1, message.message_id - 10), message.message_id + 1):
                            try:
                                bot.delete_message(chat_id=message.chat.id, message_id=id_)
                            except Exception as error:
                                print(f"Ошибка при удалении сообщения в handle_back (2) : {id_}: {error}")

                    try:
                        last_function()  # Попытка вызвать функцию
                        break  # Выход из цикла, если вызов завершился успешно
                    except Exception as error:
                        print(f"Ошибка при вызове last_function: {error}")
                        # Если возникла ошибка, продолжаем цикл, чтобы вызвать следующую функцию
                else:
                    try:
                        last_function()  # Попытка вызвать функцию
                        break  # Выход из цикла, если вызов завершился успешно
                    except Exception as error:
                        print(f"Ошибка при вызове last_function: {error}")
                        # Если возникла ошибка, продолжаем цикл, чтобы вызвать следующую функцию

        @bot.callback_query_handler(func=lambda call: True)
        def handle_query(call):
            self.call = call
            if 'Текущий месяц' in self.call.data or 'Следующий месяц' in self.call.data or 'Прошлый месяц' in self.call.data:
                if self.call.data not in self.status_dict:
                    self.state_stack[self.call.data] = self.show_month_selection

            if not self.state_stack or (
                    'Текущий месяц' not in str(list(self.state_stack.keys())[0]) and
                    'Следующий месяц' not in str(list(self.state_stack.keys())[0])):
                # Если кнопок нет, сбрасываем состояние и начинаем заново
                handle_start_main(call.message)
            else:
                if 'Текущий месяц' in self.call.data or 'Следующий месяц' in self.call.data or 'Прошлый месяц' in self.call.data:
                    self.state_stack[
                        self.call.data] = self.show_month_selection
                    # Сохраняем выбранный месяц
                    self.selected_month = self.call.data
                    self.month = str(self.selected_month).replace(
                        'Текущий месяц (', '').replace(
                        'Следующий месяц (', '').replace(
                        'Прошлый месяц (', '').replace(')', '')
                    # После выбора месяца показываем кнопки "Смены / подработки" и "Сотрудники"
                    self.show_sments_dop_sments()
                elif self.call.data in ['image']:
                    response_text = f"""Заявка на создание картинки  создана. Пожалуйста ожидайте. В течении 30 сек картинка отправиться."""
                    bot.answer_callback_query(self.call.id, response_text,
                                              show_alert=True)
                    open_site(self.month)
                    # Отправляем изображение
                    with open(path_to_img,
                              'rb') as photo:
                        bot.send_photo(self.call.message.chat.id, photo)
                elif self.call.data in ['shifts_jobs', 'employees',
                                        'get_image']:
                    self.state_stack[
                        self.call.data] = self.show_sments_dop_sments

                    if self.call.data == 'shifts_jobs':
                        # Создаем новую клавиатуру
                        self.show_shifts_jobs_selection()

                    elif self.call.data == 'employees':
                        self.add_del_employees()
                    elif self.call.data == 'get_image':
                        self.data_image()

                elif self.call.data in ['smens', 'dopsmens']:
                    self.state_stack[
                        self.call.data] = self.show_shifts_jobs_selection
                    self.smens = self.call.data
                    self.smens_users()
                elif self.call.data in ['add_employees']:
                    if self.call.data not in self.status_dict:
                        self.state_stack[self.call.data] = self.add_del_employees
                    self.add_employees()

                elif self.call.data in ['dell_employee']:
                    if self.call.data not in self.status_dict:
                        self.state_stack[self.call.data] = self.add_del_employees
                    self.dell_employee()

                elif self.call.data.startswith('select_employee_'):
                    employee_name = self.call.data.split('_', 2)[2]
                    if employee_name in self.selected_employees:
                        self.selected_employees.remove(employee_name)
                    else:
                        self.selected_employees.add(employee_name)
                    self.dell_employee()

                elif self.call.data in ['cancel_delete']:
                    self.add_del_employees()

                elif self.call.data.startswith('user_'):
                    self.select_user = str(self.call.data).replace(
                        'user_', '')
                    con = sl.connect('DB/data_grafic.db')
                    cursor = con.cursor()
                    # получаем индекс выбранного месяца
                    self.index = list_months.index(self.month)
                    # получает сотрудников из БД
                    # Предположим, что cursor.execute возвращает список кортежей
                    value_user = [user[1:] for user in
                                  cursor.execute(
                                      f'''select * from {list_months_eng[self.index]} where name = \'{self.select_user}\'''')]
                    # Преобразуем список кортежей в плоский список

                    self.status_dict = [item for sublist in value_user for item in sublist]
                    self.actualy_smens()
                # если выбран сотрудник на удаление, то вызываем функию для
                # удаления
                elif self.call.data == 'confirm_delete':
                    if self.selected_employees:
                        delete_user = DeleteUsers(self.table_data)
                        if list(self.selected_employees) and self.actualy_months:
                            delete_user.delete(list(self.selected_employees),
                                               self.actualy_months)

                            response_text = "Сотрудник(и) удален(ы)"
                            bot.answer_callback_query(call.id, response_text,
                                                      show_alert=True)
                            self.add_del_employees()
                        else:
                            response_text = "Не удалось удалить пользователя, необходимо подключиться, возникла ошибка"
                            bot.answer_callback_query(call.id, response_text,
                                                      show_alert=True)
                            self.add_del_employees()
                    else:
                        response_text = "Чтобы изменить подработку, перейдите пожалуйста в раздел 'Подработки'."
                        bot.answer_callback_query(call.id, response_text,
                                                  show_alert=True)

                    # Обработка статусов
                elif (self.smens + '_') in self.call.data:
                    day, week_day, smens, current_value = self.call.data.split('_')
                    self.key = int(day)-1
                    if self.smens == 'smens':

                        if float(current_value) == 0.0 and week_day not in ('вс', 'сб'):
                            self.status_dict[self.key] = 1.0
                            self.actualy_smens()
                        elif float(current_value) == 1.0 and week_day not in ('вс', 'сб'):
                            self.status_dict[self.key] = 0.0
                            self.actualy_smens()
                        elif week_day in ('вс', 'сб') and float(current_value) == 1.0:
                            self.select_invent = 0.0
                            self.select_n = 1.0
                            self.invent()
                        elif week_day in ('вс', 'сб') and float(current_value) == 0.0:
                            self.status_dict[self.key] = 1.0
                            self.select_invent = 1.1
                            self.select_n = 1.0
                            self.invent()
                        else:
                            response_text = """Чтобы изменить подработку, перейдите пожалуйста в раздел "Подработки"."""
                            bot.answer_callback_query(call.id, response_text,
                                                      show_alert=True)

                    elif self.smens == 'dopsmens':

                        if  float(current_value) in (1.0, 1.1):
                            response_text = "Чтобы изменить смену, перейдите пожалуйста в раздел 'Смены'."
                            bot.answer_callback_query(call.id, response_text,
                                                      show_alert=True)
                        else:
                            self.selected_number = self.status_dict[self.key]
                            self.dop_smens()
                elif call.data == "invent_selected":
                    self.select_new_invent = f'{self.select_invent}i'
                    self.select_invent = self.select_new_invent
                    self.invent()
                elif call.data == "invent_not_selected":
                    if type(self.select_invent) == str:
                        self.select_new_invent = int(
                            str(self.select_invent).replace('i',
                                                            ''))  # Убираем элемент из выбранных
                    else:
                        self.select_new_invent = f'{self.select_invent}i'
                    self.select_invent = self.select_new_invent
                    self.invent()
                    # Обновляем кнопки
                elif self.call.data.startswith("number_"):
                    selected_number = int(call.data.split("_")[1])
                    # Проверяем, выбран ли номер
                    if self.selected_number == selected_number:
                        self.selected_number = 0.0  # Снимаем выбор, если номер уже выбран
                    else:
                        self.selected_number = selected_number  # Сохраняем новый выбранный номер

                    self.dop_smens()  # Обновляем кнопки
                elif call.data == 'save_invent':
                    if self.select_invent != 1.1:

                    self.status_dict[self.key]  = self.select_n

                    self.actualy_smens()
                elif call.data == 'cancel_invent':
                    if 'i' not in str(self.key):
                        self.key = int(self.key)

                    self.status_dict = {
                        key if key != self.key else int(
                            str(self.key).replace('i', '')): value
                        for key, value in
                        self.status_dict.items()}
                    self.status_dict[
                        int(str(self.key).replace('i', ''))] = None
                    self.actualy_smens()
                elif call.data == 'cancel':
                    # Логика для отмены
                    self.actualy_smens()
                elif call.data == 'save_smens':
                    self.status_dict[self.key] = self.selected_number
                    response_text = "Подработка сохранена"
                    bot.answer_callback_query(call.id, response_text,
                                              show_alert=True
                                              )

                    self.actualy_smens()
                elif self.call.data in ['save_all_smens']:
                    if self.month and self.select_user and self.status_dict:
                        self.table.edit_smens(self.month, self.select_user,
                                              self.status_dict)

                        response_text = "Изменения сохранены."
                        bot.answer_callback_query(call.id, response_text,
                                                  show_alert=True)
                        self.smens_users()
                    else:
                        response_text = "Не удалось сохранить смены, необходимо подключиться, возникла ошибка"
                        bot.answer_callback_query(self.call.id, response_text,
                                                  show_alert=True)
                        self.smens_users()
                elif self.call.data in ['cancel_all_smens']:
                    self.smens_users()

    def show_month_selection(self):

        self.markup = InlineKeyboardMarkup()
        buttons = []

        for month in self.get_months():
            item = InlineKeyboardButton(month, callback_data=month)
            buttons.append(item)

        self.markup = InlineKeyboardMarkup([buttons])

        try:
            bot.edit_message_text(
                f"Выберите месяц:",
                chat_id=self.call.message.chat.id,
                message_id=self.call.message_id,
                reply_markup=self.markup
            )

        except Exception as error:
            bot.send_message(self.user_id, "Выберите месяц:",
                             reply_markup=self.markup)

    def show_sments_dop_sments(self):
        self.markup = InlineKeyboardMarkup()
        item1 = InlineKeyboardButton("Смены / подработки",
                                     callback_data='shifts_jobs')
        item2 = InlineKeyboardButton("Сотрудники", callback_data='employees')
        item3 = None
        if data_config['URL']:
            item3 = InlineKeyboardButton("Посмотреть график",
                                         callback_data='get_image')  # url=data_config["URL"]

        self.markup.add(item1, item2)
        if data_config['URL']:
            self.markup.add(item3)
        # Обновляем клавиатуру в том же сообщении
        bot.edit_message_text(
            f"""Вы находитесь в разделе: "<u>{self.selected_month}</u>".\n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start\n\nВыберете раздел:""",
            chat_id=self.call.message.chat.id,
            message_id=self.call.message.message_id,
            reply_markup=self.markup)

    def show_shifts_jobs_selection(self):

        self.markup = InlineKeyboardMarkup()

        item1 = InlineKeyboardButton("Смены", callback_data='smens')

        item2 = InlineKeyboardButton("Подработки", callback_data='dopsmens')

        self.markup.add(item1, item2)

        bot.edit_message_text(

            f"""Вы находитесь в разделе: "{self.selected_month}" - "<u>Смены / подработки</u>".\n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nВыберите раздел:""",

            chat_id=self.call.message.chat.id,

            message_id=self.call.message.message_id,

            reply_markup=self.markup

        )

    def actualy_smens(self):

        self.markup = types.InlineKeyboardMarkup()
        # Подключение к базе данных

        first_weekday_index = get_first_weekday_index(self.index)
        buttons = []
        count = 1
        current_weekday_index = first_weekday_index
        for value in self.status_dict:
            if value == 0.0:
                emoji = "❌"  # Выходной
            elif value == 1.0:
                emoji = "✅"  # Смена
            elif value == 1.1:
                emoji = "🟦"  # Инвентаризация
            else:
                emoji = "🟠"  # Подработка
                # Получаем день недели с учетом текущего индекса
            week_day = weekdays[current_weekday_index]

            button_text = f"{count}д ({week_day}) {emoji}"
            # item = types.InlineKeyboardButton(button_text,
            #                                   callback_data=f"{key}_{get_days[int(str(key).replace('i', ''))]}_"
            #                                                 f"{self.smens}_{value}")
            item = types.InlineKeyboardButton(button_text, callback_data=f"{count}_{week_day}_{self.smens}_{value}")
            # Увеличиваем индекс дня недели, и если он превышает 6, сбрасываем на 0
            current_weekday_index = (current_weekday_index + 1) % 7
            count += 1
            buttons.append(item)

        self.markup.add(*buttons)
        # Добавляем кнопку "Сохранить"
        save_smens = InlineKeyboardButton("💾 Сохранить!",
                                          callback_data='save_all_smens')
        cancel_smens = InlineKeyboardButton("Отмена!",
                                            callback_data='cancel_all_smens')
        self.markup.add(cancel_smens, save_smens)
        smen = 'Смены' if self.smens == 'smens' else 'Подработки'
        bot.edit_message_text(
            f"""Вы находитесь в разделе:  "{self.selected_month}" - "Смены / подработки" - "{smen}"  - "<u>{self.select_user}</u>". \n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nВыберете раздел:\n❌ - выходной\n✅ - смена\n🟠 - подработка\n🟦 - смена (инвентаризация)""",
            chat_id=self.call.message.chat.id,
            message_id=self.call.message.message_id,
            reply_markup=self.markup
        )

    def add_del_employees(self):
        self.markup = InlineKeyboardMarkup()
        item4 = InlineKeyboardButton("Добавить сотрудника",
                                     callback_data='add_employees')
        item5 = InlineKeyboardButton("Удалить сотрудника",
                                     callback_data='dell_employee')
        self.markup.add(item4, item5)
        bot.edit_message_text(
            f"""Вы находитесь в разделе: "{self.selected_month}" - "<u>Сотрудники</u>".\n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nВыберите раздел:""",
            chat_id=self.call.message.chat.id,
            message_id=self.call.message.message_id,
            reply_markup=self.markup)

    def data_image(self):
        self.markup = InlineKeyboardMarkup()
        item4 = InlineKeyboardButton("Перейти на сайт",
                                     callback_data='site_image', url=data_config["URL"], disable_web_page_preview=True)
        # item5 = InlineKeyboardButton("Показать картинку ",
        #                              callback_data='image',
        #                              )
        self.markup.add(item4)
        try:
            bot.edit_message_text(
                f"""Вы находитесь в разделе: "{self.selected_month}" - "<u>Посмотреть график</u>".\n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nВыберите раздел:""",
                chat_id=self.call.message.chat.id,
                message_id=self.call.message.message_id,
                reply_markup=self.markup)
        except Exception as error:
            bot.send_message(self.user_id,
                             f"""В""ы находитесь в разделе: "{self.selected_month}" - "<u>Посмотреть график</u>".\n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nВыберите раздел:""",
                             reply_markup=self.markup)

    def smens_users(self):
        self.markup = types.InlineKeyboardMarkup()
        buttons = []
        # Подключение к базе данных
        con = sl.connect('DB/data_grafic.db')
        cursor = con.cursor()
        index = list_months.index(self.month)
        cursor.close()
        # получает сотрудников из БД
        users = [user[0] for user in cursor.execute(f'select name from {list_months_eng[index]}')]
        # Получаем список пользователей
        # users = self.table_data.get_users(self.month)

        for user in users:
            # Используем имя пользователя в качестве callback_data
            item = types.InlineKeyboardButton(user,
                                              callback_data=f'user_{user}')
            buttons.append(item)

        self.markup.add(*buttons)
        smen = 'Смены' if self.smens == 'smens' else 'Подработки'
        bot.edit_message_text(
            f"""Вы находитесь в разделе: "{self.selected_month}" - "Смены / подработки" - "<u>{smen}</u>". \n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nВыберите сотрудника:""",
            chat_id=self.call.message.chat.id,
            message_id=self.call.message.message_id,
            reply_markup=self.markup
        )

    def add_employees(self):
        # Редактируем текущее сообщение, чтобы запросить имя сотрудника
        bot.edit_message_text(
            f"""Вы находитесь в разделе: {self.selected_month}.\n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nНапишите имя сотрудника для добавления""",
            chat_id=self.call.message.chat.id,
            message_id=self.call.message.message_id
        )

        # Устанавливаем состояние ожидания ответа от пользователя
        bot.register_next_step_handler(self.call.message,
                                       self.process_employee_name)

    def process_employee_name(self, message):
        if message.text not in ['/back',
                                '/start'] and message.text not in self.table_data.get_users(self.month):
            employee_name = message.text  # Получаем введенное имя сотрудника
            if str(employee_name) and self.actualy_months:
                # add_users = AddUser(self.table_data)

                # add_users.add(str(employee_name), self.actualy_months)
                # Здесь вы можете обработать имя сотрудника, например, сохранить его в базе данных
                response_text = f"Сотрудник {employee_name} добавлен."
                bot.answer_callback_query(self.call.id, response_text,
                                          show_alert=True)
                bot.delete_message(chat_id=message.chat.id,
                                   message_id=message.message_id)
                self.add_del_employees()
            else:
                response_text = "Не удалось добавить пользователя, необходимо подключиться, возникла ошибка"
                bot.answer_callback_query(self.call.id, response_text,
                                          show_alert=True)
                self.add_del_employees()
        else:
            if message.message_id:
                for id_ in range(max(1, message.message_id - 1), message.message_id + 1):
                    try:
                        bot.delete_message(chat_id=message.chat.id, message_id=id_)
                    except Exception as error:
                        print(f"Ошибка при удалении сообщения в process_employee_name: {id_}: {error}")

            # elif message.text in self.table_data.get_users(self.month):
            #     if self.state_stack.popitem():
            #         self.state_stack.popitem()
            #         response_text = f"Данное имя уже есть в таблице, пожалуйста, напишите другое"
            #         bot.answer_callback_query(self.call.id, response_text,
            #                                   show_alert=True)

            elif message.text == '/back':
                if self.state_stack.popitem():
                    self.state_stack.popitem()
                    self.add_del_employees()

    def dell_employee(self):
        employees = self.table_data.get_users(
            self.month)  # Получаем список сотрудников за последний месяц

        new_markup = InlineKeyboardMarkup()
        try:
            # Добавляем кнопки для сотрудников по 2 в строке
            for i in range(0, len(employees), 2):
                # Берем два сотрудника за раз
                row_buttons = []
                for j in range(2):
                    if i + j < len(
                            employees):  # Проверяем, чтобы не выйти за пределы списка
                        employee = employees[i + j]
                        is_selected = employee in self.selected_employees
                        button_text = f"{employee} {'❌' if is_selected else '✅'}"
                        item = InlineKeyboardButton(button_text,
                                                    callback_data=f'select_employee_{employee}')
                        row_buttons.append(item)

                # Добавляем кнопки в строку
                new_markup.row(*row_buttons)
        except Exception as error:
            print(f'Ошибка при удалении сообщения в dell_employee:{error}')

        # Добавляем кнопку "Удалить"
        delete_button = InlineKeyboardButton("🗑️ Удалить!",
                                             callback_data='confirm_delete')
        cancel_delete = InlineKeyboardButton("Отмена!",
                                             callback_data='cancel_delete')
        new_markup.add(cancel_delete, delete_button)

        bot.edit_message_text(
            f"""Вы находитесь в разделе: "{self.selected_month}" - "Сотрудники" - "<u>Удалить сотрудника</u>". \n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nВыберите сотрудников для удаления:""",
            chat_id=self.call.message.chat.id,
            message_id=self.call.message.message_id,
            reply_markup=new_markup
        )

    def invent(self):
        self.markup = types.InlineKeyboardMarkup()

        # Проверяем, выбран ли номер, и устанавливаем соответствующий текст кнопки
        if self.select_invent == 0.0:
            button_text = "✅"  # Зеленая галочка для выбранного номера
            callback_data = "invent_not_selected"  # Изменяем состояние
        else:
            button_text = "❌"  # Красный крестик для невыбранного номера
            callback_data = "invent_selected"  # Изменяем состояние

        item = types.InlineKeyboardButton(button_text,
                                          callback_data=callback_data)
        self.markup.add(item)

        # Добавляем кнопки "Отмена" и "Сохранить"
        cancel_button = types.InlineKeyboardButton("Убрать смену",
                                                   callback_data='cancel_invent')
        save_button = types.InlineKeyboardButton("💾 Сохранить!",
                                                 callback_data='save_invent')
        self.markup.add(cancel_button, save_button)
        smen = 'Смены' if self.smens == 'smens' else 'Подработки'
        # Обновляем клавиатуру в том же сообщении
        bot.edit_message_text(
            f"""Вы находитесь в разделе: "{self.selected_month}" - "Смены / подработки" - "<u>{smen}</u>".\n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start\n\nБудет ли инвентаризация?\n✅ - Да\n❌ - Нет""",
            chat_id=self.call.message.chat.id,
            message_id=self.call.message.message_id,
            reply_markup=self.markup
        )

    def dop_smens(self):
        self.markup = types.InlineKeyboardMarkup()
        # Создаем кнопки от 1 до 12
        for i in range(2, 13):
            # Проверяем, выбран ли номер, и устанавливаем соответствующий текст кнопки
            if int(self.selected_number) == i:
                button_text = f"{i}ч ✅"  # Зеленая галочка для выбранного номера
            else:
                button_text = f"{i}ч ❌"  # Красный крестик для невыбранного номера
            item = types.InlineKeyboardButton(button_text,
                                              callback_data=f"number_{i}")
            self.markup.add(item)

        # Добавляем кнопки "Отмена" и "Сохранить"
        cancel_button = types.InlineKeyboardButton("Отмена",
                                                   callback_data='cancel')
        save_button = types.InlineKeyboardButton("💾 Сохранить!",
                                                 callback_data='save_smens')
        self.markup.add(cancel_button, save_button)
        smen = 'Смены' if self.smens == 'smens' else 'Подработки'
        # Отправляем сообщение с кнопками
        bot.edit_message_text(
            f"""Вы находитесь в разделе: "{self.selected_month}" - "Смены / подработки" - "<u>{smen}</u>". \n\nИспользуй кнопки для навигации. Чтобы вернуться на шаг назад, используй команду /back. В начало /start \n\nВыберете подработку:\n❌ - не выбранные часы\n✅ - выбранные часы""",
            chat_id=self.call.message.chat.id,
            message_id=self.call.message.message_id,
            reply_markup=self.markup
        )


# запуск бота
while True:
    try:
        Main()
        bot.infinity_polling(timeout=90, long_polling_timeout=5)
    except Exception as e:
        continue
