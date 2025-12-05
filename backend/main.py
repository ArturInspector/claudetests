from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, SessionLocal
import crud
from parser import parse_markdown_content
from task_parser import parse_task_markdown
from compiler import get_compiler

init_db()

app = FastAPI(title="Interview Practice Platform", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

class AnswerSubmit(BaseModel):
    question_id: int
    user_answer: str
    session_id: Optional[int] = None
    time_spent: Optional[int] = None  # Секунды
    showed_answer: bool = False
    confidence_level: Optional[int] = None  # 1-5

class SessionEnd(BaseModel):
    session_id: int

class ResourceCreate(BaseModel):
    question_id: int
    type: str  # article, video, code, tool, docs
    title: str
    url: str
    description: Optional[str] = None

class NoteSave(BaseModel):
    question_id: int
    note_text: str

class ReviewUpdate(BaseModel):
    question_id: int
    confidence_level: int  # 1-5
    time_spent: Optional[int] = None

class TaskSubmissionRequest(BaseModel):
    task_id: int
    user_code: Optional[str] = None  # Для Write задач
    review_answers: Optional[Dict] = None  # Для Review задач: {"question1": "answer1", ...}
    found_issues: Optional[List[str]] = None  # Для Review задач: список найденных проблем
    improved_code: Optional[str] = None  # Для Review задач: улучшенный код
    time_spent: Optional[int] = None  # В секундах

class TopicResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    question_count: int


class QuestionResponse(BaseModel):
    id: int
    title: str
    difficulty: str
    question_type: str
    question_text: str
    topic_name: str


class QuestionWithAnswer(BaseModel):
    id: int
    title: str
    difficulty: str
    question_type: str
    question_text: str
    answer_text: str
    topic_name: str


# ==================== HTML PAGES ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    topics = crud.get_all_topics(db)
    topics_data = []
    
    for topic in topics:
        question_count = len(topic.questions)
        topics_data.append({
            "id": topic.id,
            "name": topic.name,
            "question_count": question_count
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "topics": topics_data
    })


@app.get("/practice", response_class=HTMLResponse)
async def practice_page(request: Request):
    """Страница практики (вопросы)"""
    return templates.TemplateResponse("practice.html", {"request": request})

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """Страница задач"""
    return templates.TemplateResponse("tasks.html", {"request": request})


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Страница статистики"""
    return templates.TemplateResponse("stats.html", {"request": request})


@app.get("/review", response_class=HTMLResponse)
async def review_page(request: Request):
    """Страница повторения (spaced repetition)"""
    return templates.TemplateResponse("review.html", {"request": request})

@app.post("/api/import")
async def import_questions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Импорт вопросов из .md файла"""
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Только .md файлы поддерживаются")
    
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Парсим содержимое
        parsed_data = parse_markdown_content(content_str)
        
        # Получаем или создаем тему
        topic = crud.get_or_create_topic(db, parsed_data['topic'])
        
        # Удаляем старые вопросы по теме (если нужен переимпорт)
        # crud.delete_questions_by_topic(db, topic.id)
        
        # Добавляем новые вопросы
        questions_added = 0
        question_ids = {}  # Mapping для parent_concept_id
        
        for idx, q_data in enumerate(parsed_data['questions']):
            # Обрабатываем parent_concept_id (временный ID → реальный ID)
            parent_id = None
            if q_data.get('parent_concept_id') is not None:
                parent_id = question_ids.get(q_data['parent_concept_id'])
            
            question = crud.create_question(
                db=db,
                topic_id=topic.id,
                title=q_data['title'],
                difficulty=q_data['difficulty'],
                question_type=q_data['question_type'],
                question_text=q_data['question_text'],
                answer_text=q_data['answer_text'],
                level=q_data.get('level', 1),
                parent_concept_id=parent_id,
                tags=q_data.get('tags'),
                estimated_time=q_data.get('estimated_time')
            )
            
            question_ids[idx] = question.id
            questions_added += 1
            
            # Добавляем ресурсы для вопроса
            if parsed_data.get('resources'):
                for res in parsed_data['resources']:
                    if res.get('concept_name') in q_data['title']:
                        crud.create_resource(
                            db=db,
                            question_id=question.id,
                            type=res['type'],
                            title=res['title'],
                            url=res['url'],
                            description=None
                        )
        
        return {
            "success": True,
            "topic": parsed_data['topic'],
            "questions_added": questions_added,
            "resources_added": len(parsed_data.get('resources', []))
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")


@app.get("/api/topics")
async def get_topics(db: Session = Depends(get_db)):
    """Получить список всех тем"""
    topics = crud.get_all_topics(db)
    result = []
    
    for topic in topics:
        result.append({
            "id": topic.id,
            "name": topic.name,
            "description": topic.description,
            "question_count": len(topic.questions)
        })
    
    return result


@app.get("/api/question/{topic_id}")
async def get_question(
    topic_id: int,
    difficulty: Optional[str] = None,
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Получить случайный вопрос по теме"""
    # Получаем список уже отвеченных вопросов в сессии
    exclude_ids = []
    if session_id:
        exclude_ids = crud.get_answered_questions_in_session(db, session_id)
    
    question = crud.get_random_question(db, topic_id, difficulty, exclude_ids)
    
    if not question:
        raise HTTPException(status_code=404, detail="Вопросы не найдены или все вопросы пройдены")
    
    return {
        "id": question.id,
        "title": question.title,
        "difficulty": question.difficulty,
        "question_type": question.question_type,
        "question_text": question.question_text,
        "topic_name": question.topic.name
    }


@app.get("/api/question/{question_id}/answer")
async def get_question_with_answer(question_id: int, db: Session = Depends(get_db)):
    """Получить вопрос с ответом (для показа правильного ответа)"""
    question = crud.get_question_by_id(db, question_id)
    
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")
    
    return {
        "id": question.id,
        "title": question.title,
        "difficulty": question.difficulty,
        "question_type": question.question_type,
        "question_text": question.question_text,
        "answer_text": question.answer_text,
        "topic_name": question.topic.name
    }


@app.post("/api/answer")
async def submit_answer(answer_data: AnswerSubmit, db: Session = Depends(get_db)):
    """Сохранить ответ пользователя с расширенными полями"""
    try:
        answer = crud.save_user_answer(
            db=db,
            question_id=answer_data.question_id,
            user_answer=answer_data.user_answer,
            session_id=answer_data.session_id,
            time_spent=answer_data.time_spent,
            showed_answer=answer_data.showed_answer,
            confidence_level=answer_data.confidence_level
        )
        
        return {
            "success": True,
            "answer_id": answer.id,
            "next_review_date": answer.next_review_date.isoformat() if answer.next_review_date else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения ответа: {str(e)}")


@app.post("/api/session/start")
async def start_session(db: Session = Depends(get_db)):
    """Начать новую сессию практики"""
    session = crud.create_session(db)
    return {
        "session_id": session.id,
        "started_at": session.started_at.isoformat()
    }


@app.post("/api/session/end")
async def end_session(session_data: SessionEnd, db: Session = Depends(get_db)):
    """Завершить сессию и получить summary"""
    session = crud.get_session_by_id(db, session_data.session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    # Получаем ответы из сессии для создания summary
    answers = db.query(crud.UserAnswer).filter(
        crud.UserAnswer.session_id == session_data.session_id
    ).all()
    
    # Группируем по темам
    topics_dict = {}
    for answer in answers:
        question = crud.get_question_by_id(db, answer.question_id)
        topic_name = question.topic.name
        
        if topic_name not in topics_dict:
            topics_dict[topic_name] = []
        
        topics_dict[topic_name].append({
            "title": question.title,
            "difficulty": question.difficulty
        })
    
    # Создаем summary
    summary_lines = []
    summary_lines.append(f"=== СЕССИЯ ПРАКТИКИ ===")
    summary_lines.append(f"Дата: {session.started_at.strftime('%Y-%m-%d %H:%M')}")
    summary_lines.append(f"")
    summary_lines.append(f"Всего вопросов: {len(answers)}")
    summary_lines.append(f"")
    
    for topic_name, questions in topics_dict.items():
        summary_lines.append(f"Тема: {topic_name}")
        summary_lines.append(f"  Вопросов: {len(questions)}")
        
        # Группируем по сложности
        by_difficulty = {}
        for q in questions:
            diff = q['difficulty']
            by_difficulty[diff] = by_difficulty.get(diff, 0) + 1
        
        for diff, count in by_difficulty.items():
            summary_lines.append(f"  - {diff}: {count}")
        summary_lines.append("")
    
    summary_text = "\n".join(summary_lines)
    
    # Сохраняем summary в сессию
    session = crud.end_session(db, session_data.session_id, summary_text)
    
    return {
        "session_id": session.id,
        "started_at": session.started_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "questions_count": session.questions_count,
        "duration_minutes": session.duration_minutes,
        "summary": summary_text
    }


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Получить статистику"""
    return crud.get_statistics(db)


@app.get("/api/sessions/recent")
async def get_recent_sessions(limit: int = 10, db: Session = Depends(get_db)):
    """Получить последние сессии"""
    sessions = crud.get_recent_sessions(db, limit)
    
    result = []
    for session in sessions:
        result.append({
            "id": session.id,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "questions_count": session.questions_count,
            "duration_minutes": session.duration_minutes
        })
    
    return result


# ==================== REVIEW / SPACED REPETITION ====================

@app.get("/api/review/queue")
async def get_review_queue(limit: int = 20, db: Session = Depends(get_db)):
    """Получить вопросы на повторение"""
    questions = crud.get_questions_for_review(db, limit)
    
    result = []
    for q in questions:
        result.append({
            "id": q.id,
            "title": q.title,
            "difficulty": q.difficulty,
            "level": q.level,
            "topic_name": q.topic.name
        })
    
    return result


@app.post("/api/review/update")
async def update_review(review_data: ReviewUpdate, db: Session = Depends(get_db)):
    """Обновить статус повторения вопроса"""
    try:
        answer = crud.update_review_status(
            db=db,
            question_id=review_data.question_id,
            confidence_level=review_data.confidence_level,
            time_spent=review_data.time_spent
        )
        
        return {
            "success": True,
            "next_review_date": answer.next_review_date.isoformat() if answer.next_review_date else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления review: {str(e)}")


@app.get("/api/review/stats")
async def get_review_stats(db: Session = Depends(get_db)):
    """Получить статистику по повторениям"""
    return crud.get_review_stats(db)


# ==================== RESOURCES ====================

@app.post("/api/resources")
async def create_resource(resource: ResourceCreate, db: Session = Depends(get_db)):
    """Создать ресурс для вопроса"""
    try:
        res = crud.create_resource(
            db=db,
            question_id=resource.question_id,
            type=resource.type,
            title=resource.title,
            url=resource.url,
            description=resource.description
        )
        
        return {
            "success": True,
            "resource_id": res.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания ресурса: {str(e)}")


@app.get("/api/resources/{question_id}")
async def get_resources(question_id: int, db: Session = Depends(get_db)):
    """Получить ресурсы для вопроса"""
    resources = crud.get_resources_by_question(db, question_id)
    
    result = []
    for r in resources:
        result.append({
            "id": r.id,
            "type": r.type,
            "title": r.title,
            "url": r.url,
            "description": r.description,
            "quality_score": r.quality_score
        })
    
    return result


# ==================== NOTES ====================

@app.post("/api/notes")
async def save_note(note_data: NoteSave, db: Session = Depends(get_db)):
    """Сохранить или обновить заметку"""
    try:
        note = crud.save_or_update_note(
            db=db,
            question_id=note_data.question_id,
            note_text=note_data.note_text
        )
        
        return {
            "success": True,
            "note_id": note.id,
            "updated_at": note.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения заметки: {str(e)}")


@app.get("/api/notes/{question_id}")
async def get_note(question_id: int, db: Session = Depends(get_db)):
    """Получить заметку по вопросу"""
    note = crud.get_note_by_question(db, question_id)
    
    if note:
        return {
            "id": note.id,
            "question_id": note.question_id,
            "note_text": note.note_text,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat()
        }
    else:
        return {"note_text": ""}


@app.delete("/api/notes/{question_id}")
async def delete_note(question_id: int, db: Session = Depends(get_db)):
    """Удалить заметку"""
    success = crud.delete_note(db, question_id)
    
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=404, detail="Заметка не найдена")


# ==================== RELATED QUESTIONS ====================

@app.get("/api/questions/{question_id}/related")
async def get_related(question_id: int, db: Session = Depends(get_db)):
    """Получить связанные вопросы"""
    related = crud.get_related_questions(db, question_id)
    
    result = {}
    for rel_type, questions in related.items():
        result[rel_type] = []
        for q in questions:
            result[rel_type].append({
                "id": q.id,
                "title": q.title,
                "difficulty": q.difficulty,
                "level": q.level
            })
    
    return result


@app.get("/api/questions/level/{topic_id}/{level}")
async def get_by_level(topic_id: int, level: int, db: Session = Depends(get_db)):
    """Получить вопросы определенного уровня"""
    questions = crud.get_questions_by_level(db, topic_id, level)
    
    result = []
    for q in questions:
        result.append({
            "id": q.id,
            "title": q.title,
            "difficulty": q.difficulty,
            "level": q.level,
            "tags": q.tags
        })
    
    return result


@app.get("/api/questions/{question_id}/children")
async def get_children(question_id: int, db: Session = Depends(get_db)):
    """Получить подвопросы концепта (для progressive disclosure)"""
    children = crud.get_concept_children(db, question_id)
    
    result = []
    for q in children:
        result.append({
            "id": q.id,
            "title": q.title,
            "level": q.level,
            "difficulty": q.difficulty
        })
    
    return result


# ==================== TASKS ====================

@app.post("/api/tasks/import")
async def import_tasks(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Импорт задач из .md файла"""
    if not file.filename.endswith('.md'):
        raise HTTPException(status_code=400, detail="Только .md файлы поддерживаются")
    
    try:
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Парсим содержимое
        parsed_data = parse_task_markdown(content_str)
        
        # Получаем или создаем тему
        topic = crud.get_or_create_topic(db, parsed_data['topic'])
        
        # Добавляем задачи
        tasks_added = 0
        for task_data in parsed_data['tasks']:
            task = crud.create_task(
                db=db,
                topic_id=topic.id,
                title=task_data['title'],
                description=task_data['description'],
                task_type=task_data.get('task_type', 'write'),
                block=task_data.get('block'),
                starter_code=task_data.get('starter_code'),
                test_code=task_data.get('test_code'),
                solution_code=task_data.get('solution_code'),
                ai_code=task_data.get('ai_code'),
                review_questions=task_data.get('review_questions'),
                expected_issues=task_data.get('expected_issues'),
                difficulty=task_data['difficulty'],
                language=task_data['language'],
                estimated_time=task_data.get('estimated_time'),
                hints=task_data.get('hints'),
                requirements=task_data.get('requirements'),
                tags=task_data.get('tags'),
                order=task_data.get('order', 0)
            )
            tasks_added += 1
        
        return {
            "success": True,
            "topic": parsed_data['topic'],
            "tasks_added": tasks_added
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка импорта: {str(e)}")


@app.get("/api/tasks")
async def get_tasks(
    topic_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    language: Optional[str] = None,
    task_type: Optional[str] = None,
    block: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить список задач с фильтрами"""
    if topic_id:
        tasks = crud.get_tasks_by_topic(db, topic_id, difficulty, language)
    else:
        # Если topic_id не указан, возвращаем все задачи
        from database import Task
        query = db.query(Task)
        if difficulty:
            query = query.filter(Task.difficulty == difficulty)
        if language:
            query = query.filter(Task.language == language)
        if task_type:
            query = query.filter(Task.task_type == task_type)
        if block:
            query = query.filter(Task.block == block)
        tasks = query.order_by(Task.order, Task.id).all()
    
    result = []
    for task in tasks:
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "block": task.block,
            "difficulty": task.difficulty,
            "language": task.language,
            "estimated_time": task.estimated_time,
            "order": task.order,
            "tags": task.tags,
            "topic_id": task.topic_id,
            "topic_name": task.topic.name if task.topic else None
        })
    
    return result


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Получить задачу по ID (без решения)"""
    task = crud.get_task_by_id(db, task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Получаем статистику попыток
    submissions = crud.get_task_submissions(db, task_id, limit=1)
    attempts = submissions[0].attempts if submissions else 0
    
    result = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "block": task.block,
        "difficulty": task.difficulty,
        "language": task.language,
        "estimated_time": task.estimated_time,
        "requirements": task.requirements,
        "tags": task.tags,
        "order": task.order,
        "topic_name": task.topic.name if task.topic else None,
        "previous_attempts": attempts
    }
    
    # Возвращаем поля в зависимости от типа задачи
    if task.task_type == "review":
        result.update({
            "ai_code": task.ai_code,
            "review_questions": task.review_questions,
            "expected_issues": None  # Не показываем ожидаемые проблемы
        })
    else:
        result.update({
            "starter_code": task.starter_code,
            "test_code": task.test_code,
            "hints": task.hints
        })
    
    return result


@app.post("/api/tasks/{task_id}/submit")
async def submit_task_solution(
    task_id: int,
    submission_data: TaskSubmissionRequest,
    db: Session = Depends(get_db)
):
    """Отправить решение задачи и проверить через компилятор"""
    task = crud.get_task_by_id(db, task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    
    # Обработка в зависимости от типа задачи
    if task.task_type == "review":
        # Review задачи - проверяем ответы на вопросы
        return await _submit_review_task(task, submission_data, db)
    else:
        # Write задачи - компилируем код
        return await _submit_write_task(task, submission_data, db)


async def _submit_write_task(task, submission_data: TaskSubmissionRequest, db: Session):
    """Обработка Write задач"""
    if not submission_data.user_code:
        raise HTTPException(status_code=400, detail="user_code обязателен для Write задач")
    
    # Получаем компилятор
    compiler = get_compiler()
    
    # Компилируем код в зависимости от языка
    if task.language == "go":
        result = compiler.compile_go(
            submission_data.user_code,
            task.test_code
        )
    elif task.language == "solidity":
        result = compiler.compile_solidity(submission_data.user_code)
    else:
        raise HTTPException(status_code=400, detail=f"Язык {task.language} не поддерживается")
    
    # Определяем прошло ли решение
    passed = False
    if task.language == "go":
        passed = result.get("success", False) and (
            result.get("test_results", {}).get("passed", False) if task.test_code else result.get("compiled", False)
        )
    elif task.language == "solidity":
        passed = result.get("compiled", False)
    
    # Сохраняем отправку
    submission = crud.create_task_submission(
        db=db,
        task_id=task.id,
        user_code=submission_data.user_code,
        compilation_result=result,
        test_results=result.get("test_results"),
        passed=passed,
        time_spent=submission_data.time_spent
    )
    
    # Формируем ответ с подсказками если не прошло
    response = {
        "success": passed,
        "submission_id": submission.id,
        "compilation": {
            "compiled": result.get("compiled", False),
            "errors": result.get("errors", []),
            "output": result.get("output", "")
        },
        "test_results": result.get("test_results"),
        "attempts": submission.attempts
    }
    
    # Добавляем подсказки если не прошло и есть попытки
    if not passed and submission.attempts >= 2 and task.hints:
        response["hints"] = task.hints[:submission.attempts - 1]
    
    return response


async def _submit_review_task(task, submission_data: TaskSubmissionRequest, db: Session):
    """Обработка Review задач"""
    if not submission_data.review_answers and not submission_data.found_issues:
        raise HTTPException(status_code=400, detail="review_answers или found_issues обязательны для Review задач")
    
    # Простая проверка: сравниваем найденные проблемы с ожидаемыми
    # В реальности можно использовать ИИ для проверки качества ответов
    found_issues = submission_data.found_issues or []
    expected_issues = task.expected_issues or []
    
    # Подсчитываем совпадения
    matched_issues = set(found_issues) & set(expected_issues)
    score = len(matched_issues) / len(expected_issues) if expected_issues else 0
    passed = score >= 0.6  # Прошли если нашли 60%+ проблем
    
    # Сохраняем отправку
    submission = crud.create_task_submission(
        db=db,
        task_id=task.id,
        review_answers=submission_data.review_answers,
        found_issues=submission_data.found_issues,
        improved_code=submission_data.improved_code,
        passed=passed,
        time_spent=submission_data.time_spent
    )
    
    return {
        "success": passed,
        "submission_id": submission.id,
        "score": round(score * 100, 1),
        "matched_issues": list(matched_issues),
        "expected_issues": expected_issues,
        "found_issues": found_issues,
        "attempts": submission.attempts,
        "feedback": _generate_review_feedback(matched_issues, expected_issues, found_issues)
    }


def _generate_review_feedback(matched: set, expected: list, found: list) -> str:
    """Генерирует фидбек для Review задачи"""
    if len(matched) == len(expected):
        return "Отлично! Ты нашел все проблемы."
    elif len(matched) >= len(expected) * 0.6:
        missing = set(expected) - matched
        return f"Хорошо! Найдено {len(matched)} из {len(expected)} проблем. Пропущено: {', '.join(missing)}"
    else:
        missing = set(expected) - matched
        return f"Нужно больше практики. Найдено {len(matched)} из {len(expected)} проблем. Пропущено: {', '.join(missing)}"


@app.get("/api/tasks/{task_id}/submissions")
async def get_task_submissions(task_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Получить историю отправок решения задачи"""
    submissions = crud.get_task_submissions(db, task_id, limit)
    
    result = []
    for sub in submissions:
        result.append({
            "id": sub.id,
            "passed": sub.passed,
            "attempts": sub.attempts,
            "time_spent": sub.time_spent,
            "submitted_at": sub.submitted_at.isoformat(),
            "compilation_errors": sub.compilation_result.get("errors", []) if sub.compilation_result else []
        })
    
    return result


@app.get("/api/tasks/stats")
async def get_task_statistics(topic_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Получить статистику по задачам"""
    return crud.get_user_task_statistics(db, topic_id)


if __name__ == "__main__":
    import uvicorn
    # При прямом запуске reload не работает, используем без него
    uvicorn.run(app, host="0.0.0.0", port=8000)

