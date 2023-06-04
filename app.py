from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import *
import logging
from phonenumbers import carrier
import phonenumbers
from phonenumbers.phonenumberutil import number_type
from datetime import datetime
import sqlite3

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
button_schedule = InlineKeyboardButton(text='Расписание тренировок📆', callback_data='schedule')
button_sign_up = InlineKeyboardButton(text='Запись на тренировку🏒', callback_data='sign up')
button_contacts = InlineKeyboardButton(text='Контакты📞', callback_data='contacts')
button_where = InlineKeyboardButton(text='Как добраться🚗', callback_data='where')
button_admin_panel = InlineKeyboardButton(text='Админ-панель', callback_data='admin')
admin_menu_buttons.row(button_schedule, button_sign_up).row(button_contacts, button_where).row(
    button_admin_panel)
menu_buttons.row(button_schedule, button_sign_up).row(button_contacts, button_where)

# Back button
back_button = InlineKeyboardMarkup(row_width=1).row(
    InlineKeyboardButton('Назад⬅️', callback_data='back'))

# Admin-panel
panel = InlineKeyboardMarkup(row_width=2)
button_add_training = InlineKeyboardButton(text='Добавить тренировку', callback_data='add tr')
button_refactor_training = InlineKeyboardButton(text='Редактировать тренировку',
                                                callback_data='refactor tr')
button_delete_training = InlineKeyboardButton(text='Удалить тренировку',
                                              callback_data='delete tr')
button_sign_up_other = InlineKeyboardButton(text='Записать на тренировку',
                                            callback_data='sign up tr')
panel.row(button_add_training, button_refactor_training).row(button_delete_training,
                                                             button_sign_up_other).row(
    InlineKeyboardButton('Назад⬅️', callback_data='back'))

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


@dp.message_handler(commands=['start'], state='*')
async def start_handler(message: types.Message, state: FSMContext):
    await state.finish()
    check = cur.execute('''SELECT * FROM Users WHERE tg_id = ?''', (message.from_user.id,)).fetchone()
    if not check:
        await state.set_state(Register.waiting_phone_number.state)
        await bot.send_message(message.from_user.id, text_register, parse_mode='html')
    else:
        if message.from_user.id in admins:
            btns = admin_menu_buttons
        else:
            btns = admin_menu_buttons
        await bot.send_message(message.from_user.id,
                               text_menu_first + message.from_user.username + text_menu_second,
                               parse_mode='html', reply_markup=btns)

@dp.message_handler(state=Register.waiting_phone_number)
async def refactor_training_chosen(message: types.Message, state: FSMContext):
    check = message.text
    if check[0] == '8':
        check = '+7' + check[1:]
    if carrier._is_mobile(number_type(phonenumbers.parse(check))):
        check = phonenumbers.format_number(phonenumbers.parse(check), phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        cur.execute('''INSERT INTO Users(tg_id, phone_number) VALUES (?, ?)''', (message.from_user.id, check))
        con.commit()
        await state.finish()
        if message.from_user.id in admins:
            btns = admin_menu_buttons
        else:
            btns = admin_menu_buttons
        await bot.send_message(message.from_user.id,
                               text_menu_first + message.from_user.username + text_menu_second,
                               parse_mode='html', reply_markup=btns)
    else:
        await bot.send_message(message.from_user.id, text_register_retry)
        return


@dp.callback_query_handler(text='admin')
async def admin_func(call: types.CallbackQuery):
    await call.message.edit_text(text_admin_panel, parse_mode='html',
                                 reply_markup=panel)


@dp.callback_query_handler(text='add tr')
async def add_training(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer(text_admin_add_training_type, parse_mode='html',
                              reply_markup=menu_choose_type)
    await state.set_state(AddTraining.waiting_for_type_training.state)


@dp.callback_query_handler(text='refactor tr')
async def refactor_training(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(RefactorTraining.waiting_id.state)
    res = ''
    every = cur.execute('''SELECT * FROM Trainings''').fetchall()
    for i in every:
        res += str(i[0]) + '. ' + str(i[1]) + ', ' + str(i[2]) + '\n'
    await call.message.edit_text(text_admin_refactor_training + res)


@dp.message_handler(state=RefactorTraining.waiting_id)
async def refactor_training_chosen(message: types.Message, state: FSMContext):
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
    data = await state.get_data()
    cur.execute('''UPDATE Trainings set type_training = ? WHERE id = ? ''',
                (message.text, data.get('id_training')))
    con.commit()
    await bot.send_message(message.from_user.id, text=text_admin_successfully_refactor, reply_markup=remove_keyboard)
    await state.finish()
    await bot.send_message(message.from_user.id, text=text_admin_panel, reply_markup=panel)


@dp.callback_query_handler(text='delete tr')
async def delete_training(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(DeleteTraining.waiting_number.state)
    res = ''
    every = cur.execute('''SELECT * FROM Trainings''').fetchall()
    for i in every:
        res += str(i[0]) + '. ' + str(i[1]) + ', ' + str(i[2]) + '\n'
    await call.message.edit_text(text_admin_delete_training + res)


@dp.message_handler(state=DeleteTraining.waiting_number)
async def delete_training_chosen(message: types.Message, state: FSMContext):
    try:
        id_training = int(message.text)
        cur.execute('''DELETE FROM Trainings WHERE id = ?''', (id_training,))
        con.commit()
        await bot.send_message(message.from_user.id, text_admin_successfully_delete)
        await state.finish()
        await bot.send_message(message.from_user.id, text=text_admin_panel, reply_markup=panel)
    except ValueError:
        await bot.send_message(message.from_user.id, text_admin_delete_training_retry)


@dp.message_handler(state=AddTraining.waiting_for_type_training)
async def type_training_chosen(message: types.Message, state: FSMContext):
    await state.update_data(chosen_type_training=message.text)
    await state.set_state(AddTraining.waiting_for_date_training.state)
    await bot.send_message(message.from_user.id, text=text_admin_add_training_date,
                           reply_markup=remove_keyboard)


@dp.message_handler(state=AddTraining.waiting_for_date_training)
async def date_training_chosen(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        date_time = datetime.strptime(message.text, '%d.%m %H:%M')
        date_time = date_time.replace(year=2023)
        cur.execute('''INSERT INTO Trainings(type_training, datetime) VALUES (?, ?)''',
                    (data['chosen_type_training'], date_time))
        con.commit()
        await bot.send_message(message.from_user.id, text=text_admin_successfully_add)
        await state.finish()
        await bot.send_message(message.from_user.id, text=text_admin_panel, reply_markup=panel)
    except ValueError:
        await bot.send_message(message.from_user.id, text=text_admin_add_training_date_retry)
        return


@dp.callback_query_handler(text='schedule')
async def schedule_trainings(call: types.CallbackQuery):
    await call.message.delete()
    with open('schedule.jpg', 'rb') as photo:
        photo = open('schedule.jpg', 'rb')
        await call.message.answer_photo(photo=photo, reply_markup=back_button)


@dp.callback_query_handler(text='sign up')
async def schedule_trainings(call: types.CallbackQuery, state: FSMContext):
    pass


@dp.callback_query_handler(text='contacts')
async def get_contacts(call: types.CallbackQuery):
    await call.message.edit_text(text_contacts, parse_mode='html',
                                 reply_markup=back_button)


@dp.callback_query_handler(text='where')
async def location(call: types.CallbackQuery):
    await call.message.delete()
    await bot.send_location(call.from_user.id, 55.723572, 37.677364, reply_markup=back_button)


@dp.callback_query_handler(text='back')
async def back_func(call: types.CallbackQuery):
    if call.from_user.id in admins:
        btns = admin_menu_buttons
    else:
        btns = admin_menu_buttons
    if call.message.photo or call.message.location:
        await call.message.delete()
        await call.message.answer(text_menu_first + call.from_user.username + text_menu_second,
                                  reply_markup=btns, parse_mode='html')
    else:
        await call.message.edit_text(
            text_menu_first + call.from_user.username + text_menu_second, reply_markup=btns,
            parse_mode='html')


if __name__ == "__main__":
    executor.start_polling(dp)
