from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, init_db, SessionLocal
import crud
from parser import parse_markdown_content

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

class SessionEnd(BaseModel):
    session_id: int

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
    """Страница практики"""
    return templates.TemplateResponse("practice.html", {"request": request})


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Страница статистики"""
    return templates.TemplateResponse("stats.html", {"request": request})

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
        for q_data in parsed_data['questions']:
            crud.create_question(
                db=db,
                topic_id=topic.id,
                title=q_data['title'],
                difficulty=q_data['difficulty'],
                question_type=q_data['question_type'],
                question_text=q_data['question_text'],
                answer_text=q_data['answer_text']
            )
            questions_added += 1
        
        return {
            "success": True,
            "topic": parsed_data['topic'],
            "questions_added": questions_added
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
    """Сохранить ответ пользователя"""
    try:
        answer = crud.save_user_answer(
            db=db,
            question_id=answer_data.question_id,
            user_answer=answer_data.user_answer,
            session_id=answer_data.session_id
        )
        
        return {
            "success": True,
            "answer_id": answer.id
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


if __name__ == "__main__":
    import uvicorn
    # При прямом запуске reload не работает, используем без него
    uvicorn.run(app, host="0.0.0.0", port=8000)

