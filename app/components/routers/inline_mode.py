import hashlib

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultCachedPhoto, InlineQueryResultArticle, InputTextMessageContent

from app.database.requests import get_image

router_inline_mode = Router()


@router_inline_mode.inline_query()
async def inline_inline_query(query: InlineQuery):
    text = query.query.lower()
    result_id: str = hashlib.md5(text.encode('utf-8')).hexdigest()

    if text in ['понедельник', 'пн']:
        week_name = 'monday'
        file_id = await get_image(week_name)

        result = InlineQueryResultCachedPhoto(
            id=result_id,
            photo_file_id=f"{file_id[0]}",
            title="Расписание на понедельник",
            description="Нажмите, чтобы отправить расписание на понедельник",
            caption="📆 <b>Расписание на понедельник</b>",
            parse_mode='HTML'
        )

        await query.answer(results=[result], cache_time=1, is_personal=True)

    elif text in ['вторник', 'вт']:
        week_name = 'tuesday'
        file_id = await get_image(week_name)

        result = InlineQueryResultCachedPhoto(
            id=result_id,
            photo_file_id=f"{file_id[0]}",
            title="Расписание на вторник",
            description="Нажмите, чтобы отправить расписание на вторник",
            caption="📆 <b>Расписание на вторник</b>",
            parse_mode='HTML'
        )

        await query.answer(results=[result], cache_time=1, is_personal=True)

    elif text in ['среда', 'ср']:
        week_name = 'wednesday'
        file_id = await get_image(week_name)

        result = InlineQueryResultCachedPhoto(
            id=result_id,
            photo_file_id=f"{file_id[0]}",
            title="Расписание на среду",
            description="Нажмите, чтобы отправить расписание на среду",
            caption="📆 <b>Расписание на среду</b>",
            parse_mode='HTML'
        )

        await query.answer(results=[result], cache_time=1, is_personal=True)

    elif text in ['четверг', 'чт']:
        week_name = 'thrusday'
        file_id = await get_image(week_name)

        result = InlineQueryResultCachedPhoto(
            id=result_id,
            photo_file_id=f"{file_id[0]}",
            title="Расписание на четверг",
            description="Нажмите, чтобы отправить расписание на четверг",
            caption="📆 <b>Расписание на четверг</b>",
            parse_mode='HTML'
        )

        await query.answer(results=[result], cache_time=1, is_personal=True)

    elif text in ['пятница', 'пт']:
        week_name = 'friday'
        file_id = await get_image(week_name)

        result = InlineQueryResultCachedPhoto(
            id=result_id,
            photo_file_id=f"{file_id[0]}",
            title="Расписание на пятницу",
            description="Нажмите, чтобы отправить расписание на пятницу",
            caption="📆 <b>Расписание на пятницу</b>",
            parse_mode = 'HTML'
        )

        await query.answer(results=[result], cache_time=1, is_personal=True)

    elif text in ['звонки', 'зв', 'zv']:
        week_name = 'calls'
        file_id = await get_image(week_name)

        result = InlineQueryResultCachedPhoto(
            id=result_id,
            photo_file_id=f"{file_id[0]}",
            title="Расписание звонков",
            description="Нажмите, чтобы отправить расписание звонков",
            caption="🔔 <b>Расписание звонков</b>",
            parse_mode = 'HTML'
        )

        await query.answer(results=[result], cache_time=1, is_personal=True)
    else:
        result = InlineQueryResultArticle(
            id=result_id,
            title='Введите день недели',
            input_message_content=InputTextMessageContent(message_text='❌')
        )
        await query.answer(results=[result], cache_time=1, is_personal=True)
