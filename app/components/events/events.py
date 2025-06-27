from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from app.database.requests import get_image
from app.components.events.events_keyboard import events_keyboard

router_events = Router()


@router_events.callback_query(F.data == 'events')
async def callback_event(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    f = await get_image(week_name='main_events')
    photo = InputMediaPhoto(media=f,  caption='🎈 <b>События</b>\n\n🤖 Искусственный помощник\n\n', parse_mode='HTML')

    await callback.message.edit_media(media=photo, reply_markup=await events_keyboard(), parse_mode='html')