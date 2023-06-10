from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import *
from texts import *
import logging
from phonenumbers import carrier
import phonenumbers
from phonenumbers.phonenumberutil import number_type
from datetime import datetime
import sqlite3
import locale
import pymorphy2

# Settings for Russian days of week
locale.setlocale(locale.LC_ALL, '')

# Logging for check
logging.basicConfig(level=logging.INFO)

# Connecting DB
con = sqlite3.connect('data.db')
cur = con.cursor()

# Connecting Bot
bot = Bot(bot_token)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.message_handler(commands=['start'])

# Setting buttons
# Menu
menu_buttons = InlineKeyboardMarkup(row_width=2)
admin_menu_buttons = InlineKeyboardMarkup(row_width=2)
trainer_menu_buttons = InlineKeyboardMarkup(row_width=2)
button_schedule = InlineKeyboardButton(text='Расписание📆', callback_data='schedule')
button_sign_up = InlineKeyboardButton(text='Запись🏒', callback_data='sign up')
button_contacts = InlineKeyboardButton(text='Контакты📞', callback_data='contacts')
button_where = InlineKeyboardButton(text='Как добраться🚗', callback_data='where')
button_admin_panel = InlineKeyboardButton(text='Админ-панель👑', callback_data='admin')
admin_menu_buttons.row(button_schedule, button_sign_up).row(button_contacts, button_where).row(
    button_admin_panel)
menu_buttons.row(button_schedule, button_sign_up).row(button_contacts, button_where)

# Back button
back_button = InlineKeyboardMarkup(row_width=1).row(
    InlineKeyboardButton('Назад⬅️', callback_data='back'))

# Admin-panel
panel = InlineKeyboardMarkup(row_width=2)
button_add_training = InlineKeyboardButton(text='➕Добавить тренировку', callback_data='add tr')
button_refactor_training = InlineKeyboardButton(text='✏️Редактировать тренировку',
                                                callback_data='refactor tr')
button_delete_training = InlineKeyboardButton(text='➖Удалить тренировку',
                                              callback_data='delete tr')
button_sign_up_other = InlineKeyboardButton(text='📝Записать на тренировку',
                                            callback_data='sign up tr')
panel.row(button_add_training, button_refactor_training).row(button_delete_training,
                                                             button_sign_up_other).row(
    InlineKeyboardButton('Назад⬅️', callback_data='back'))

# Trainer's buttons
trainer_menu_buttons.row(button_schedule, button_sign_up).row(button_contacts,
                                                              button_where).row(
    button_sign_up_other)

# Choose types of training
menu_choose_type = ReplyKeyboardMarkup(row_width=2)
button_choose_game = KeyboardButton(text='Игровая')
button_choose_complex = KeyboardButton(text='Комплексная')
button_choose_individual = KeyboardButton(text='Индивидуальная')
button_choose_ofp_sfp = KeyboardButton(text='ОФП/СФП')
menu_choose_type.row(button_choose_game, button_choose_complex).row(button_choose_individual,
                                                                    button_choose_ofp_sfp)

# RemoveKeyboardButton
remove_keyboard = ReplyKeyboardRemove()

# Button for notifications
menu_notifications = InlineKeyboardMarkup(row_width=2)
button_notifications = InlineKeyboardButton(text='Записаться на тренировку',
                                            url="https://t.me/abchockeybot")
menu_notifications.add(button_notifications)


class AddTraining(StatesGroup):
    waiting_for_type_training = State()
    waiting_for_date_training = State()


class DeleteTraining(StatesGroup):
    waiting_number = State()


class RefactorTraining(StatesGroup):
    waiting_id = State()
    waiting_column = State()
    waiting_date = State()
    waiting_type = State()


class Register(StatesGroup):
    waiting_phone_number = State()


class SignUp(StatesGroup):
    waiting_number = State()
    waiting_fi = State()
    waiting_born = State()


class SignUpTr(StatesGroup):
    waiting_number = State()
    waiting_fi = State()
    waiting_born = State()
    waiting_phone_number = State()


def get_members(id_training):
    training = cur.execute('''SELECT * FROM Trainings WHERE id = ?''',
                           (id_training,)).fetchone()
    every = cur.execute('''SELECT * FROM user_to_training WHERE training_id = ?''',
                        (id_training,)).fetchall()
    res = str(training[2]).split(' ')[0] + ' ' + training[1] + ' ' + ':'.join(
        str(training[2]).split(' ')[1].split(':')[:-1]) + '\nУчастники:\n'
    for i in range(len(every)):
        res += str(i + 1) + '. ' + every[i][4] + ', ' + every[i][3].split(' ')[0].split('-')[
            0] + '\n'
    return res, training[3]


def get_members_private(id_training):
    training = cur.execute('''SELECT * FROM Trainings WHERE id = ?''',
                           (id_training,)).fetchone()
    every = cur.execute('''SELECT * FROM user_to_training WHERE training_id = ?''',
                        (id_training,)).fetchall()
    res = str(training[2]).split(' ')[0] + ' ' + training[1] + ' ' + ':'.join(
        str(training[2]).split(' ')[1].split(':')[:-1]) + '\nУчастники:\n'
    for i in range(len(every)):
        res += str(i + 1) + '. ' + every[i][4] + ', ' + every[i][3].split(' ')[0].split('-')[
            0] + ', ' + every[i][5] + '\n'
    return res, training[4]


def check_banned(tg_id):
    check = cur.execute('''SELECT * FROM Banned WHERE tg_id=?''', (tg_id,)).fetchone()
    if check:
        return True
    return False


@dp.message_handler(text='Назад⬅️', state='*')
async def back_func(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    await bot.send_message(message.from_user.id, text_back, reply_markup=remove_keyboard)
    await state.finish()
    if message.from_user.id in admins:
        btns = admin_menu_buttons
    elif message.from_user.id in trainers:
        btns = trainer_menu_buttons
    else:
        btns = menu_buttons
    await bot.send_message(message.from_user.id,
                           text_menu_first + message.from_user.first_name + ' ' + message.from_user.last_name + text_menu_second,
                           parse_mode='html', reply_markup=btns)


@dp.message_handler(commands=['start'], state='*')
async def start_handler(message: types.Message, state: FSMContext):
    await bot.send_message(id_tech_chat, '[' + str(
        message.from_user.id) + '] ' + message.from_user.first_name + ' ' + message.from_user.last_name + ': Команда /start')
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    await state.finish()
    check = cur.execute('''SELECT * FROM Users WHERE tg_id = ?''',
                        (message.from_user.id,)).fetchone()
    if not check:
        await state.set_state(Register.waiting_phone_number.state)
        await bot.send_message(message.from_user.id, text_register, parse_mode='html')
    else:
        if message.from_user.id in admins:
            btns = admin_menu_buttons
        elif message.from_user.id in trainers:
            btns = trainer_menu_buttons
        else:
            btns = menu_buttons
        await bot.send_message(message.from_user.id,
                               text_menu_first + message.from_user.first_name + ' ' + message.from_user.last_name + text_menu_second,
                               parse_mode='html', reply_markup=btns)


@dp.message_handler(commands=['ban'])
async def ban_handler(message: types.Message):
    await bot.send_message(id_tech_chat, '[' + str(
        message.from_user.id) + '] ' + message.from_user.first_name + ' ' + message.from_user.last_name + ': Команда /ban')
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        tg_id = int(message.get_args())
        if message.from_user.id in admins:
            if tg_id in admins:
                await bot.send_message(message.from_user.id, text_ban_error)
            else:
                cur.execute('''INSERT INTO Banned(tg_id) VALUES(?)''', (tg_id,))
                con.commit()
                await bot.send_message(message.from_user.id, text_ban_successfully)
    except ValueError:
        await bot.send_message(message.from_user.id, text_ban_retry)


@dp.message_handler(commands=['unban'])
async def unban_handler(message: types.Message):
    await bot.send_message(id_tech_chat, '[' + str(
        message.from_user.id) + '] ' + message.from_user.first_name + ' ' + message.from_user.last_name + ': Команда /unban')
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        tg_id = int(message.get_args())
        if message.from_user.id in admins:
            cur.execute('''DELETE FROM Banned WHERE tg_id=?''', (tg_id,))
            con.commit()
            await bot.send_message(message.from_user.id, text_unban_successfully)
    except ValueError:
        await bot.send_message(message.from_user.id, text_ban_retry)


@dp.message_handler(commands=['del'])
async def delete_member_handler(message: types.Message):
    await bot.send_message(id_tech_chat, '[' + str(
        message.from_user.id) + '] ' + message.from_user.first_name + ' ' + message.from_user.last_name + ': Команда /del')
    if message.from_user.id in admins:
        my_args = message.get_args()
        fi = ' '.join(my_args.split()[:2])
        birthday = datetime.strptime(my_args.split()[2], '%y')
        type_training = ' '.join(my_args.split()[3:])
        every = cur.execute('''SELECT * FROM user_to_training WHERE fi = ? AND birthday = ?''',
                            (fi, birthday)).fetchall()
        for i in every:
            this_training = cur.execute('''SELECT * FROM Trainings WHERE id = ?''',
                                        (i[2],)).fetchone()
            if this_training[1] == ('<b>' + type_training + '</b>'):
                cur.execute('''DELETE FROM user_to_training WHERE id = ?''', (i[0],))
                con.commit()
                res, msg_id = get_members(i[2])
                await bot.edit_message_text(message_id=msg_id, chat_id=id_chat, text=res,
                                            parse_mode='html')
        await bot.send_message(message.from_user.id, text_delete_member_successfully)


@dp.message_handler(commands=['p'])
async def notifications(message: types.Message):
    await bot.send_message(id_tech_chat, '[' + str(
        message.from_user.id) + '] ' + message.from_user.first_name + ' ' + message.from_user.last_name + ': Команда /p')
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    if message.from_user.id in admins:
        await bot.send_message(id_channel, message.text[3:], reply_markup=menu_notifications)


@dp.message_handler(state=Register.waiting_phone_number)
async def refactor_training_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    check = message.text
    if check[0] == '8':
        check = '+7' + check[1:]
    try:
        if carrier._is_mobile(number_type(phonenumbers.parse(check))):
            check = phonenumbers.format_number(phonenumbers.parse(check),
                                               phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            cur.execute('''INSERT INTO Users(tg_id, phone_number) VALUES (?, ?)''',
                        (message.from_user.id, check))
            con.commit()
            await state.finish()
            if message.from_user.id in admins:
                btns = admin_menu_buttons
            elif message.from_user.id in trainers:
                btns = trainer_menu_buttons
            else:
                btns = menu_buttons
            await bot.send_message(message.from_user.id,
                                   text_menu_first + message.from_user.first_name + ' ' + message.from_user.last_name + text_menu_second,
                                   parse_mode='html', reply_markup=btns)
        else:
            await bot.send_message(message.from_user.id, text_register_retry)
            return
    except:
        await bot.send_message(message.from_user.id, text_register_retry)
        return


@dp.callback_query_handler(text='admin')
async def admin_func(call: types.CallbackQuery):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Открыл админ-панель')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    await call.message.edit_text(text_admin_panel, parse_mode='html',
                                 reply_markup=panel)


@dp.callback_query_handler(text='add tr')
async def add_training(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Начал добавлять тренировку')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text_admin_add_training_type, parse_mode='html',
                              reply_markup=menu_choose_type)
    await state.set_state(AddTraining.waiting_for_type_training.state)


@dp.callback_query_handler(text='refactor tr')
async def refactor_training(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Начал изменять тренировку')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    await state.set_state(RefactorTraining.waiting_id.state)
    try:
        await call.message.delete()
    except Exception:
        pass
    res = ''
    menu_numbers = ReplyKeyboardMarkup()
    menu_numbers.add(KeyboardButton('Назад⬅️'))
    every = cur.execute('''SELECT * FROM Trainings''').fetchall()
    for i in every:
        menu_numbers.add(KeyboardButton(str(i[0])))
        res += '<b>#' + str(i[0]) + '</b> ' + str(i[2]).split(' ')[0] + ' ' + str(
            i[1]) + ' ' + ':'.join(str(i[2]).split(' ')[1].split(':')[:-1]) + '\n'
    await bot.send_message(call.from_user.id, text_admin_refactor_training + res,
                           reply_markup=menu_numbers, parse_mode='html')


@dp.message_handler(state=RefactorTraining.waiting_id)
async def refactor_training_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        id_training = int(message.text)
        this_training = cur.execute('''SELECT * FROM Trainings WHERE id = ?''',
                                    (id_training,)).fetchone()
        if not this_training:
            await bot.send_message(message.from_user.id, text_admin_delete_training_retry)
            return
        await state.update_data(id_training=id_training)
        await state.set_state(RefactorTraining.waiting_column.state)
        await bot.send_message(message.from_user.id,
                               text_admin_refactor_training_column + '1. Тип тренировки - ' +
                               this_training[1] + '\n2. Дата и время - ' + str(
                                   this_training[2]))
    except ValueError:
        await bot.send_message(message.from_user.id, text_admin_delete_training_retry)
        return


@dp.message_handler(state=RefactorTraining.waiting_column)
async def refactor_training_chosen_column(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    if message.text == '1':
        await state.set_state(RefactorTraining.waiting_type.state)
        await bot.send_message(message.from_user.id, text_admin_refactor_training_type,
                               reply_markup=menu_choose_type)
    elif message.text == '2':
        await state.set_state(RefactorTraining.waiting_date.state)
        await bot.send_message(message.from_user.id, text_admin_refactor_training_date)
    else:
        await bot.send_message(message.from_user.id, text_admin_refactor_training_retry)
        return


@dp.message_handler(state=RefactorTraining.waiting_date)
async def refactor_training_chosen_column_date(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        data = await state.get_data()
        date_time = datetime.strptime(message.text, '%d.%m %H:%M')
        date_time = date_time.replace(year=2023)
        cur.execute('''UPDATE Trainings set datetime = ? WHERE id = ? ''',
                    (date_time, data.get('id_training')))
        con.commit()
        await bot.send_message(message.from_user.id, text=text_admin_successfully_refactor)
        await state.finish()
        await bot.send_message(message.from_user.id, text=text_admin_panel, reply_markup=panel)
    except ValueError:
        await bot.send_message(message.from_user.id, text=text_admin_add_training_date_retry)
        return


@dp.message_handler(state=RefactorTraining.waiting_type)
async def refactor_training_chosen_column_type(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    data = await state.get_data()
    cur.execute('''UPDATE Trainings set type_training = ? WHERE id = ? ''',
                (message.text, data.get('id_training')))
    con.commit()
    await bot.send_message(message.from_user.id, text=text_admin_successfully_refactor,
                           reply_markup=remove_keyboard)
    await state.finish()
    await bot.send_message(message.from_user.id, text=text_admin_panel, reply_markup=panel)


@dp.callback_query_handler(text='delete tr')
async def delete_training(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Начал удалять тренировку')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    await state.set_state(DeleteTraining.waiting_number.state)
    try:
        await call.message.delete()
    except Exception:
        pass
    res = ''
    menu_numbers = ReplyKeyboardMarkup()
    menu_numbers.add(KeyboardButton('Назад⬅️'))
    every = cur.execute('''SELECT * FROM Trainings''').fetchall()
    for i in every:
        menu_numbers.add(KeyboardButton(str(i[0])))
        res += '<b>#' + str(i[0]) + '</b> ' + str(i[2]).split(' ')[0] + ' ' + str(
            i[1]) + ' ' + ':'.join(str(i[2]).split(' ')[1].split(':')[:-1]) + '\n'

    await bot.send_message(call.from_user.id, text_admin_delete_training + res,
                           reply_markup=menu_numbers, parse_mode='html')


@dp.message_handler(state=DeleteTraining.waiting_number)
async def delete_training_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        id_training = int(message.text)
        cur.execute('''DELETE FROM Trainings WHERE id = ?''', (id_training,))
        con.commit()
        await bot.send_message(message.from_user.id, text_admin_successfully_delete,
                               reply_markup=remove_keyboard)
        await state.finish()
        await bot.send_message(message.from_user.id, text=text_admin_panel, reply_markup=panel)
    except ValueError:
        await bot.send_message(message.from_user.id, text_admin_delete_training_retry)


@dp.message_handler(state=AddTraining.waiting_for_type_training)
async def type_training_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    await state.update_data(chosen_type_training=message.text)
    await state.set_state(AddTraining.waiting_for_date_training.state)
    await bot.send_message(message.from_user.id, text=text_admin_add_training_date,
                           reply_markup=remove_keyboard)


@dp.message_handler(state=AddTraining.waiting_for_date_training)
async def date_training_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        data = await state.get_data()
        date_time = datetime.strptime(message.text, '%d.%m %H:%M')
        date_time = date_time.replace(year=2023)
        # res = str(training[2]).split(' ')[0] + ' ' + training[1] + ' ' + ':'.join(
        #     str(training[2]).split(' ')[1].split(':')[:-1]) + '\nУчастники:\n'
        # NOTIFICATION
        msg = await bot.send_message(id_chat, str(date_time).split(' ')[0] + ' <b>' + data[
            'chosen_type_training'] + '</b> ' + ':'.join(
            str(date_time).split(' ')[1].split(':')[:-1]) + '\nУчастники: ', parse_mode='html')
        # PRIVATE
        pr_msg = await bot.send_message(id_private_chat,
                                        str(date_time).split(' ')[0] + ' <b>' + data[
                                            'chosen_type_training'] + '</b> ' + ':'.join(
                                            str(date_time).split(' ')[1].split(':')[
                                            :-1]) + '\nУчастники: ', parse_mode='html')

        cur.execute(
            '''INSERT INTO Trainings(type_training, datetime, msg_id, pr_msg_id) VALUES (?, ?, ?, ?)''',
            ('<b>' + data['chosen_type_training'] + '</b>', date_time, msg.message_id,
             pr_msg.message_id))
        con.commit()
        await bot.send_message(message.from_user.id, text=text_admin_successfully_add)
        await state.finish()
        await bot.send_message(message.from_user.id, text=text_admin_panel, reply_markup=panel)
    except ValueError:
        await bot.send_message(message.from_user.id, text=text_admin_add_training_date_retry)
        return


@dp.callback_query_handler(text='schedule')
async def schedule_trainings(call: types.CallbackQuery):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Посмотрел расписание')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    with open('static/img/schedule.jpg', 'rb') as photo:
        await call.message.answer_photo(photo=photo, reply_markup=back_button)


@dp.callback_query_handler(text='sign up')
async def sign_up(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Начал записываться на тренировку')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    await state.set_state(SignUp.waiting_number.state)
    try:
        await call.message.delete()
    except Exception:
        pass
    res = text_sign_up
    menu_numbers = ReplyKeyboardMarkup()
    menu_numbers.add(KeyboardButton('Назад⬅️'))
    every = cur.execute('''SELECT * FROM Trainings ORDER BY datetime''').fetchall()
    if every:
        now = every[0][2].split()[0]
        await state.update_data(date_chosen=now)
        res += datetime.strptime(now, '%Y-%m-%d').strftime('%d.%m.%Y')
        morph = pymorphy2.MorphAnalyzer()
        pm = morph.parse(datetime.strptime(now, '%Y-%m-%d').strftime('%A'))[0]
        res += ' в ' + pm.inflect({'accs'}).word.capitalize() + text_sign_up_2
        for i in every:
            if i[2].split()[0] == now:
                menu_numbers.add(KeyboardButton(i[2].split()[1][:-3]))
                res += i[2].split()[1][:-3] + ' ' + i[1] + '\n'
            else:
                break
        await bot.send_message(call.from_user.id, res, reply_markup=menu_numbers,
                               parse_mode='html')


@dp.message_handler(state=SignUp.waiting_number)
async def sign_up_number_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        data = await state.get_data()
        now = data.get('date_chosen')
        this_training = cur.execute('''SELECT * FROM Trainings WHERE datetime = ?''',
                                    (now + ' ' + message.text + ':00',)).fetchone()
        if not this_training:
            await bot.send_message(message.from_user.id, text_admin_delete_training_retry)
            return
        check = cur.execute('''SELECT * FROM Users WHERE tg_id = ?''',
                            (message.from_user.id,)).fetchone()
        already_exists = cur.execute(
            '''SELECT * FROM user_to_training WHERE user_id=? AND training_id=? AND fi = ?''',
            (check[0], this_training[0], check[4])).fetchone()
        if already_exists:
            await state.update_data(id_training=this_training[0])
            await state.set_state(SignUp.waiting_fi.state)
            await bot.send_message(message.from_user.id, text_sign_up_fi)
            return

        if check[3]:
            cur.execute(
                '''INSERT INTO user_to_training(user_id, training_id, birthday, fi, phone_number) VALUES (?, ?, ?, ?, ?)''',
                (check[0], this_training[0], check[3], check[4], check[2]))
            con.commit()

            # NOTIFICATION
            res, msg_id = get_members(this_training[0])
            await bot.edit_message_text(message_id=msg_id, chat_id=id_chat, text=res,
                                        parse_mode='html')

            # PRIVATE
            res, msg_id = get_members_private(this_training[0])
            await bot.edit_message_text(message_id=msg_id, chat_id=id_private_chat, text=res,
                                        parse_mode='html')

            await state.finish()
            res = text_sign_up_successfully + this_training[1] + ' ' + datetime.strptime(now,
                                                                                         '%Y-%m-%d').strftime(
                '%d.%m.%Y') + ' в '
            morph = pymorphy2.MorphAnalyzer()
            pm = morph.parse(datetime.strptime(now, '%Y-%m-%d').strftime('%A'))[0]
            res += pm.inflect({'accs'}).word.capitalize() + ' в ' + message.text
            await bot.send_message(message.from_user.id, res,
                                   reply_markup=remove_keyboard, parse_mode='html')
            if message.from_user.id in admins:
                btns = admin_menu_buttons
            elif message.from_user.id in trainers:
                btns = trainer_menu_buttons
            else:
                btns = menu_buttons
            await bot.send_message(message.from_user.id,
                                   text_menu_first + message.from_user.first_name + ' ' + message.from_user.last_name + text_menu_second,
                                   parse_mode='html', reply_markup=btns)
            return
        await state.update_data(time_training=message.text)
        await state.update_data(id_training=this_training[0])
        await state.set_state(SignUp.waiting_fi.state)
        await bot.send_message(message.from_user.id, text_sign_up_fi,
                               reply_markup=remove_keyboard)
    except ValueError:
        await bot.send_message(message.from_user.id, text_admin_delete_training_retry)


@dp.message_handler(state=SignUp.waiting_fi)
async def sign_up_fi_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        fi = ' '.join(message.text.split()[:2])
        data = await state.get_data()
        date_time = datetime.strptime(message.text.split()[-1], '%y')
        user = cur.execute('''SELECT * FROM Users WHERE tg_id = ?''',
                           (message.from_user.id,)).fetchone()
        already_exists = cur.execute(
            '''SELECT * FROM user_to_training WHERE user_id=? AND training_id=? AND fi = ?''',
            (user[0], data.get('id_training'), fi)).fetchone()
        if already_exists:
            await bot.send_message(message.from_user.id, text_sign_up_already)
            await state.finish()
            if message.from_user.id in admins:
                btns = admin_menu_buttons
            elif message.from_user.id in trainers:
                btns = trainer_menu_buttons
            else:
                btns = menu_buttons
            await bot.send_message(message.from_user.id,
                                   text_menu_first + message.from_user.first_name + ' ' + message.from_user.last_name + text_menu_second,
                                   parse_mode='html', reply_markup=btns)
            return
        if not user[4]:
            cur.execute('''UPDATE Users set fi = ?, birthday = ? WHERE tg_id = ?''',
                        (fi, date_time, message.from_user.id))
            con.commit()
        cur.execute(
            '''INSERT INTO user_to_training(user_id, training_id, birthday, fi, phone_number) VALUES (?, ?, ?, ?, ?)''',
            (user[0], data.get('id_training'), date_time, fi, user[2]))
        con.commit()

        # NOTIFICATION
        res, msg_id = get_members(data.get('id_training'))
        await bot.edit_message_text(message_id=msg_id, chat_id=id_chat, text=res,
                                    parse_mode='html')
        # PRIVATE
        res, msg_id = get_members_private(data.get('id_training'))
        await bot.edit_message_text(message_id=msg_id, chat_id=id_private_chat, text=res,
                                    parse_mode='html')
        this_training = cur.execute('''SELECT * FROM Trainings WHERE id=?''',
                                    (data.get('id_training'),)).fetchone()
        now = data.get('date_chosen')
        res2 = text_sign_up_successfully + this_training[1] + ' ' + datetime.strptime(now,
                                                                                      '%Y-%m-%d').strftime(
            '%d.%m.%Y') + ' в '
        morph = pymorphy2.MorphAnalyzer()
        pm = morph.parse(datetime.strptime(now, '%Y-%m-%d').strftime('%A'))[0]
        res2 += pm.inflect({'accs'}).word.capitalize() + ' в ' + data.get('time_training')
        await state.finish()
        await bot.send_message(message.from_user.id, res2,
                               reply_markup=remove_keyboard, parse_mode='html')
        if message.from_user.id in admins:
            btns = admin_menu_buttons
        elif message.from_user.id in trainers:
            btns = trainer_menu_buttons
        else:
            btns = menu_buttons
        await bot.send_message(message.from_user.id,
                               text_menu_first + message.from_user.first_name + ' ' + message.from_user.last_name + text_menu_second,
                               parse_mode='html', reply_markup=btns)
    except ValueError:
        await bot.send_message(message.from_user.id, text=text_sign_up_retry)
        return


# ---------------------------ADMINS SIGN UP-----------------------------------

@dp.callback_query_handler(text='sign up tr')
async def sign_up_tr(call: types.CallbackQuery, state: FSMContext):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Администратор начал записывать на тренировку')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    await state.set_state(SignUpTr.waiting_phone_number.state)
    await call.message.edit_text(text_sign_up_tr)


@dp.message_handler(state=SignUpTr.waiting_phone_number)
async def sign_up_tr_phone_number_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    check = message.text
    if check[0] == '8':
        check = '+7' + check[1:]
    try:
        if carrier._is_mobile(number_type(phonenumbers.parse(check))):
            check = phonenumbers.format_number(phonenumbers.parse(check),
                                               phonenumbers.PhoneNumberFormat.INTERNATIONAL)
            await state.update_data(phone_number=check)
            await state.set_state(SignUpTr.waiting_number.state)
            res = ''
            menu_numbers = ReplyKeyboardMarkup()
            menu_numbers.add(KeyboardButton('Назад⬅️'))
            every = cur.execute('''SELECT * FROM Trainings''').fetchall()
            for i in every:
                menu_numbers.add(KeyboardButton(str(i[0])))
                res += '<b>#' + str(i[0]) + '</b> ' + str(i[2]).split(' ')[0] + ' ' + str(
                    i[1]) + ' ' + ':'.join(str(i[2]).split(' ')[1].split(':')[:-1]) + '\n'

            await bot.send_message(message.from_user.id, text_sign_up + ':\n' + res,
                                   reply_markup=menu_numbers, parse_mode='html')
        else:
            await bot.send_message(message.from_user.id, text_register_retry)
            return
    except:
        await bot.send_message(message.from_user.id, text_register_retry)
        return


@dp.message_handler(state=SignUpTr.waiting_number)
async def sign_up_tr_number_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        id_training = int(message.text)
        this_training = cur.execute('''SELECT * FROM Trainings WHERE id = ?''',
                                    (id_training,)).fetchone()
        if not this_training:
            await bot.send_message(message.from_user.id, text_admin_delete_training_retry)
            return
        await state.update_data(id_training=id_training)
        await state.set_state(SignUpTr.waiting_fi.state)
        await bot.send_message(message.from_user.id, text_sign_up_fi)
    except ValueError:
        await bot.send_message(message.from_user.id, text_admin_delete_training_retry)


@dp.message_handler(state=SignUpTr.waiting_fi)
async def sign_up_tr_fi_chosen(message: types.Message, state: FSMContext):
    if check_banned(message.from_user.id):
        await bot.send_message(message.from_user.id, text_banned)
        return
    try:
        fi = ' '.join(message.text.split()[:2])
        data = await state.get_data()
        date_time = datetime.strptime(message.text.split()[-1], '%y')
        user_id = cur.execute('''SELECT * FROM Users WHERE tg_id = ?''',
                              (message.from_user.id,)).fetchone()[0]
        cur.execute(
            '''INSERT INTO user_to_training(user_id, training_id, birthday, fi, phone_number) VALUES (?, ?, ?, ?, ?)''',
            (0, data.get('id_training'), date_time, fi,
             data.get('phone_number')))
        con.commit()

        # NOTIFICATION
        res, msg_id = get_members(data.get('id_training'))
        await bot.edit_message_text(message_id=msg_id, chat_id=id_chat, text=res,
                                    parse_mode='html')
        res, msg_id = get_members_private(data.get('id_training'))
        await bot.edit_message_text(message_id=msg_id, chat_id=id_private_chat, text=res,
                                    parse_mode='html')
        await state.finish()
        await bot.send_message(message.from_user.id, text_sign_up_tr_successfully)
        await bot.send_message(message.from_user.id, text=text_admin_panel, reply_markup=panel)
    except ValueError:
        await bot.send_message(message.from_user.id, text=text_sign_up_retry)
        return


# ---------------------------ADMINS SIGN UP-----------------------------------

@dp.callback_query_handler(text='contacts')
async def get_contacts(call: types.CallbackQuery):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Открыл контакты')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    await call.message.edit_text(text_contacts, parse_mode='html',
                                 reply_markup=back_button)


@dp.callback_query_handler(text='where')
async def location(call: types.CallbackQuery):
    await bot.send_message(id_tech_chat, '[' + str(
        call.from_user.id) + '] ' + call.from_user.first_name + ' ' + call.from_user.last_name + ': Открыл местоположение')
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    try:
        await call.message.delete()
    except Exception:
        pass
    with open('static/img/where.png', 'rb') as photo:
        await bot.send_photo(call.from_user.id, photo, caption=text_address,
                             reply_markup=back_button)


@dp.callback_query_handler(text='back')
async def back_func(call: types.CallbackQuery):
    if check_banned(call.from_user.id):
        await bot.send_message(call.from_user.id, text_banned)
        return
    if call.from_user.id in admins:
        btns = admin_menu_buttons
    elif call.from_user.id in trainers:
        btns = trainer_menu_buttons
    else:
        btns = menu_buttons
    if call.message.photo or call.message.location:
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(
            text_menu_first + call.from_user.first_name + ' ' + call.from_user.last_name + text_menu_second,
            reply_markup=btns, parse_mode='html')
    else:
        await call.message.edit_text(
            text_menu_first + call.from_user.first_name + ' ' + call.from_user.last_name + text_menu_second,
            reply_markup=btns,
            parse_mode='html')


if __name__ == "__main__":
    executor.start_polling(dp)
