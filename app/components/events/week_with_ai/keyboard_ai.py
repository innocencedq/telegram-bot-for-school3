from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


async def kb_ai():
    build = InlineKeyboardBuilder()

    build.add(InlineKeyboardButton(text='⬅️ Назад', callback_data='events'))

    return build.adjust(1).as_markup()