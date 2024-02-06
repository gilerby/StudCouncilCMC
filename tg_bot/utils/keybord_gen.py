from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def make_row_keyboard(items: list[str], resize = False, adjust = 1) -> ReplyKeyboardMarkup:
    """
    Создаёт реплай-клавиатуру с кнопками в один ряд
    :param items: список текстов для кнопок
    :return: объект реплай-клавиатуры
    """

    builder = ReplyKeyboardBuilder()
    for elem in items:
        builder.add(types.KeyboardButton(text=elem))
    builder.adjust(adjust)

    return builder.as_markup(  one_time_keyboard = True, 
                               input_field_placeholder = 'Нажмите ↓',
                               resize_keyboard=resize)




def get_keyboard_inline(items: list[list[str]], adjust: list[int]):
    builder = InlineKeyboardBuilder()
    for elem in items:
        builder.button( text=str(elem[0]), callback_data=str(elem[1]))
   
    builder.adjust(*adjust)
    # Выравниваем кнопки по 4 в ряд, чтобы получилось 4 + 1
    return builder.as_markup()



