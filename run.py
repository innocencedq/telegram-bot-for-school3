import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from config import tg_token
from app.components.routers.handlers import router
from app.database.data import async_main
from app.components.notifyprocesses.vk_notify import send_new_posts
from app.components.routers.callbacks import router_callback
from app.components.routers.admin import router_adm
from app.components.events.events import router_events
from app.components.events.womanday.woman_day import router_woman_day
from app.components.routers.inline_mode import router_inline_mode
from app.components.events.week_with_ai.week_with_ai import week_with_ai
from app.components.diary.callback_diary import callback_diary
from app.supportfunctions.check_users import remove_blocked_users
from app.supportfunctions.redis_misc import redis

bot = Bot(token=tg_token)

#Функция инициализации
async def main():
    await async_main()
    asyncio.create_task(send_new_posts())
    asyncio.create_task(remove_blocked_users())

    dp = Dispatcher(storage=RedisStorage(redis))
    dp.include_routers(router, router_callback, router_adm, router_events, router_woman_day, router_inline_mode, week_with_ai, callback_diary)

    await dp.start_polling(bot)


#Точка входа
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt as e:
        logging.error(e)