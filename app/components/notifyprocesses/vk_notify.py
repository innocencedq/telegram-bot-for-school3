import aiohttp
import asyncio
import logging
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter, TelegramBadRequest
from sqlalchemy import delete
from config import vk_token

from app.components.logs.logs import logger
from app.database.data import async_session, User
from app.database.requests import get_all_users_with_notify
from app.components.keyboard import for_vk_notify

#Запрос
async def vk_api_request(method, params):
    url = f"https://api.vk.com/method/{method}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            return data


#Получение последнего поста
async def get_last_post_id(group_id):
    params = {
        "owner_id": group_id,
        "count": 5,
        "access_token": f"{vk_token}",
        "v": "5.199"
    }
    data = await vk_api_request("wall.get", params)
    if data.get("response", {}).get("items"):
        posts = data["response"]["items"]
        for post in posts:
            if not post.get("is_pinned", 0):
                return post["id"]
    return 0


#Получение новых постов
async def get_new_posts(group_id, last_post_id):
    params = {
        "owner_id": group_id,
        "count": 5,
        "access_token": f"{vk_token}",
        "v": "5.199"
    }
    data = await vk_api_request("wall.get", params)
    new_posts = []
    if data.get("response", {}).get("items"):
        posts = data["response"]["items"]
        for post in posts:
            if post.get("is_pinned", 0):
                continue
            if post["id"] > last_post_id:
                if post.get("copy_history"):
                    new_posts.append({
                        "text": post["copy_history"][0]["text"],
                        "url": f'https://vk.com/wall{group_id}_{post["id"]}'
                    })
                else:
                    new_posts.append({
                        "text": post["text"],
                        "url": f'https://vk.com/wall{group_id}_{post["id"]}'
                    })
                last_post_id = post["id"]
    return new_posts, last_post_id


#Отправка новых постов
async def send_new_posts():
    group_id = -217585014
    last_post_id = await get_last_post_id(group_id)
    while True:
        try:
            new_posts, last_post_id = await get_new_posts(group_id, last_post_id)
            for post in new_posts:
                post_text = post["text"]
                message = f'<b>⭕️ Новый пост в группе!</b>\n\n{post_text[:350]}...\n\n➡️ <a href="{post["url"]}">Подробнее</a>'
                for user_id in await get_all_users_with_notify():
                    try:
                        from run import bot
                        await bot.send_message(user_id, message, parse_mode="html", reply_markup=await for_vk_notify(user=user_id))
                    except TelegramForbiddenError:
                        async with async_session() as session:
                            stmt = (delete(User).where(User.tg_id == user_id))
                            await session.execute(stmt)
                            await session.commit()
                            await logger.info(f'{user_id} заблокировал бота!')
                    except TelegramRetryAfter as e:
                        retry_after = e.retry_after
                        await asyncio.sleep(retry_after)
                        continue
                    except TelegramBadRequest:
                        try:
                            async with async_session() as session:
                                stmt = (delete(User).where(User.tg_id == user_id))
                                await session.execute(stmt)
                                await session.commit()
                                await logger.info(f'{user_id} удалил аккаунт!')
                        except Exception:
                            continue
            await asyncio.sleep(600) #Задержка перед следующей проверкой (в секундах)
        except Exception as e:
            logging.error(f'Error from vk_notify: {e}')