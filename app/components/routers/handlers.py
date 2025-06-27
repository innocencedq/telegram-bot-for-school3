import asyncio
import datetime
import pytz
from aiogram import Router, F
from datetime import datetime
from aiogram.types import Message, FSInputFile, CallbackQuery, InputMediaPhoto
from aiogram.filters import CommandStart, Command
from sqlalchemy import select, update
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.components.diary.parsing import refresh_token as rf
from app.supportfunctions.main_utils import get_week, get_fast_rasp
from app.components.routers.callbacks import week_callback
from app.components.notifyprocesses.notify import notify_update, special_notify
from app.database.requests import get_all_users, get_list_admin, get_image
from app.database.data import async_session, User, Images, Static
from app.components.keyboard import main_menu as keyboard_menu, ask_notify, ask_quick_menu
from app.components.keyboard import back_main_2 as back
from app.components.keyboard import for_vk_notify as kb_vk
from app.components.keyboard import notify as hide
from config import welcome_message

router = Router()

#Команда старт + авторизация КИАСУО
@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        refresh_token = args[1]

        result = await rf(message.from_user.id, refresh_token)
        if result == 'success': 
            await message.answer('✅ Авторизация прошла успешно! Меню автоматически откроется через 1 секунду...')
            await asyncio.sleep(1)
        elif result == 'failed':
            await message.answer("❌ Ошибка на стороне КИАСУО, попробуйте позже. Меню автоматически откроется через 1 секунду...")
            await asyncio.sleep(1)


    if message.from_user.id in await get_all_users():
        await menu(message, state)
    else:
        async with async_session() as session:
            if message.from_user.id not in await get_all_users():
                username = message.from_user.username if message.from_user.username else "unspecific_user"
                new_user = User(
                             tg_id=message.from_user.id,
                             username=username,
                             )

                session.add(new_user)
                await session.commit()
        await quick_settings_notify(message=message)


#Быстрая настройка
async def quick_settings_notify(message: Message):
    await message.answer('⚙️ <b>Быстрая настройка</b>\n\nНужны ли вам уведомления о новых постах ВКонтакте?\n\n<b>Настройки можно изменить в главном меню</b>', parse_mode='HTML', reply_markup=ask_notify)

#Команда /menu
@router.message(Command('menu'))
async def menu(message: Message, state: FSMContext):
    try:
        await message.delete()
        await state.clear()
        f = await get_image(week_name='main_menu')
        await message.answer_photo(photo=f, caption=f"<b>Привет, {message.from_user.first_name}!</b> 👋\n{welcome_message}\n\nДолго обрабатываются кнопки? ->\n/menu", reply_markup=await keyboard_menu(message.from_user.id), parse_mode='html')
    except Exception as e:
        await message.answer('❌')


#Команда /whoami
@router.message(Command('whoami'))
async def givemefromdatabase(message: Message):
    await message.answer(f'Ваш ID: <b>{message.from_user.id}</b>, Ваш USERNAME: <b>@{message.from_user.username}</b>', parse_mode='html')


#Команда /correctdatabase (не использовать!)
@router.message(Command('correctdatabase'))
async def getfileid(message: Message):
    week_days = {1: 'monday', 2: 'tuesday', 3: 'thursday', 4: 'wednesday' , 5: 'friday', 6: 'calls'}
    async with async_session() as session:
        if message.from_user.id not in await get_list_admin():
            await message.answer('Нет доступа!')
        else:
            for keys, value in week_days.items():
                photo = FSInputFile(f'app/assets/raspisanie/{value}.jpg')
                sent_photo = await message.answer_photo(photo=photo)

                file_id = sent_photo.photo[-1].file_id

                existing_image = await session.execute(select(Images).where(Images.image_name == value))
                existing_image = existing_image.scalar_one_or_none()

                if existing_image:
                    stmt = update(Images).where(Images.image_name == value).values(image_id=file_id)
                    await session.execute(stmt)
                else:
                    new_image = Images(
                        image_id = file_id,
                        image_name = value
                    )
                    session.add(new_image)
                await session.commit()


#Команда рассылки обновления (не использовать!!)
@router.message(Command('sendupdate'))
async def sendupdate(message: Message):
    if message.from_user.id not in await get_list_admin():
        await message.answer('Нет доступа!')
    else:
        await notify_update()


#Айди фото
@router.message(Command('thisfileidphoto'))
async def thisfileidphoto(message: Message):
    try:
        await message.answer(f'file_id: {message.photo[-1].file_id}')
    except Exception as e:
        print(e)
        await message.answer('❌')


#Айди видео
@router.message(Command('thisfileid'))
async def thisfileid(message: Message):
    try:
        await message.answer(f'file_id: {message.video.file_id}')
    except Exception:
        await message.answer('❌')


#Получения chat_id
@router.message(Command('getmychatid'))
async def getmychatid(message: Message):
    await message.answer(f'{message.from_user.id}')


#Обработчики быстрого меню
@router.message(F.text == '🏠 Главное меню')
async def menu_text(message: Message, state: FSMContext):
    await menu(message=message, state=state)


@router.message(F.text == '🗓 Расписание на сегодня')
async def week_quick_callback(message: Message):
    user_id = message.from_user.id
    new_username = message.from_user.username if message.from_user.username else 'unspecific_user'
    async with async_session() as session:
        last_username = await session.scalar(select(User.username).where(User.tg_id == user_id))
        
        if last_username != new_username:
            stmt = update(User).where(User.tg_id == user_id).values(username = new_username)
            stmt2 = update(Static).where(Static.id == 1).values(active_users = Static.active_users + 1)
            await session.execute(stmt)
            await session.execute(stmt2)
            await session.commit()
    try:
        week = await get_week()
        f, msg, markup = await get_fast_rasp(week)

        await message.answer_photo(photo=f, caption=f'{msg}', reply_markup=markup, parse_mode='html')
    except Exception:
        await message.answer('😌 <b>Сегодня выходной!</b> Можешь спокойно отдыхать от школы)', parse_mode='html')


#Команда /ege
@router.message(Command('ege'))
async def schedule_ege(message: Message):
    await message.delete()
    text_schedule_ege = f"<b>Расписание ЕГЭ</b>\n" \
    f"<b>Основной период:</b>\n\n" \
    f"<b>23 мая (пт)</b> — история, литература и химия\n" \
    f"<b>27 мая (вт)</b> — математика базового и профильного уровней\n" \
    f"<b>30 мая (пт)</b> — русский язык\n" \
    f"<b>2 июня (пн)</b> — обществознание, физика\n" \
    f"<b>5 июня (чт)</b> — биология, география и иностранные языки (письменная часть)\n" \
    f"<b>10 июня (вт)</b> — иностранные языки (устная часть) и информатика\n" \
    f"<b>11 июня (ср)</b> — иностранные языки (устная часть) и информатика\n\n" \
    f"<i>Резервные дни:</i>\n\n" \
    f"<b>16 июня (пн)</b> — география, литература, обществознание, физика\n" \
    f"<b>17 июня (вт)</b> — русский язык\n" \
    f"<b>18 июня (ср)</b> — иностранные языки (английский, испанский, китайский, немецкий, французский) (устная часть), история, химия\n" \
    f"<b>19 июня (чт)</b> — биология, иностранные языки (английский, испанский, китайский, немецкий, французский) (письменная часть), информатика\n" \
    f"<b>20 июня (пт)</b> — ЕГЭ по математике базового уровня, ЕГЭ по математике профильного уровня\n" \
    f"<b>23 июня (пн)</b> — по всем учебным предметам"
    await message.answer(text=text_schedule_ege, parse_mode='HTML', reply_markup=hide)


#Команда /oge
@router.message(Command('oge'))
async def schedule_oge(message: Message):
    await message.delete()
    text_schedule_oge = f"<b>Расписание ОГЭ</b>\n" \
    f"<b>Основной период:</b>\n\n" \
    f"<b>21 мая (ср)</b> — иностранные языки (английский, испанский, немецкий, французский)\n" \
    f"<b>22 мая (чт)</b> — иностранные языки (английский, испанский, немецкий, французский)\n" \
    f"<b>26 мая (пн)</b> — биология, информатика, обществознание, химия\n" \
    f"<b>29 мая (чт)</b> — география, история, физика, химия\n" \
    f"<b>3 июня (вт)</b> — математика\n" \
    f"<b>6 июня (пт)</b> — география, информатика, обществознание\n" \
    f"<b>9 июня (пн)</b> — русский язык\n" \
    f"<b>16 июня (пн)</b> — биология, информатика, литература, физика\n\n" \
    f"<i>Резервные дни</i>\n\n" \
    f"<b>26 июня (чт)</b> — русский язык\n" \
    f"<b>27 июня (пт)</b> — по всем учебным предметам (кроме русского языка и математики)\n" \
    f"<b>28 июня (сб)</b> — по всем учебным предметам (кроме русского языка и математики)\n" \
    f"<b>30 июня (пн)</b> — математика\n" \
    f"<b>1 июля (вт)</b> — по всем учебным предметам\n" \
    f"<b>2 июля (ср)</b> — по всем учебным предметам"
    await message.answer(text=text_schedule_oge, parse_mode='HTML', reply_markup=hide)


@router.message(Command('cancel'))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('<b>Вы отменили все действия!</b>\n\nДля перехода в меню нажмите /menu', parse_mode='HTML')
