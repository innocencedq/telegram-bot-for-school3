import asyncio
from aiogram.types import Chat
from aiogram.exceptions import TelegramForbiddenError

from app.database.requests import get_all_users, delete_user
from app.components.logs.logs import logger

async def remove_blocked_users():
    while True:
        try:
            all_users = await get_all_users()

            try:
                for user in all_users:
                    from run import bot
                    await bot.send_chat_action(user, 'typing')

                await asyncio.sleep(432000)
            except TelegramForbiddenError:
                await logger.info(f"{user} blocked bot!")
                await delete_user(user)
            except Exception:
                await logger.error("Unexcpected error in check_users.py // remove_blocked_users()")
        except Exception:
            await logger.error("Unexcpected error in check_users.py // remove_blocked_users()")
            await asyncio.sleep(3600)
