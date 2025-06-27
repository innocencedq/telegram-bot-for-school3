import aiohttp
import datetime
from typing import List, Dict, Any
from app.database.requests import get_access_token
from app.components.diary.parsing import refresh_token

async def get_info_mark(user, max_retries=2):
    urls = {
        "id": "https://diaryapi.kiasuo.ru/diary/api/user",
        "periods": "https://diaryapi.kiasuo.ru/diary/api/study_periods",
    }

    for attempt in range(max_retries + 1):
        access_token = await get_access_token(user)
        headers = {
            "Accept": "application/json, text/plain, */*",
            "authorization": f"Bearer {access_token}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(urls["id"], headers=headers) as response:
                    if response.status != 200:
                        raise ValueError("wrong user id")
                    data = await response.json()
                    id = data['children'][0]['id']

                async with session.get(urls["periods"], headers=headers, params={"id": id}) as response:
                    if response.status != 200:
                        raise ValueError("wrong periods")
                    data = await response.json()
                    try:
                        period_id = data[3]["id"]
                    except IndexError:
                        period_id = data[1]["id"]

                async with session.get(f"https://diaryapi.kiasuo.ru/diary/api/lesson_marks/{period_id}?id={id}", headers=headers) as response:
                    if response.status != 200:
                        raise ValueError("wrong marks")
                    return await response.json()

        except (ValueError, aiohttp.ClientError) as e:
            if attempt == max_retries:
                raise
            await refresh_token(user)
            continue

    raise RuntimeError("Unexpected error in get_info")


async def get_info_homework(user, max_retries=2):
    urls = {
        "id": "https://diaryapi.kiasuo.ru/diary/api/user",
        "periods": "https://diaryapi.kiasuo.ru/diary/api/study_periods",
    }

    today = datetime.date.today()

    for attempt in range(max_retries + 1):
        access_token = await get_access_token(user)
        headers = {
            "Accept": "application/json, text/plain, */*",
            "authorization": f"Bearer {access_token}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(urls["id"], headers=headers) as response:
                    if response.status != 200:
                        raise ValueError("wrong user id")
                    data = await response.json()
                    id = data['children'][0]['id']

                async with session.get(f"https://diaryapi.kiasuo.ru/diary/api/schedule?id={id}&week={str(int(today.strftime("%U")) + 1)}&year={today.strftime("%Y")}", headers=headers) as response:
                    if response.status != 200:
                        raise ValueError("wrong marks")
                    return await response.json()

        except (ValueError, aiohttp.ClientError) as e:
            if attempt == max_retries:
                raise
            await refresh_token(user)
            continue

    raise RuntimeError("Unexpected error in get_info")


async def get_all_period_marks(user: str) -> Dict[str, Any]:
    data = await get_info_mark(user)

    all_subjects_data = []
    count_good_marks = 0
    subject_number = 1
    
    for lesson in data['lessons']:
        subject_name = lesson['subject']
        marks_all_period = []
        all_marks = []

        for slot in lesson['slots']:
            if 'value' in slot['mark']:
                all_marks.append(slot['mark']['value'])
        
            marks_all_period.append({
                "marks": all_marks
            })

        avg_mark = None
        rounded_mark = None
        avg_status = "Нет данных о среднем балле"

        # Безопасная проверка средних оценок
        if lesson.get('averages', {}).get('for_student'):
            try:
                avg_mark = float(lesson['averages']['for_student'][0])
                
                if avg_mark >= 4.5:
                    avg_status = "(5)"
                    rounded_mark = 5
                    count_good_marks += 1
                elif avg_mark >= 3.5:
                    avg_status = "(4)"
                    rounded_mark = 4
                    count_good_marks += 1
                elif avg_mark >= 2.5:
                    avg_status = "(3)"
                    rounded_mark = 3
                else:
                    avg_status = "(2)"
                    rounded_mark = 2
            except (IndexError, ValueError, TypeError):
                pass

        subject_data = {
            "number": subject_number,
            "subject": subject_name,
            "has_marks": bool(marks_all_period),
            "marks": marks_all_period if marks_all_period else 
                   [{"message": "За эту четверть/полугодие Вы не получили ни одну оценку"}],
            "average_mark": avg_mark,
            "average_status": avg_status,
            "rounded_mark": rounded_mark
        }
        
        all_subjects_data.append(subject_data)
        subject_number += 1

    count_subjects_with_marks = sum(1 for subj in all_subjects_data if subj['has_marks'])

    return {
        "total_subjects": len(data['lessons']),
        "subjects_with_marks": count_subjects_with_marks,
        "good_marks_total": count_good_marks,
        "subjects": all_subjects_data
    }


async def get_marks_last_5_days(user: str) -> Dict[str, Any]:
    data = await get_info_mark(user)
    
    all_subjects_data = []
    count_good_marks = 0
    today = datetime.date.today()
    date_range = [today - datetime.timedelta(days=i) for i in range(5)]
    subject_number = 1

    for lesson in data['lessons']:
        subject_name = lesson['subject']
        marks_last_5_days = []
        
        for day in date_range:
            day_marks = []
            for slot in lesson['slots']:
                slot_date = datetime.datetime.strptime(slot['lesson_date'], "%Y-%m-%d").date()
                if slot_date == day and 'mark' in slot and 'value' in slot['mark']:
                    day_marks.append(slot['mark']['value'])
            
            if day_marks:
                marks_last_5_days.append({
                    "date": day.strftime("%d.%m.%Y"),
                    "marks": day_marks
                })

        avg_mark = None
        rounded_mark = None
        avg_status = "Нет данных о среднем балле"
        
        if lesson['averages']['for_student']:
            avg_mark = float(lesson['averages']['for_student'][0])
            
            if avg_mark >= 4.5:
                avg_status = "(5)"
                rounded_mark = 5
                count_good_marks += 1
            elif avg_mark >= 3.5:
                avg_status = "(4)"
                rounded_mark = 4
                count_good_marks += 1
            elif avg_mark >= 2.5:
                avg_status = "(3)"
                rounded_mark = 3
            else:
                avg_status = "(2)"
                rounded_mark = 2
        
        subject_data = {
            "number": subject_number,
            "subject": subject_name,
            "has_marks_last_5_days": bool(marks_last_5_days),
            "marks": marks_last_5_days if marks_last_5_days else 
                   [{"message": f"За последние 5 дней не было оценок по {subject_name}"}],
            "average_mark": avg_mark,
            "average_status": avg_status,
            "rounded_mark": rounded_mark
        }
        
        all_subjects_data.append(subject_data)
        subject_number += 1

    count_subjects_with_marks = sum(1 for subj in all_subjects_data if subj['has_marks_last_5_days'])

    return {
        "date_from": date_range[-1].strftime("%d.%m.%Y"),
        "date_to": today.strftime("%d.%m.%Y"),
        "total_subjects": len(data['lessons']),
        "subjects_with_marks": count_subjects_with_marks,
        "good_marks_total": count_good_marks,
        "subjects": all_subjects_data
    }


async def get_homework(user: str) -> Dict[str, Any]:
    data = await get_info_homework(user)
    all_homework_data = []
    subject_number = 1

    for subjects in data['schedule']:
        homework_data = []
        subject = subjects['subject']

        if 'created_homework_id' in subjects:
            for homework in data['homeworks']:
                if homework['id'] == subjects['created_homework_id'] or homework['id'] in subjects['homework_to_check_ids']:
                    homework_data.append({
                        "text": homework['text'],
                        "check_at": homework['check_at']
                    })
        
        subject_data = {
            "subject": subject,
            "number": subject_number,
            "homework": homework_data,
            "has_homework": bool(homework_data)
        }

        all_homework_data.append(subject_data)

        subject_number += 1

    return {
        "subjects": all_homework_data
    }
                

        
