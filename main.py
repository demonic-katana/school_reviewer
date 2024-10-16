import asyncio
from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.formatting import hcite, hitalic, hbold, hlink
from random import choice
import json
from background import keep_alive


with open('db.json', 'r') as file:
    db = json.load(file)

bot = AsyncTeleBot(db['bot_token'])


def get_rating(rating):
    if len(rating) >= 1:
        return f'{sum(rating) / len(rating):.1f}'
    else:
        return "Нет оценок"


def update_rating(teacher, rating):
    teacher["rating"].append(int(rating))


def get_quote(quote):
    if len(quote) > 0:
        return choice(quote)
    else:
        return "Нет цитат"


def get_review(review):
    if len(review) > 0:
        return choice(review)
    else:
        return "Нет отзывов"


def about_teacher_short(full_name, teacher, id, id_teacher):
    kb = types.InlineKeyboardMarkup(row_width=3)
    btn1 = types.InlineKeyboardButton(text='Оценить', callback_data=f"rate_{id_teacher}") if full_name not in \
                                                                                            db["user"][str(id)][
                                                                                                "appreciated"] else None
    btn2 = types.InlineKeyboardButton(text='Отзывы', callback_data=f"review_0_{id_teacher}")
    btn3 = types.InlineKeyboardButton(text='Цитаты', callback_data=f"quote_0_{id_teacher}")
    kb.add(*[i for i in (btn1, btn2, btn3) if i])
    if str(id) in db["admin"]:
        kb.add(types.InlineKeyboardButton(text='Изменить', callback_data=f"edit_{id_teacher}"),
               types.InlineKeyboardButton(text='Удалить', callback_data=f"del_{id_teacher}"))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data=f"back_to_"))

    rating = get_rating(teacher['rating'])
    if rating != "Нет оценок":
        if float(rating) <= 4:
            emoji = "😡"
        elif float(rating) <= 7:
            emoji = "😐"
        else:
            emoji = "😎"
    else:
        emoji = '❔'

    return (f"— {full_name}\n"
            f"— {hitalic('Предмет:')} {teacher['subject']}\n"
            f"— {hitalic('Общий рейтинг:')} {rating} {emoji}\n\n"
            f"{hbold('Случайный отзыв:')}\n"
            f"{hcite(get_review(teacher['review']))}\n\n"
            f"{hbold('Случайная цитата:')}\n"
            f"{hcite(get_quote(teacher['quote']))}"), teacher['photo'], kb

def update_db():
    with open('db.json', 'w') as file:
        json.dump(db, file)

# админы: id(строка с числом): статус разработчика(bool),
#         добавление учителя: начал добавлять(bool), фио(str), предмет(str), фото(str),
#         редактировать учителя: начал редактировать(bool), фио(str), что изменить(str)
db["admin"] = {"5285632228": {"first_name":'Alexa',
                              "developer_status": True,
                              "add_teacher": {"start": False, "full_name": '',
                                              "subject": '', "photo": ''},
                              "edit_teacher": {"full_name": '', 'edit': '', 'new': ''},
                              "add_admin": False, 'del_admin': False},
               "950100889": {"first_name":'Hakuuz',
                             "developer_status": False,
                             "add_teacher": {"start": False, "full_name": '',
                                             "subject": '', "photo": ''},
                             "edit_teacher": {"full_name": '', 'edit': '', 'new': ''},
                             "add_admin": False, 'del_admin': False}}

# юзеры: id(строка с числом): пишет отзыв(bool), пишет цитату(bool), учитель(str),
#                             фио учителя(str): [оценил ли(bool)...]
db["user"] = {"5285632228": {"first_name":'Alexa', "make_review" : '', "make_quote" : '', "appreciated": [], 'support': False},
              "950100889": {"first_name":'Hakuuz', "make_review" : '', "make_quote" : '', "appreciated": [], 'support': False}}

# учителя: фио(str): {предмет(str), фото(str), рейтинг(список с оценками),
#                    цитаты(список с цитатами), отзывы(список с отзывами), id_teacher(int)}
# db["teacher"] = {}
#
# db["id_teacher"] = {}


# непроверенные цитаты: {фио учителя(str): [цитата(str)...]}
# db["quote"] = {}

# непроверенные отзывы: {фио учителя(str): [отзыв(str)...]}
# db["review"] = {}

# запросы в поддержку: {id запроса(str с числом): [запрос(str), id пользователя(str с числом)]...}
# db["support"] = {}


# Handle '/start' and '/help'
@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    if message.from_user.id not in db["user"]:
        db["user"][str(message.from_user.id)] = {"first_name": message.from_user.first_name, "make_review": "",
                                                 "make_quote": "", "appreciated": [], 'support': False}
        update_db()

    text = ('Привет! Наш бот разработан полутора энтузиастами для системы сбора мнений '
            'учеников нашей школы (или уже бывших учеников). Здесь вы можете оставить '
            'свой отзыв на учителя или добавить его цитату. Или вы можете просто '
            'просмотреть уже существующие страницы учителей по команде "/view_teacher"\n'
            'У нас есть обратная связь! По команде "/support" вы можете напрямую '
            'обратиться к нашим администраторам, а они вам обязательно ответят :)\n'
            'Наша группа тг: t.me/sc72botgroup')
    await bot.reply_to(message, text)


# Меню с командами админа
@bot.message_handler(commands=['admin_menu'])
async def admin_menu(message):
    if str(message.from_user.id) in db["admin"]:
        text = ("/add_teacher - Добавить учителя\n"
                "/add_admin - Добавить админа\n"
                "/delete_admin - Удалить админа\n"
                "/get_quote - Получить цитату для проверки\n"
                "/get_review - Получить отзыв для проверки\n"
                "/answer_support - Ответить на запросы и предложения юзеров\n"
                "/cancel - Отменить все действия\n")

    else:
        text = "Вы не являетесь админом"

    await bot.reply_to(message, text)


# Добавление учителя (только админы)
@bot.message_handler(commands=['add_teacher'])
async def add_teacher(message):
    if str(message.from_user.id) in db["admin"]:
        db["admin"][str(message.from_user.id)]["add_teacher"]["start"] = True

        update_db()

        await bot.reply_to(message, "Введите ФИО учителя в формате:\n"
                                    "Фамилия Имя Отчество")
    else:
        await bot.reply_to(message, "Вы не являетесь админом")


# Прекратить все действия
@bot.message_handler(commands=['cancel'])
async def cancel(message):
    db["user"][str(message.from_user.id)] = {"first_name": message.from_user.first_name,
                                             "make_review": "", "make_quote": "",
                                             "appreciated": db["user"][str(message.from_user.id)]["appreciated"],
                                             'support': False}
    if str(message.from_user.id) in db['admin']:
        db['admin'][str(message.from_user.id)]["add_teacher"] = {"start": False, "full_name": '', "subject": '',
                                                                 "photo": ''}
        db['admin'][str(message.from_user.id)]["edit_teacher"] = {"full_name": '', 'edit': '', 'new': ''}
        db['admin'][str(message.from_user.id)]["add_admin"] = False
        db['admin'][str(message.from_user.id)]['del_admin'] = False
    update_db()

    await bot.reply_to(message, "Все действия прекращены!")


# Проверка цитат/отзывов (только админы)
@bot.message_handler(commands=['get_quote', 'get_review'])
async def get_quote_or_review_for_adm(message):
    if str(message.from_user.id) in db["admin"]:
        comm = message.text[5:]
        kb = types.InlineKeyboardMarkup(row_width=2)
        if len(db[comm]):
            teacher = choice(list(db[comm].keys()))
            dict_q_or_r = choice(db[comm][teacher])
            text = (f'Цитата от {teacher}:\n'
                    f'{hcite(dict_q_or_r)}')
            id_teacher = db['teacher'][teacher]['id_teacher']
            q_or_r = db[comm][teacher].index(dict_q_or_r)

            kb.add(types.InlineKeyboardButton(text="Добавить", callback_data=f"add_{comm}_{id_teacher}_{q_or_r}"),
                   types.InlineKeyboardButton(text="Удалить", callback_data=f"del_{comm}_{id_teacher}_{q_or_r}"))
        else:
            text = f'Нет непроверенных {"цитат" if comm == "quote" else "отзывов"}.'
        await bot.send_message(message.from_user.id, text, parse_mode='HTML', reply_markup=kb)
    else:
        await bot.reply_to(message, "Вы не являетесь админом")


# Добавить админа (только админы)
@bot.message_handler(commands=['add_admin'])
async def add_admin(message):
    if str(message.from_user.id) in db['admin']:
        db['admin'][str(message.from_user.id)]["add_admin"] = True
        text = 'Введите id пользователя, которого хотите сделать админом:'
        for user_id in db['user']:
            if user_id not in db['admin'] and user_id != str(message.from_user.id):
                text = text + '\n' + hlink(db['user'][user_id]['first_name'], f"tg://user?id={user_id}") + f' {user_id}'
        if text == 'Введите id пользователя, которого хотите сделать админом:':
            text = text + '\n' + 'Таких нет. Действие отменено.'
            db['admin'][str(message.from_user.id)]["add_admin"] = False

        update_db()

        await bot.send_message(message.from_user.id, text, parse_mode='HTML')
    else:
        await bot.send_message(message.from_user.id,
                               'Действие не может быть выполнено, поскольку вы не являетесь админом.')


# Удалить админа (только админы)
@bot.message_handler(commands=['del_admin'])
async def del_admin(message):
    if str(message.from_user.id) in db['admin']:
        db['admin'][str(message.from_user.id)]["del_admin"] = True
        text = 'Введите id пользователя, которого хотите удалить из админов:'
        for admin_id in db['admin']:
            if admin_id != str(message.from_user.id):
                text = text + '\n' + hlink(db['user'][admin_id]['first_name'],
                                           f"tg://user?id={admin_id}") + f' {admin_id}'

        update_db()

        await bot.send_message(message.from_user.id, text, parse_mode='HTML')
    else:
        await bot.send_message(message.from_user.id, 'Действие не может быть выполнено, '
                                                     'поскольку вы не являетесь админом.')


# Написать в поддержку
@bot.message_handler(commands=['support'])
async def support(message):
    db['user'][str(message.from_user.id)]['support'] = True
    await bot.send_message(message.from_user.id, 'Введите сообщение с описание ошибки или предложением, '
                                                 'как можно улучшить бота. Наши админы ответят вам в ближайшее время.')
    update_db()


# Ответить на запрос, присланный в поддержку (только админы)
@bot.message_handler(commands=['answer_support'])
async def answer_support(message):
    if str(message.from_user.id) in db['admin']:
        if len(db['support']):
            sup = db['support'][min(db['support'])][0]
            await bot.send_message(message.from_user.id, f"support_{min(db['support'])}\n"
                                                         f"{hcite(sup)}\n\n"
                                                         "Ответьте на данное сообщение и я перешлю ваш ответ пользователю.",
                                   parse_mode="HTML")
        else:
            await bot.send_message(message.from_user.id, 'Никто не написал в поддержку.')
    else:
        await bot.send_message(message.from_user.id, 'Действие не может быть выполнено, '
                                                     'поскольку вы не являетесь админом.')


# Просмотр информации об учителе (выбор учителя из списка, запуск)
@bot.message_handler(commands=['view_teacher'])
async def view_teacher(message):
    teacher = sorted(db["teacher"].keys())
    kb = types.InlineKeyboardMarkup(row_width=3)
    for full_name in teacher[:min(len(teacher), 5)]:
        id_teacher = db["teacher"][full_name]['id_teacher']
        kb.add(types.InlineKeyboardButton(text=full_name, callback_data=f"open_{id_teacher}"))

    if len(teacher) > 5:
        kb.add(types.InlineKeyboardButton(text="1", callback_data="pass"),
               types.InlineKeyboardButton(text="▶️", callback_data="5_view"))
    await bot.send_message(message.chat.id, "Выберете учителя:", reply_markup=kb)


# Просмотр информации об учителе (выбор учителя из списка, следующая страница)
@bot.callback_query_handler(func=lambda callback: "_view" in callback.data)
async def callback_view(callback):
    callback.data = int(callback.data.split('_')[0])
    teacher = sorted(db["teacher"].keys())
    id_teacher = db["teacher"][teacher]['id_teacher']
    kb = types.InlineKeyboardMarkup(row_width=3)

    for full_name in teacher[callback.data:callback.data + min(len(teacher) - callback.data, 5)]:
        kb.add(types.InlineKeyboardButton(text=full_name, callback_data=f"open_{id_teacher}"))

    if len(teacher) > 5:
        btn0 = types.InlineKeyboardButton(text="◀️",
                                          callback_data=f"{callback.data - 5}_view") if callback.data >= 5 else None
        btn1 = types.InlineKeyboardButton(text=f"{(callback.data + 5) // 5}", callback_data="pass")
        btn2 = types.InlineKeyboardButton(text="▶️", callback_data=f"{callback.data + 5}_view") if len(
            teacher) - callback.data > 5 else None
        kb.add(*[i for i in (btn0, btn1, btn2) if i])
    await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                text="Выберете учителя:", reply_markup=kb)


# Вернуться к списку учителей
@bot.callback_query_handler(func=lambda callback: "back_to_" in callback.data)
async def callback_back_to_(callback):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    callback.chat = callback.message.chat
    await view_teacher(callback)


# Просмотр информации об учителе (просмотр конкретного учителя)
@bot.callback_query_handler(func=lambda callback: "open_" in callback.data or "back_" in callback.data)
async def callback_open(callback):
    id_teacher = callback.data[5:]
    full_name = db["id_teacher"][id_teacher]
    teacher = db["teacher"][full_name]
    text, photo, kb = about_teacher_short(full_name, teacher, callback.message.chat.id, id_teacher)

    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await bot.send_photo(callback.message.chat.id, photo, text, parse_mode='HTML', reply_markup=kb)


# Оценить учителя от 1 до 10 (вывод кнопочек)
@bot.callback_query_handler(func=lambda callback: "rate_" in callback.data)
async def callback_rate(callback):
    id_teacher = callback.data[5:]
    kb = types.InlineKeyboardMarkup(row_width=5)
    kb.add(
        *[types.InlineKeyboardButton(text=str(i), callback_data=f"rating_{i}_{id_teacher}") for i in range(1, 11)])

    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id,
                                        reply_markup=kb)


# Оценить учителя от 1 до 10 (можно только 1 раз), возвращение кнопок от предыдущей функции
@bot.callback_query_handler(func=lambda callback: "rating_" in callback.data)
async def callback_rating(callback):
    rate, id_teacher = callback.data[7:].split("_")
    full_name = db["id_teacher"][id_teacher]
    teacher = db["teacher"][full_name]
    update_rating(teacher, rate)
    db["user"][str(callback.message.chat.id)]["appreciated"].append(full_name)

    kb = types.InlineKeyboardMarkup(row_width=2)
    btn2 = types.InlineKeyboardButton(text='Отзывы', callback_data=f"review_0_{id_teacher}")
    btn3 = types.InlineKeyboardButton(text='Цитаты', callback_data=f"quote_0_{id_teacher}")
    kb.add(btn2, btn3)

    update_db()

    callback.data = f'open_{id_teacher}'
    await callback_open(callback)
    await bot.send_message(callback.message.chat.id, "Благодарим за оценку ❤️")


# Добавление цитаты/отзыва, отмена действия
@bot.callback_query_handler(func=lambda callback: "OK_" in callback.data or "off_" in callback.data)
async def callback_confirmation(callback):
    action, comm, id_teacher = callback.data.split('_')
    full_name = db["id_teacher"][id_teacher]
    db["user"][str(callback.message.chat.id)]["make_" + comm] = ''
    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    if action == "OK":
        if full_name not in db[comm]:
            db[comm][full_name] = []
        db[comm][full_name].append(callback.message.text.split('\n')[1])

        update_db()

        await bot.send_message(callback.message.chat.id,
                               f'Благодарим вас за {"отзыв" if comm == "review" else "цитату"} ❤️\n'
                               f'Мы отправим {"его" if comm == "review" else "её"} на модерацию, для проверки на цензуру.')
    else:
        await bot.send_message(callback.message.chat.id, 'Действие отменено.')
    callback.data = f'open_{id_teacher}'
    await callback_open(callback)


# Оставить отзыв / Добавить цитату
@bot.callback_query_handler(func=lambda callback: "make_" in callback.data)
async def callback_make_review_or_quote(callback):
    comm, id_teacher = callback.data.split("_")[1], callback.data.split("_")[2]
    full_name = db["id_teacher"][id_teacher]
    db["user"][str(callback.message.chat.id)]["make_review" if comm == "review" else "make_quote"] = full_name

    update_db()

    await bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id)
    await bot.send_message(callback.message.chat.id, f'Введите {"отзыв" if comm == "review" else "цитату"}:')


# Просмотр цитат/отзывов. Возможность их добавить
@bot.callback_query_handler(func=lambda callback: ("review_" in callback.data or "quote_" in callback.data) and
                                                  "del" not in callback.data and "add" not in callback.data)
async def callback_review_or_quote(callback):
    comm, num, id_teacher = callback.data.split("_")[0], int(callback.data.split("_")[1]), callback.data.split("_")[2]
    full_name = db["id_teacher"][id_teacher]
    lst = db["teacher"][full_name][comm]

    kb = types.InlineKeyboardMarkup(row_width=3)
    btn0 = types.InlineKeyboardButton(text="◀️", callback_data=f"{comm}_{num - 1}_{id_teacher}") \
        if num != 0 and len(lst) > 0 else None
    btn1 = types.InlineKeyboardButton(text=str(num + 1), callback_data="pass") if len(lst) > 0 else None
    btn2 = types.InlineKeyboardButton(text="▶️", callback_data=f"{comm}_{num + 1}_{id_teacher}") \
        if num != len(lst) - 1 and len(lst) > 0 else None
    kb.add(*[i for i in (btn0, btn1, btn2) if i])
    kb.add(types.InlineKeyboardButton(text="Назад ⬅", callback_data=f"back_{id_teacher}"),
           types.InlineKeyboardButton(text="Написать отзыв" if comm == 'review' else "Добавить цитату",
                                      callback_data=f"make_{comm}_{id_teacher}"))

    text = (f"{'Отзывы на' if comm == 'review' else 'Цитаты от'} {full_name}:\n"
            f"{hcite(lst[num]) if len(lst) > 0 else hitalic('Ничего не нашлось.')}")

    await bot.edit_message_caption(chat_id=callback.message.chat.id,
                                   message_id=callback.message.message_id,
                                   caption=text, reply_markup=kb, parse_mode='HTML')


# Сохранение изменений в профиле учителя
@bot.callback_query_handler(func=lambda callback: "save_edit_" in callback.data)
async def callback_save_edit(callback):
    id = str(callback.message.chat.id)
    full_name = db["admin"][id]["edit_teacher"]['full_name']
    id_teacher = db["teacher"][full_name]['id_teacher']
    edit = {'ФИО': 'full_name', 'Предмет': "subject", "Фото": "photo"}[db["admin"][id]["edit_teacher"]['edit']]
    new_obj = db['admin'][id]['edit_teacher']['new']
    db['admin'][id]['edit_teacher']['full_name'] = ''
    db['admin'][id]['edit_teacher']['edit'] = ''
    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id)

    if 'dont' not in callback.data:
        if edit == "full_name":
            db["teacher"][new_obj.title()] = db["teacher"][full_name]
            db["id_teacher"][str(id_teacher)] = new_obj.title()
            if new_obj.title() in db['quote']:
                db['quote'][new_obj.title()] = db['quote'][full_name]
            if new_obj.title() in db['review']:
                db['review'][new_obj.title()] = db['review'][full_name]
            del db["teacher"][full_name]
        else:
            db['teacher'][full_name][edit] = new_obj

        callback.data = f'open_{id_teacher}'
        await callback_open(callback)
        await bot.send_message(int(id), '↑ Данные успешно обновлены ↑')
    else:
        await bot.send_message(int(id), 'Действие отменено.')
    update_db()


# Запрос: на что именно изменять данные у учителя
@bot.callback_query_handler(func=lambda callback: "_editing_" in callback.data)
async def callback_editing(callback):
    obj, _, id_teacher = callback.data.split("_")
    full_name = db["id_teacher"][id_teacher]
    text = f"Введите новые данные ({obj}):"
    db['admin'][str(callback.message.chat.id)]['edit_teacher']['full_name'] = full_name
    db['admin'][str(callback.message.chat.id)]['edit_teacher']['edit'] = obj

    update_db()

    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await bot.send_message(callback.message.chat.id, text)


# Запрос: какие изменять данные у учителя
@bot.callback_query_handler(func=lambda callback: "edit_" in callback.data)
async def callback_edit(callback):
    id_teacher = callback.data[5:]
    if db['admin'][str(callback.message.chat.id)]['edit_teacher']['full_name']:
        db['admin'][str(callback.message.chat.id)]['edit_teacher']['full_name'] = ''
        db['admin'][str(callback.message.chat.id)]['edit_teacher']['edit'] = ''

        update_db()

    text = "Выберете, что вы хотите изменить:"
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(*[types.InlineKeyboardButton(text=f"{i}", callback_data=f"{i}_editing_{id_teacher}") for i in
             ('ФИО', "Предмет", "Фото")])

    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await bot.send_message(callback.message.chat.id, text, reply_markup=kb)


# Добавление цитаты/отзыва, предложенных юзером (только админы)
@bot.callback_query_handler(func=lambda callback: "add_quote_" in callback.data or "add_review_" in callback.data)
async def callback_add_q_or_r(callback):
    _, comm, id_teacher, q_or_r = callback.data.split("_")
    teacher = db["id_teacher"][id_teacher]
    q_or_r = db[comm][teacher].pop(int(q_or_r))
    db['teacher'][teacher][comm].append(q_or_r)

    update_db()

    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await bot.send_message(callback.message.chat.id,
                           ("Цитата была добавлена" if comm == 'quote' else "Отзыв был добавлен") +
                           f" учителю {hitalic(teacher)}", parse_mode='HTML')


# Удаление цитаты/отзыва, предложенных юзером (только админы)
@bot.callback_query_handler(func=lambda callback: "del_quote_" in callback.data or "del_review_" in callback.data)
async def callback_del_q_or_r(callback):
    _, comm, id_teacher, q_or_r = callback.data.split("_")
    teacher = db["id_teacher"][id_teacher]
    del db[comm][teacher][int(q_or_r)]

    update_db()

    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await bot.send_message(callback.message.chat.id, "Цитата была удалена." if comm == 'quote' else "Отзыв был удален.")


# Удаление учителя или отмена (обработка с кнопок: удалить/не удалять)
@bot.callback_query_handler(func=lambda callback: "delete_" in callback.data)
async def callback_delete(callback):
    if 'dont' not in callback.data:
        full_name = db["id_teacher"][callback.data[7:]]
        del db["teacher"][full_name]
        del db["id_teacher"][callback.data[7:]]
        if full_name in db['quote']:
            del db['quote'][full_name]
        if full_name in db['review']:
            del db['review'][full_name]
        text = "Учитель успешно удалён."

        update_db()

    else:
        text = "Действие отменено."
    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await bot.send_message(callback.message.chat.id, text)


# Удаление учителя или отмена (создание кнопок: удалить/не удалять)
@bot.callback_query_handler(func=lambda callback: "del_" in callback.data)
async def callback_del(callback):
    full_name = db["id_teacher"][int(callback.data[4:])]
    text = f'Вы уверены, что хотите безвозвратно удалить учителя {hbold(full_name)} ?'
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(types.InlineKeyboardButton(text="Да", callback_data=f'delete_{callback.data[4:]}'),
           types.InlineKeyboardButton(text="Нет, отмена!", callback_data='dont_delete_'))

    await bot.edit_message_reply_markup(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await bot.send_message(callback.message.chat.id, text, parse_mode='HTML', reply_markup=kb)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True, content_types=["text", "photo"])
async def text_processing(message):
    text = ''
    id = str(message.from_user.id)
    if id in db["user"]:
        # написать цитату/отзыв
        if db["user"][id]["make_review"] or db["user"][id]["make_quote"]:
            comm = "review" if db["user"][id]["make_review"] else "quote"
            id_teacher = db['teacher'][db["user"][id]["make_review"] or db["user"][id]["make_quote"]]['id_teacher']

            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(types.InlineKeyboardButton(text="OK", callback_data=f'OK_{comm}_'
                                                                       f'{id_teacher}'),
                   types.InlineKeyboardButton(text="Изменить", callback_data=f'make_{comm}_'
                                                                             f'{id_teacher}'),
                   types.InlineKeyboardButton(
                       text=f"Удалить и не {'оставлять отзыв' if comm == 'review' else 'добавить цитату'}",
                       callback_data=f'off_{comm}_{id_teacher}'))
            text = (f"Ваш{' отзыв' if comm == 'review' else 'у цитату'} будут видеть так:\n"
                    f"{hcite(message.text)}\n\n"
                    f"Пожалуйста, проверьте {'его' if comm == 'review' else 'её'} на правильность.\n"
                    f"Нажав {hitalic('OK')}, вы уже не сможете ничего изменить!")
            await bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=kb)
            text = ''

        # Написать в поддержку
        elif db['user'][id]['support']:
            if len(db['support']) > 0:
                db['support'][str(max([int(i) for i in db['support']]) + 1)] = [message.text, str(message.from_user.id)]
            else:
                db['support']['1'] = [message.text, str(message.from_user.id)]

            db['user'][id]['support'] = False
            await bot.send_message(message.chat.id, 'Благодарим вас за обратную связь ❤️\n'
                                                    'Постараемся вам ответить в ближайшее время.')
    # Обработка сообщений админов
    if id in db["admin"]:

        # Добавление учителя
        if db["admin"][id]["add_teacher"]["start"]:
            shortcut = db["admin"][id]["add_teacher"]
            if message.photo and shortcut["full_name"] and shortcut["subject"]:
                shortcut["photo"] = message.photo[0].file_id
                shortcut["start"] = False

                n = int(max(list(db["id_teacher"].keys()))) + 1 if len(db["id_teacher"]) > 0 else 0
                db["id_teacher"][str(n)] = shortcut["full_name"]

                db["teacher"][shortcut["full_name"]] = {'subject': shortcut["subject"],
                                                        'photo': message.photo[0].file_id,
                                                        'rating': [], 'quote': [], 'review': [],
                                                        "id_teacher": str(n)}
                text, photo, kb = about_teacher_short(shortcut["full_name"],
                                                      db["teacher"][shortcut["full_name"]], id, str(n))
                await bot.send_photo(message.chat.id, photo, text, parse_mode='HTML', reply_markup=kb)

                shortcut["full_name"], shortcut["subject"], shortcut["photo"] = "", "", ""
                text = "↑ Учитель добавлен! ↑"

            elif not shortcut["full_name"] and ("".join(message.text.split())).isalpha() and len(
                    message.text.split()) == 3:
                shortcut["full_name"] = " ".join(message.text.split()).title()

                text = "Введите предмет учителя"

            elif not shortcut["subject"] and ("".join(message.text.split())).isalpha() and shortcut["full_name"]:
                shortcut["subject"] = " ".join(message.text.split())
                text = "Отправьте ОДНО фото учителя"

            else:
                text = ("Что-то пошло не так!\n\n"
                        "Проверьте формат отправляемых данных: \n"
                        "Фамилия Имя Отчество (в 3 слова, только буквы)\n"
                        "Предмет (только буквы)\n"
                        "Фото (не более 1 фото)")

        # Редактирование учителя
        elif db["admin"][id]["edit_teacher"]['full_name']:
            shortcut = db["admin"][id]["edit_teacher"]
            shortcut['new'] = message.text if not message.photo else message.photo[0].file_id
            if shortcut['edit'] != 'ФИО' or message.text.title() not in db['teacher']:
                if shortcut['edit'] == 'ФИО':
                    shortcut["new"] = shortcut["new"].title()
                if not message.photo:
                    text = (
                        f"Вы уверены, что хотите изменить {hitalic(shortcut['edit'])} у учителя {hitalic(shortcut['full_name'])} на:\n"
                        f'{hbold(shortcut["new"])} ?')
                else:
                    text = f"Вы уверены, что хотите изменить {hitalic('Фото')} у учителя {hitalic(shortcut['full_name'])} на данное ↑ ?\n"

                kb = types.InlineKeyboardMarkup(row_width=3)
                kb.add(types.InlineKeyboardButton(text="Да", callback_data='save_edit_'),
                       types.InlineKeyboardButton(text="Нет, редактировать",
                                                  callback_data=f'edit_{db["teacher"][shortcut["full_name"]]["id_teacher"]}'),
                       types.InlineKeyboardButton(text=f"Удалить и ничего не менять", callback_data=f"dont_save_edit_"))

                await bot.send_message(message.from_user.id, text, parse_mode='HTML', reply_markup=kb)
                text = ''
            else:
                text = "Этот учитель уже существует в базе данных. Введите другое ФИО"

        # Добавление админа
        elif db['admin'][id]["add_admin"]:
            if message.text in db['user']:
                db['admin'][id]["add_admin"] = False
                db['admin'][message.text] = {"first_name": db['user'][message.text]['first_name'],
                                             "developer_status": False,
                                             "add_teacher": {"start": False, "full_name": '',
                                                             "subject": '', "photo": ''},
                                             "edit_teacher": {"full_name": '', 'edit': '', 'new': ''},
                                             "add_admin": False, 'del_admin': False}

                await bot.send_message(message.from_user.id,
                                       f"Пользователь " +
                                       hlink(db['user'][message.text]['first_name'], f"tg://user?id={message.text}") +
                                       " теперь админ.", parse_mode='HTML')
                await bot.send_message(message.text,
                                       "Вы теперь админ! Вам доступно меня /admin_menu и ещё много всего!")
            else:
                text = 'Такого пользователя нет в базе данных. Его нельзя сделать админом. Введите ещё раз.'

        # Удаление админа
        elif db['admin'][id]["del_admin"]:
            if message.text in db['admin']:
                db['admin'][id]["del_admin"] = False
                del db['admin'][message.text]

                await bot.send_message(message.from_user.id,
                                       f"Пользователь " +
                                       hlink(db['user'][message.text]['first_name'], f"tg://user?id={message.text}") +
                                       " больше не админ.", parse_mode='HTML')
            else:
                text = 'Такого пользователя нет в базе данных. Его нельзя удалить из админов. Введите ещё раз.'

        # Ответ поддержки на вопрос пользователя
        elif message.reply_to_message and message.reply_to_message.text.startswith('support_'):
            num_mess = message.reply_to_message.text.split('\n')[0][8:]
            if num_mess in db['support']:
                id_chat = db['support'][num_mess][1]
                await bot.send_message(id_chat, 'Ответ на ваш запрос в поддержку!\n' + hcite(
                    db['support'][num_mess][0]) + '\n\n' + f'{message.text}', parse_mode='HTML')
                await bot.send_message(message.from_user.id, 'Ответ на запрос отправлен пользователю!')
                del db['support'][num_mess]

    if text:
        await bot.reply_to(message, text)
    update_db()


async def main():
    await bot.polling(non_stop=True)



# keep_alive()
asyncio.run(main())