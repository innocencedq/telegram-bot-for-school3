import aiohttp
from app.database.requests import get_refresh_token, update_tokens
from app.components.logs.logs import logger


async def refresh_token(user, token: str = None):
    refresh_token = token if token else await get_refresh_token(user)
    url = "https://diaryapi.kiasuo.ru/diary/refresh"
    headers = {
        "Host":"diaryapi.kiasuo.ru",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
        "Access-Control-Allow-Credentials": "true",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "DNT": "1",
        "Origin": "https://pwa.kiasuo.ru",
        "Pragma": "no-cache",
        "Priority": "u=4",
        "Referer": "https://pwa.kiasuo.ru/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-GPC": "1",
    }
    payload = {
        "refresh-token": f"{refresh_token}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                new_access_token = data.get("accessToken")
                new_refresh_token = data.get("refreshToken")
                await update_tokens(new_access_token, new_refresh_token, user)
                return 'success'
            else:
                await logger.error('Update tokens unexpected error')
                return 'failed'
            
            