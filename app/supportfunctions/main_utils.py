import pytz
from datetime import datetime
from aiogram.types import CallbackQuery


from app.components.keyboard import ScheduleKeyboards
from app.database.requests import get_image

#Красноярское время
krasnoyarsk_tz = pytz.timezone('Asia/Krasnoyarsk')

#Получение текущего дня
async def get_week():
    curr_time = datetime.now(krasnoyarsk_tz)
    day = curr_time.strftime('%A').lower()
    return day


#Обработка "Расписание на сегодня"
async def get_fast_rasp(week):
    f = await get_image(week)
    message = {
        "monday": "<b>🗓 Расписание на понедельник</b>",
        "tuesday": "<b>🗓 Расписание на вторник</b>",
        "wednesday": "<b>🗓 Расписание на среду</b>",
        "thursday": "<b>🗓 Расписание на четверг</b>",
        "friday": "<b>🗓 Расписание на пятницу</b>"
    }
    markup = {
        "monday": ScheduleKeyboards.monday,
        "tuesday": ScheduleKeyboards.tuesday,
        "wednesday": ScheduleKeyboards.wednesday,
        "thursday": ScheduleKeyboards.thursday,
        "friday": ScheduleKeyboards.friday
    }
    return f, message[week], markup[week]

    
async def try_delete_msg_callback(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass