from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Chat, InputMediaPhoto
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.formatting import Italic, Bold, Text, Underline, Url, BlockQuote, Spoiler, Code, ExpandableBlockQuote, TextLink, Strikethrough
from sqlalchemy import update

from app.components.routers.callbacks import back_callback
from app.database.data import Images, async_session, Admin
from app.database.requests import count_users, check_admin, advert_write_sql, refresh_last_advert_id, del_image_from_redis, get_all_data_about_advert, update_data_about_advert, \
    deleting_data_about_advert, refresh_last_advert_id, get_image
from app.components.keyboard import admin_panel, adm_back, adm_rasp, next_week, tech_works, confirm_adm, repeat_adm, \
    confirm_schedule, confirm_day, confirm_calls, send_own_message, manual_formatting, advert_manage_kb, advert_confirmed, \
    advert_skip_picture, advert_continue_picture, advert_edit_cancel, advert_editing, advert_continue_edit
from app.components.keyboard import notify as hide
from app.components.notifyprocesses.notify import notify_update, notify_update_schedule, technical_works, technical_works_finish, notify_rework_schedule, message_admin, notify_update_calls, \
    new_advert_notify

#Роутер
router_adm = Router()

#Состояния
class Form(StatesGroup):
    message_adm = State()
    confirm_adm = State()
    waiting_schedule = State()
    waiting_day = State()
    waiting_calls = State()
    waiting_admin = State()
    manual_message_adm = State()


class AdvertManage(StatesGroup):
    title_processing = State()
    description_processing = State()
    image_processing = State()
    title_editing = State()
    description_editing = State()
    image_editing = State()
    title_data = State()
    image_data = State()
    description_data = State()


#Админ панель
@router_adm.message(Command('adminpanel'))
async def adminpanel(message: Message):
    count = await count_users()
    is_admin = await check_admin(message.from_user.id)
    if is_admin:
        await message.answer(f'<b>Админ панель</b>\n\nПользователей в боте: <b>{count}</b>', reply_markup=admin_panel, parse_mode='html')
    else:
        await message.answer('Вы не администратор!')


@router_adm.callback_query(F.data == 'adminpanel')
async def adminpanel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    count = await count_users()
    try:
        await callback.message.edit_text(f'<b>Админ панель</b>\n\nПользователей в боте: <b>{count}</b>', reply_markup=admin_panel, parse_mode='html')
    except Exception:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
        await callback.message.answer(f'<b>Админ панель</b>\n\nПользователей в боте: <b>{count}</b>', reply_markup=admin_panel, parse_mode='html')

#Основной callback
@router_adm.callback_query(F.data.in_(['notify_schedule', 'notify_update', 'next_week_notify', 'day_change', 'tech_works', 'tech_works_start', 'tech_works_finish', 'friday_rasp', 'thursday_rasp', 'wednesday_rasp', 'tuesday_rasp', 'monday_rasp', 'adm_message', 'notify_calls', 'confirm_adm', 'yes_schedule', 'yes_day_change', 'yes_calls_change', 'add_admin']))
async def callback(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'notify_schedule':
        await callback.message.edit_text('<b>Выберите один из вариантов.</b>\n\n1. Обновить расписание на следующую неделю\n2. Обновить расписание на день недели\n3. Обновить расписание звонков', reply_markup=adm_rasp, parse_mode='html')

    elif callback.data == 'next_week_notify':
        await callback.message.edit_text('<b>Обновление расписания на следующую неделю</b>\n\nСначала отправьте расписание на понедельник', reply_markup=adm_back, parse_mode='html')
        await state.set_state(Form.waiting_schedule)

    elif callback.data == 'day_change':
        await callback.message.edit_text('<b>Внесение изменений в текущее расписание</b>\n\nВыберите день недели.', reply_markup=next_week, parse_mode='html')

    elif callback.data == 'tech_works':
        await callback.message.edit_text('<b>Технический перерыв</b>\n\nВыберите один из вариантов', reply_markup=tech_works, parse_mode='html')

    elif callback.data == 'tech_works_start':
        try:
            await callback.message.edit_text('⏳ Подождите, начал оповещать всех...')

            await technical_works()
            await callback.message.edit_text('✅ <b>Оповещение отправлено успешно!</b>', reply_markup=adm_back, parse_mode='html')
        except Exception:
            await callback.message.edit_text('❌ <b>Не получилось доставить оповещение, попробуйте еще раз!</b>', reply_markup=adm_back, parse_mode='html')

    elif callback.data == 'tech_works_finish':
        try:
            await callback.message.edit_text('⏳ Подождите, начал оповещать всех...')

            await technical_works_finish()
            await callback.message.edit_text('✅ <b>Оповещение отправлено успешно!</b>', reply_markup=adm_back, parse_mode='html')
        except Exception:
            await callback.message.edit_text('❌ <b>Не получилось доставить оповещение, попробуйте еще раз!</b>', reply_markup=adm_back, parse_mode='html')

    elif callback.data == 'notify_update':
        try:
            await callback.message.edit_text('⏳ Подождите, начал оповещать всех...')
            
            await notify_update()
            await callback.message.edit_text('✅ <b>Оповещение отправлено успешно!</b>', reply_markup=adm_back, parse_mode='html')
        except Exception:
            await callback.message.edit_text('❌ <b>Не получилось доставить оповещение, попробуйте еще раз!</b>', reply_markup=adm_back, parse_mode='html')

    elif callback.data == 'monday_rasp':
        day = 'monday'

        await callback.message.edit_text(f'Отправьте новое расписание на понедельник', reply_markup=adm_back, parse_mode='html')

        await state.update_data(day=day)
        await state.set_state(Form.waiting_day)

    elif callback.data == 'tuesday_rasp':
        day = 'tuesday'

        await callback.message.edit_text(f'Отправьте новое расписание на вторник', reply_markup=adm_back,
                                         parse_mode='html')

        await state.update_data(day=day)
        await state.set_state(Form.waiting_day)

    elif callback.data == 'wednesday_rasp':
        day = 'wednesday'

        await callback.message.edit_text(f'Отправьте новое расписание на среду', reply_markup=adm_back,
                                         parse_mode='html')

        await state.update_data(day=day)
        await state.set_state(Form.waiting_day)

    elif callback.data == 'thursday_rasp':
        day = 'thursday'

        await callback.message.edit_text(f'Отправьте новое расписание на четверг', reply_markup=adm_back,
                                         parse_mode='html')

        await state.update_data(day=day)
        await state.set_state(Form.waiting_day)

    elif callback.data == 'friday_rasp':
        day = 'friday'

        await callback.message.edit_text(f'Отправьте новое расписание на пятницу', reply_markup=adm_back,
                                         parse_mode='html')

        await state.update_data(day=day)
        await state.set_state(Form.waiting_day)

    elif callback.data == 'adm_message':
        await callback.message.edit_text('<b>Отправка своего уведомления</b>\n\n<b>Бот сам отформатирует текст в зависимости от примененного формата. Не забывайте вместе с текстом форматировать и смайлики! Ручное форматирование используется ЯР HTML</b>\n\n<b>Напишите, о чем хотите сообщить всех</b>', reply_markup=send_own_message, parse_mode='html')
        await state.set_state(Form.message_adm)

    elif callback.data == 'notify_calls':
        await callback.message.edit_text('<b>Обновление расписания звонков</b>\n\nОтправьте новое расписание звонков', reply_markup=adm_back, parse_mode='html')
        await state.set_state(Form.waiting_calls)

    elif callback.data == 'yes_schedule':
        try:
            await callback.message.edit_text('⏳ Подождите, начал оповещать всех...')

            await notify_update_schedule()
            await callback.message.edit_text('✅ <b>Оповещение отправлено успешно!</b>', reply_markup=adm_back, parse_mode='html')
        except Exception:
            await callback.message.edit_text('❌ <b>Не получилось доставить оповещение, попробуйте еще раз!</b>', reply_markup=adm_back, parse_mode='html')

    elif callback.data == 'yes_day_change':
        data = await state.get_data()
        day = data.get('day')

        await callback.message.edit_text('⏳ Подождите, начал оповещать всех...')
        await notify_rework_schedule(message=day)
        await state.clear()

        await callback.message.edit_text('✅ <b>Оповещение отправлено успешно!</b>', reply_markup=adm_back, parse_mode='html')

    elif callback.data == 'yes_calls_change':
        await callback.message.edit_text('⏳ Подождите, начал оповещать всех...')

        await notify_update_calls()
        await callback.message.edit_text('✅ <b>Оповещение отправлено успешно!</b>', reply_markup=adm_back, parse_mode='html')

    elif callback.data == 'add_admin':
        await callback.message.edit_text('Введите chat_id пользователя, чтобы добавить его в администраторы\n\nДля получения chat_id, попросите ввести человека /getmychatid, после чего перешлите его ответ от бота', reply_markup=adm_back, parse_mode='html')
        await state.set_state(Form.waiting_admin)


@router_adm.callback_query(F.data == 'manual_edit')
async def manual_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text('Ручное форматирование HTML\n\n<b>Жирный</b>\n<i>Курсив</i>\n<code>Монохромный</code>\n<s>Перечеркнутый</s>\n<u>Подчеркнутый</u>\n<pre language="c++">Код</pre>\n<a href="smth.ru">Сайт</a>\n\nПодробнее: https://habr.com/ru/sandbox/170069/', reply_markup=manual_formatting)
    await state.set_state(Form.manual_message_adm)


@router_adm.message(Form.manual_message_adm)
async def manual_message_adm(message: Message, state: FSMContext):
    adm_message = message.text
    await state.update_data(adm_message=adm_message)
    await state.set_state(Form.confirm_adm)
    try:
        await message.answer(f'<b>Бот отправит следующее:</b>\n\n{adm_message}\n\n<b>Вы уверены что хотите отправить? (нажмите один раз на кнопку и ждите, бот делает рассылку ~30 секунд)</b>', reply_markup=confirm_adm, parse_mode='HTML')
    except Exception:
        await message.answer('<b>Проверьте текст!</b>', parse_mode='html', reply_markup=hide)


#Подтверждения для рассылки
@router_adm.callback_query(F.data == 'adm_confirm')
async def confirm_admin(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'adm_confirm':
        try:
            data = await state.get_data()
            adm_message = data.get('adm_message')
            await state.clear()
            await callback.message.edit_text('⏳ Подождите, начал оповещать всех...')

            await message_admin(adm_message)
            await callback.message.edit_text('✅ <b>Оповещение отправлено успешно!</b>', reply_markup=adm_back, parse_mode='html')
        except Exception:
            await callback.message.edit_text('❌ <b>Не получилось доставить оповещение, попробуйте еще раз!</b>', reply_markup=adm_back, parse_mode='html')


#Добавление администратора
@router_adm.message(Form.waiting_admin)
async def waiting_admin(message: Message, state: FSMContext):
    async with async_session() as session:
        if await check_admin(int(message.text)):
            await message.answer('Данный пользователь уже является администратором!', reply_markup=adm_back, parse_mode='html')
        else:
            try:
                adm_id = int(message.text)

                from run import bot
                chat: Chat = await bot.get_chat(adm_id)

                new_adm = Admin(
                    tg_id=adm_id,
                    username=chat.username if chat.username else 'unspecified_admin',
                )
                session.add(new_adm)
                await session.commit()

                await state.clear()
                await message.answer('Администратор добавлен!', reply_markup=adm_back)
            except Exception:
                await message.answer('Произошло что-то не так, проверьте chat_id!', reply_markup=adm_back, parse_mode='html')


#Обновление звонков
@router_adm.message(Form.waiting_calls)
async def waiting_calls(message: Message, state: FSMContext):
    async with async_session() as session:
        try:
            file_id = message.photo[0].file_id

            stmt = update(Images).where(Images.image_name == 'calls').values(image_id=file_id)
            await session.execute(stmt)
            await session.commit()

            await state.clear()
            await message.answer('Расписание звонков загружено! Не удаляйте отправленную фотографию! Оповестить всех? (нажмите один раз на кнопку и ждите, бот делает рассылку ~30 секунд)', reply_markup=confirm_calls)
        except Exception:
            await message.answer('Что-то пошло не так')


#Обновление расписания (выборочно)
@router_adm.message(Form.waiting_schedule)
async def waiting_schedule(message: Message, state: FSMContext):
    async with async_session() as session:
        try:
            values = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            file_id = message.photo[0].file_id

            data = await state.get_data()
            current_index = data.get('current_index', 0)

            if current_index < len(values):
                val = values[current_index]
                try:
                    await del_image_from_redis(val)
                    stmt = update(Images).where(Images.image_name == val).values(image_id=file_id)
                    await session.execute(stmt)
                    await session.commit()

                    current_index = current_index + 1
                    await state.update_data(current_index=current_index)

                    if current_index < len(values):
                        await message.answer(f'Расписание на {"понедельник" if val == "monday" else ""}{"вторник" if val == "tuesday" else ""}{"среду" if val == "wednesday" else ""}{"четверг" if val == "thursday" else ""}{"пятницу" if val == "friday" else ""} загружено! Теперь отправьте на {"вторник" if val == "monday" else ""}{"среду" if val == "tuesday" else ""}{"четверг" if val == "wednesday" else ""}{"пятницу" if val == "thursday" else ""}')
                    else:
                        await state.clear()
                        await message.answer('Расписание обновлено! Не удаляйте отправленные фотографии! Оповестить всех? (нажмите один раз на кнопку и ждите, бот делает рассылку ~30 секунд)', reply_markup=confirm_schedule)
                except Exception:
                        await message.answer('Отправьте фотографию еще раз')
        except Exception:
            await message.answer('Что-то пошло не так... Перезайдите в админ панель и попробуйте снова - /adminpanel')

#Обновление расписания
@router_adm.message(Form.waiting_day)
async def waiting_day(message: Message, state: FSMContext):
    async with async_session() as session:
        try:
            days = {"monday": "понедельник", "tuesday": "вторник", "wednesday": "среду", "thursday": "четверг", "friday": "пятницу"}
            data = await state.get_data()
            day = data.get('day')
            file_id = message.photo[0].file_id

            stmt = update(Images).where(Images.image_name == day).values(image_id=file_id)
            await session.execute(stmt)
            await session.commit()

            await message.answer(f'Расписание на {days[day]} загружено! Не удаляйте отправленную фотографию! Оповестить всех? (нажмите один раз на кнопку и ждите, бот делает рассылку ~30 секунд)', reply_markup=confirm_day)
        except Exception:
            await message.answer('Что-то пошло не так... Перезайдите в админ панель и попробуйте снова - /adminpanel')


#Логика рассылки
@router_adm.message(Form.message_adm)
async def message_adm(message: Message, state: FSMContext):
    text = message.text
    ents = sorted(message.entities or [], key=lambda x: (x.offset, -x.length))

    formatted_text = Text()

    last_offset = 0
    i = 0
    while i < len(ents):
        ent = ents[i]

        if ent.offset > last_offset:
            formatted_text += text[last_offset:ent.offset]

        ent_text = text[ent.offset:ent.offset + ent.length]

        entities_in_group = [ent]
        j = i + 1
        while j < len(ents):
            next_ent = ents[j]
            if (next_ent.offset < ent.offset + ent.length and
                    next_ent.offset + next_ent.length > ent.offset):
                entities_in_group.append(next_ent)
                j += 1
            else:
                break

        formatting_order = [
            'bold', 'italic', 'underline', 'strikethrough',
            'code', 'text_link', 'spoiler', 'blockquote'
        ]

        formatted_ent_text = ent_text
        for fmt in formatting_order:
            if any(e.type == fmt for e in entities_in_group):
                if fmt == "text_link":
                    text_link_ent = next(e for e in entities_in_group if e.type == "text_link")
                    formatted_ent_text = TextLink(formatted_ent_text, url=text_link_ent.url)
                elif fmt == "bold":
                    formatted_ent_text = Bold(formatted_ent_text)
                elif fmt == "italic":
                    formatted_ent_text = Italic(formatted_ent_text)
                elif fmt == "underline":
                    formatted_ent_text = Underline(formatted_ent_text)
                elif fmt == "strikethrough":
                    formatted_ent_text = Strikethrough(formatted_ent_text)
                elif fmt == "code":
                    formatted_ent_text = Code(formatted_ent_text)
                elif fmt == "spoiler":
                    formatted_ent_text = Spoiler(formatted_ent_text)
                elif fmt == "blockquote":
                    formatted_ent_text = BlockQuote(formatted_ent_text)

        formatted_text += formatted_ent_text

        max_end = max(e.offset + e.length for e in entities_in_group)
        last_offset = max_end

        i = j

    if last_offset < len(text):
        formatted_text += text[last_offset:]
    adm_message = formatted_text.as_html()
    await state.update_data(adm_message=adm_message)
    await state.set_state(Form.confirm_adm)
    try:
        await message.answer(f'<b>Бот отправит следующее:</b>\n\n{adm_message}\n\n<b>Вы уверены что хотите отправить? (нажмите один раз на кнопку и ждите, бот делает рассылку ~30 секунд)</b>', reply_markup=confirm_adm, parse_mode='HTML')
    except Exception:
        await message.answer('<b>Произошла непредвиденная ошибка... Перезайдите в админ панель и попробуйте снова - /adminpanel</b>', parse_mode='html', reply_markup=repeat_adm)


#Вспомогательная функция к расписаниям
async def message_rasp(message_pass):
    await notify_rework_schedule(message=message_pass)


@router_adm.callback_query(F.data.in_(['advert_manage', 'advert_create', 'advert_edit']))
async def advert_manage(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'advert_manage':
        await callback.message.edit_text('Управление объявлениями', reply_markup=advert_manage_kb)

    elif callback.data == 'advert_create':
        global on_editing
        on_editing = False
        await callback.message.edit_text('Создание объявления\n\nДля начала введите заголовок.\n\n<b>Заголовок не должен превышать 30-ти символов!!!</b>', parse_mode='html')
        await state.set_state(AdvertManage.title_processing)


@router_adm.message(AdvertManage.title_processing)
async def title_process(message: Message, state: FSMContext):
    try:
        if len(str(message.text)) > 30:
            await message.answer(f'Вы превысили допустимое количество символов в тексте, пожалуйста сократите его\n\nТекущее количество символов: {len(str(message.text))}')
            await state.set_state(AdvertManage.title_processing)
        else:
            await state.update_data({'advert_title': str(message.text)})

            await message.answer('Теперь введите описание\n\n<b>Описание не должно превышать 650-ти символов!!!</b>', parse_mode='html')
            await state.set_state(AdvertManage.description_processing)
    except Exception:
        await message.answer('Вы отправили явно не текст... Попробуйте еще раз')
        await state.set_state(AdvertManage.title_processing)


@router_adm.message(AdvertManage.description_processing)
async def desc_process(message: Message, state: FSMContext):
    try:
        if len(str(message.text)) > 650:
            await message.answer(f'Вы превысили допустимое количество символов в тексте, пожалуйста сократите его\n\nТекущее количество символов: {len(str(message.text))}')
            await state.set_state(AdvertManage.description_processing)
        else:
            await state.update_data({'advert_desc': str(message.text)})

            photo = await get_image('advert_default_image')
            await message.answer_photo(photo=photo,
                                    caption='Вы можете загрузить свое изображение/видео или пропустить этот шаг. По умолчанию будет загружено изображение, которое прикреплено к сообщению', 
                                    reply_markup=advert_skip_picture)
            await state.set_state(AdvertManage.image_processing)
    except Exception:
        await message.answer('Вы отправили явно не текст... Попробуйте еще раз')
        await state.set_state(AdvertManage.description_processing)
    


@router_adm.message(AdvertManage.image_processing)
async def image_process(message: Message, state: FSMContext):
    try:
        try:
            await state.update_data({'advert_image': message.photo[-1].file_id})
        except TypeError:
            await state.update_data({'advert_image': message.video.file_id})
        await message.answer_photo(photo=message.photo[-1].file_id, caption='Вы отправили это изображение/видео\n\nВы можете изменить его, отправив другое изоброжение/видео в чат\n\nДля продолжения нажмите на кнопку',
                                   reply_markup=advert_continue_picture)
    except TelegramBadRequest:
        await message.answer('Что-то пошло не так, отправьте изображение еще раз')
    
    await state.set_state(AdvertManage.image_processing)


@router_adm.callback_query(F.data.in_(['advert_next', 'advert_skip', 'advert_confirm', 'advert_edit_title', 'advert_edit_description', 'advert_edit_image', 'advert_cancel', 'advert_edit_cancel']))
async def advert_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    advert_title = data.get('advert_title')
    advert_desc = data.get('advert_desc')
    advert_image = data.get('advert_image', None)

    if callback.data == 'advert_next' or callback.data == 'advert_edit_cancel':
        await callback.answer('Переходим к объявлению...')
        await state.set_state(state=None)

        if advert_image:
            photo = InputMediaPhoto(media=advert_image,
                                    caption=f'Ваше объявление:\n\n<b>{advert_title}</b>\n\n{advert_desc}\n\nПодтвердите или измените',
                                    parse_mode='HTML')
            await callback.message.edit_media(media=photo, reply_markup=advert_confirmed)
        else:
            await callback.message.answer(f'Ваше объявление:\n\n<b>{advert_title}</b>\n\n{advert_desc}\n\nПодтвердите или измените',
                              reply_markup=advert_confirmed,
                              parse_mode='HTML')

    elif callback.data == 'advert_skip':
        photo = await get_image('advert_default_image')
        await callback.message.delete()
        await callback.answer('Пропускаю шаг...')
        await state.set_state(state=None)
        await callback.message.answer_photo(photo=photo,
                                            caption=f'Ваше объявление:\n\n<b>{advert_title}</b>\n\n{advert_desc}\n\nПодтвердите или измените',
                                            reply_markup=advert_confirmed,
                                            parse_mode='HTML')
        await state.update_data({"advert_image": callback.message.photo[-1].file_id})

    elif callback.data == 'advert_confirm':
        await callback.message.delete()
        await callback.message.answer('Загружаю...')
        await advert_write_sql(advert_title=advert_title, advert_description=advert_desc, advert_image_id=advert_image if advert_image else None)
        await refresh_last_advert_id()
        await callback.message.answer('Объявление загружено! Начинаю рассылку...')
        await new_advert_notify(advert_title)
        await callback.message.answer('Рассылка завершена успешно!', reply_markup=adm_back)
        await state.clear()

    elif callback.data == 'advert_cancel':
        await callback.message.delete()
        await state.clear()
        await callback.message.answer('Создание отменено!', reply_markup=adm_back)

    elif callback.data == 'advert_edit_title':
        await callback.answer('Перехожу в редактирование...')
        await callback.message.answer('Введите новый заголовок\n\n<b>Заголовок не должен превышать 30-ти символов!!!</b>', parse_mode='html', reply_markup=advert_edit_cancel)
        await state.set_state(AdvertManage.title_editing)

    elif callback.data == 'advert_edit_description':
        await callback.answer('Перехожу в редактирование...')
        await callback.message.answer('Введите новое описание\n\n<b>Описание не должено превышать 650-ти символов!!!</b>', parse_mode='html', reply_markup=advert_edit_cancel)
        await state.set_state(AdvertManage.description_editing)

    elif callback.data == 'advert_edit_image':
        await callback.answer('Перехожу в редактирование...')
        await callback.message.answer('Отправьте новое изображение/видео', reply_markup=advert_edit_cancel)
        await state.set_state(AdvertManage.image_editing)


@router_adm.message(AdvertManage.title_editing)
async def advert_title_edit(message: Message, state: FSMContext):
    try:
        if len(str(message.text)) > 30:
            await message.answer(f'Вы превысили допустимое количество символов в тексте, пожалуйста сократите его\n\nТекущее количество символов: {len(str(message.text))}')
        else:
            await state.update_data({'advert_title': str(message.text)})
            await message.answer(f'Вот ваш новый заголовок\n\n{message.text}\n\nНапишите другой, если хотите еще раз изменить',
                            reply_markup=advert_continue_picture if not on_editing else await advert_continue_edit(advert_id=curr_id_advert))
    except TelegramBadRequest:
        await message.answer('Вы отправили явно не текст... Попробуйте еще раз')
    await state.set_state(AdvertManage.title_editing)


@router_adm.message(AdvertManage.description_editing)
async def advert_title_edit(message: Message, state: FSMContext):
    try:
        if len(str(message.text)) > 650:
            await message.answer(f'Вы превысили допустимое количество символов в тексте, пожалуйста сократите его\n\nТекущее количество символов: {len(str(message.text))}')
        else:
            await state.update_data({'advert_desc': str(message.text)})
            await message.answer(f'Вот ваше новое описание\n\n{message.text}\n\nНапишите другое, если хотите еще раз изменить',
                                reply_markup=advert_continue_picture if not on_editing else await advert_continue_edit(advert_id=curr_id_advert))
    except TelegramBadRequest:
        await message.answer('Вы отправили явно не текст... Попробуйте еще раз')
    await state.set_state(AdvertManage.description_editing)


@router_adm.message(AdvertManage.image_editing)
async def advert_title_edit(message: Message, state: FSMContext):
    try:
        try:
            await state.update_data({'advert_image': message.photo[-1].file_id})
        except TypeError:
            await state.update_data({'advert_image': message.video.file_id})
        await message.answer_photo(photo=message.photo[-1].file_id, caption=f'Вот ваше новое изображение\n\nПришлите другое, если хотите еще раз изменить',
                                   reply_markup=advert_continue_picture if not on_editing else await advert_continue_edit(advert_id=curr_id_advert))
    except TelegramBadRequest:
        await message.answer('Что-то пошло не так, попробуйте отправить изображение еще раз')

    await state.set_state(AdvertManage.image_editing)


@router_adm.callback_query(F.data.startswith('edit_advert-'))
async def editing_advert(callback: CallbackQuery, state: FSMContext):
    global curr_id_advert, on_editing
    curr_id_advert = callback.data.split('-')[1]
    on_editing = True
    await state.set_state(None)
    try:
        canceled = callback.data.split('-')[2]
    except Exception:
        canceled = None

    if canceled:
        await state.set_state(state=None)

    data = await get_all_data_about_advert(curr_id_advert)
    data_from_state = await state.get_data()

    id = data.get("id")
    title = data.get("title") if not data_from_state.get("advert_title", None) else data_from_state.get("advert_title")
    desc = data.get("description") if not data_from_state.get("advert_desc", None) else data_from_state.get("advert_desc")
    image = data.get("image_id", None) if not data_from_state.get("advert_image", None) else data_from_state.get("advert_image")

    await state.update_data({
        "advert_title": title,
        "advert_desc": desc,
        "advert_image": image
    })

    await callback.answer('Перехожу в редактирование...')
    await callback.message.answer_photo(photo=str(image), 
                                        caption=f'Редактирование объявления:\n\n'
                                        f'<b>{title}</b>\n\n'
                                        f'{desc}', reply_markup=await advert_editing(curr_id_advert), parse_mode='HTML')
    

@router_adm.callback_query(F.data.startswith('advert_editing_confirm-'))
async def advert_edit_confirm(callback: CallbackQuery, state: FSMContext):
    global curr_id_advert
    curr_id_advert = None
    id = callback.data.split('-')[1]
    data = await state.get_data()
    advert_title = data.get('advert_title')
    advert_desc = data.get('advert_desc')
    advert_image = data.get('advert_image', None)

    await update_data_about_advert(id, advert_title, advert_desc, advert_image)
    await state.clear()
    await callback.answer("Объявление изменено!")

    await back_callback(callback, state)


@router_adm.callback_query(F.data.startswith('delete_advert-'))
async def deleting_advert(callback: CallbackQuery, state: FSMContext):
    id = callback.data.split('-')[1]
    await callback.message.delete()
    await callback.message.answer("Приступаю к удалению...")
    await deleting_data_about_advert(id)
    await refresh_last_advert_id()
    await callback.message.answer('Объявление успешно удалено!', parse_mode='HTML')
    await back_callback(callback=callback, state=state, where="yes_quick_menu")

