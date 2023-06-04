from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import *
import logging
import phonenumbers

# Logging for check
logging.basicConfig(level=logging.INFO)

# Connecting Bot
bot = Bot(bot_token)
dp = Dispatcher(bot)
dp.message_handler(commands=['start'])

# Setting buttons
# Menu
menu_buttons = InlineKeyboardMarkup(row_width=2)
button_schedule = InlineKeyboardButton(text='Расписание тренировок📆', callback_data='schedule')
button_sign_up = InlineKeyboardButton(text='Запись на тренировку🏒', callback_data='sign up')
button_contacts = InlineKeyboardButton(text='Контакты📞', callback_data='contacts')
button_where = InlineKeyboardButton(text='Как добраться🚗', callback_data='where')
menu_buttons.row(button_schedule).row(button_contacts, button_where)

# Back buttons
back_button = InlineKeyboardMarkup(row_width=1).row(
    InlineKeyboardButton('Назад⬅️', callback_data='back'))


@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await bot.send_message(message.from_user.id, text_menu_first + message.from_user.username + text_menu_second, parse_mode='html')



@dp.callback_query_handler(text='schedule')
async def schedule_trainings(call: types.CallbackQuery):
    await call.message.delete()
    with open('schedule.jpg', 'rb') as photo:
        photo = open('schedule.jpg', 'rb')
        await call.message.answer_photo(photo=photo, reply_markup=back_button)


@dp.callback_query_handler(text='sign up')
async def schedule_trainings(call: types.CallbackQuery):
    await call.message.delete()
    with open('schedule.jpg', 'rb') as photo:
        photo = open('schedule.jpg', 'rb')
        await call.message.answer_photo(photo=photo, reply_markup=back_button)


@dp.callback_query_handler(text='contacts')
async def get_contacts(call: types.CallbackQuery):
    await call.message.edit_text('<b>Телефон:</b> +7(916)645-53-43', parse_mode='html',
                                 reply_markup=back_button)


@dp.callback_query_handler(text='where')
async def location(call: types.CallbackQuery):
    await call.message.delete()
    await bot.send_location(call.from_user.id, 55.723572, 37.677364, reply_markup=back_button)


@dp.callback_query_handler(text='back')
async def back_func(call: types.CallbackQuery):
    if call.message.photo or call.message.location:
        await call.message.delete()
        await call.message.answer('Проверка', reply_markup=menu_buttons)
    else:
        await call.message.edit_text('Проверка', reply_markup=menu_buttons)


if __name__ == "__main__":
    executor.start_polling(dp)
