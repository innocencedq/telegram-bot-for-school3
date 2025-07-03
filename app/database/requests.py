from app.database.data import User, async_session, Admin, Images, Advert
from sqlalchemy import select, func, update, delete, desc, text
from aiogram.types import Chat

from app.components.logs.logs import logger
from app.supportfunctions.redis_misc import redis


#Все названия отвечают сами за себя
async def get_all_users():
    async with async_session() as session:
        users = await session.scalars(select(User.tg_id))
        users_id = users.all()
        return users_id


async def get_all_users_with_notify():
    async with async_session() as session:
        value = await session.scalars(select(User.tg_id).filter_by(notify_vk=True))
        value = value.all()
        return value


async def get_user_with_notify(user):
    async with async_session() as session:
        value = await session.scalar(select(User.notify_vk).where(User.tg_id == user))
        return value


async def get_list_admin():
    async with async_session() as session:
        admins = await session.scalars(select(Admin.tg_id))
        admins_id = admins.all()
        return admins_id


async def get_list_username(user):
    async with async_session() as session:
        usernames = await session.scalars(select(User.username).filter_by(username=user))
        usernames_id = usernames.all()
        return usernames_id


async def get_username_with_id(username):
    async with async_session() as session:
        chat_id = await session.scalars(select(User.tg_id).filter_by(username=username))
        chat_id = chat_id.all()
        return chat_id


async def get_user_value_valentines(user_id):
    async with async_session() as session:
        value = await session.scalars(select(User.valentines_value).filter_by(tg_id=user_id))
        value = value.all()
        return value


async def get_user_value_valentines_from_top(user_id):
    async with async_session() as session:
        value = await session.scalars(select(User.valentines_top).filter_by(tg_id=user_id))
        value = value.all()
        return value


async def get_image(week_name):
    res = await redis.get(name="week_name:" + week_name)
    if not res:
        async with async_session() as session:
            image_id = await session.scalar(select(Images.image_id).where(Images.image_name == week_name))
            await redis.set(name="week_name:" + week_name, value=image_id)
            return str(image_id)
    else:
        return res
    

async def del_image_from_redis(week_name):
    await redis.delete(f'week_name:{week_name}')


async def get_requests_ai(user):
    async with async_session() as session:
        count = await session.scalar(select(User.requests_ai).where(User.tg_id == user))
        return count


async def count_users() -> int:
    async with async_session() as session:
        result = select(func.count(User.tg_id))
        result = await session.execute(result)
        return result.scalar()


async def get_quick_menu(user):
    async with async_session() as session:
        value = await session.scalar(select(User.quick_menu).where(User.tg_id == user))
        return value
    

async def get_refresh_token(user):
    async with async_session() as session:
        refresh_token = await session.scalar(select(User.refresh_token).where(User.tg_id == user))
        return refresh_token
    

async def get_access_token(user):
    res = await redis.get(name="access_token:" + str(user))
    if not res:
        async with async_session() as session:
            access_token = await session.scalar(select(User.access_token).where(User.tg_id == user))
            await redis.set(name="access_token:" + str(user), value=access_token)
            return access_token
    else:
        return res
    

async def update_tokens(access_token, refresh_token, user):
    async with async_session() as session:
        stmt = update(User).where(User.tg_id == user).values(access_token = access_token, refresh_token = refresh_token)
        await session.execute(stmt)
        await session.commit()


async def get_tester(user):
    async with async_session() as session:
        res = await session.scalar(select(User.tester).where(User.tg_id == user))
        return res
    

async def get_user_with_extended_diary(user):
    async with async_session() as session:
        res = await session.scalar(select(User.extended_diary).where(User.tg_id == user))
        return res
    

async def check_admin(user):
    res = await redis.get(name="check_admin:" + str(user))
    if not res:
        async with async_session() as session:
            sql_res = await session.scalar(select(Admin).where(Admin.tg_id == user))
            await redis.set(name="check_admin:" + str(user), value=1 if sql_res else 0, ex=21600)
    else:
        return bool(int(res))


async def delete_user(user):
    async with async_session() as session:
        stmt = (delete(User).where(User.tg_id == user))
        await session.execute(stmt)
        await session.commit()


async def advert_write_sql(advert_title, advert_description, advert_image_id: str = None):
    async with async_session() as session:
        try:
            stmt = Advert(
                title = advert_title,
                description = advert_description,
                file_id = advert_image_id if advert_image_id else None
            )
            session.add(stmt)
            await session.commit()
        except Exception as e:
            await logger.info(f'Error in advert_write_sql -> {e}')


async def get_last_advert_id():
    res = await redis.get(name='last:advert:id')
    if not res:
        async with async_session() as session:
            stmt = await session.scalar(select(Advert.id).order_by(desc(Advert.id)).limit(1))
            await redis.set(name='last:advert:id', value=str(stmt))
            return stmt
    else:
        return int(res)
    

async def refresh_last_advert_id():
    await redis.delete('last:advert:id')


async def get_all_data_about_advert(id):
    async with async_session() as session:
        stmt = await session.scalar(select(Advert).where(Advert.id == id))
        res = {
            "id": stmt.id,
            "title": stmt.title,
            "description": stmt.description,
            "image_id": stmt.file_id
        }
        return res
    

async def update_data_about_advert(id, advert_title, advert_desc, advert_image):
    async with async_session() as session:
        stmt = update(Advert).where(Advert.id == id).values(title = advert_title,
                                                            description = advert_desc,
                                                            file_id = advert_image)
        await session.execute(stmt)
        await session.commit()


async def deleting_data_about_advert(id):
    async with async_session() as session:
        stmt = (delete(Advert).where(Advert.id == id))
        await session.execute(stmt)

        result = await session.execute(select(Advert).order_by(Advert.id))
        items = result.scalars().all()

        for index, item in enumerate(items, start=1):
            if item.id != index:
                await session.execute(
                    text(f"UPDATE advert SET id = {index} WHERE id = {item.id}")
                )
        
        await session.commit()