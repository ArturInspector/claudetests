from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict
from datetime import datetime
import random

from database import Topic, Question, UserAnswer, Session as DBSession


# ==================== TOPICS ====================

def get_or_create_topic(db: Session, name: str, description: str = None) -> Topic:
    """Получить существующую тему или создать новую"""
    topic = db.query(Topic).filter(Topic.name == name).first()
    if not topic:
        topic = Topic(name=name, description=description)
        db.add(topic)
        db.commit()
        db.refresh(topic)
    return topic


def get_all_topics(db: Session) -> List[Topic]:
    """Получить все темы с количеством вопросов"""
    return db.query(Topic).all()


def get_topic_by_id(db: Session, topic_id: int) -> Optional[Topic]:
    """Получить тему по ID"""
    return db.query(Topic).filter(Topic.id == topic_id).first()


# ==================== QUESTIONS ====================

def create_question(
    db: Session,
    topic_id: int,
    title: str,
    difficulty: str,
    question_type: str,
    question_text: str,
    answer_text: str
) -> Question:
    """Создать новый вопрос"""
    question = Question(
        topic_id=topic_id,
        title=title,
        difficulty=difficulty,
        question_type=question_type,
        question_text=question_text,
        answer_text=answer_text
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def get_questions_by_topic(db: Session, topic_id: int, difficulty: str = None) -> List[Question]:
    """Получить все вопросы по теме с опциональным фильтром по сложности"""
    query = db.query(Question).filter(Question.topic_id == topic_id)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    return query.all()


def get_random_question(db: Session, topic_id: int, difficulty: str = None, exclude_ids: List[int] = None) -> Optional[Question]:
    """Получить случайный вопрос по теме"""
    query = db.query(Question).filter(Question.topic_id == topic_id)
    
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    if exclude_ids:
        query = query.filter(~Question.id.in_(exclude_ids))
    
    questions = query.all()
    if not questions:
        return None
    
    return random.choice(questions)


def get_question_by_id(db: Session, question_id: int) -> Optional[Question]:
    """Получить вопрос по ID"""
    return db.query(Question).filter(Question.id == question_id).first()


def delete_questions_by_topic(db: Session, topic_id: int) -> int:
    """Удалить все вопросы по теме (для переимпорта)"""
    count = db.query(Question).filter(Question.topic_id == topic_id).delete()
    db.commit()
    return count


# ==================== USER ANSWERS ====================

def save_user_answer(
    db: Session,
    question_id: int,
    user_answer: str,
    session_id: int = None
) -> UserAnswer:
    """Сохранить ответ пользователя"""
    answer = UserAnswer(
        question_id=question_id,
        user_answer=user_answer,
        session_id=session_id
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def get_answered_questions_in_session(db: Session, session_id: int) -> List[int]:
    """Получить список ID вопросов, на которые уже ответили в этой сессии"""
    answers = db.query(UserAnswer.question_id).filter(
        UserAnswer.session_id == session_id
    ).all()
    return [a[0] for a in answers]


def get_user_answers_by_question(db: Session, question_id: int, limit: int = 5) -> List[UserAnswer]:
    """Получить последние ответы пользователя на вопрос"""
    return db.query(UserAnswer).filter(
        UserAnswer.question_id == question_id
    ).order_by(desc(UserAnswer.answered_at)).limit(limit).all()


# ==================== SESSIONS ====================

def create_session(db: Session) -> DBSession:
    """Создать новую сессию практики"""
    session = DBSession(started_at=datetime.utcnow())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def end_session(db: Session, session_id: int, summary: str = None) -> DBSession:
    """Завершить сессию и сохранить summary"""
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if session:
        session.ended_at = datetime.utcnow()
        
        # Подсчитать количество вопросов
        session.questions_count = db.query(UserAnswer).filter(
            UserAnswer.session_id == session_id
        ).count()
        
        # Подсчитать продолжительность в минутах
        if session.started_at and session.ended_at:
            duration = (session.ended_at - session.started_at).total_seconds() / 60
            session.duration_minutes = round(duration, 2)
        
        session.summary = summary
        db.commit()
        db.refresh(session)
    
    return session


def get_session_by_id(db: Session, session_id: int) -> Optional[DBSession]:
    """Получить сессию по ID"""
    return db.query(DBSession).filter(DBSession.id == session_id).first()


def get_recent_sessions(db: Session, limit: int = 10) -> List[DBSession]:
    """Получить последние сессии"""
    return db.query(DBSession).order_by(desc(DBSession.started_at)).limit(limit).all()


# ==================== STATISTICS ====================

def get_statistics(db: Session) -> Dict:
    """Получить общую статистику"""
    # Общее количество вопросов
    total_questions = db.query(Question).count()
    
    # Количество отвеченных уникальных вопросов
    answered_questions = db.query(func.count(func.distinct(UserAnswer.question_id))).scalar()
    
    # Количество сессий
    total_sessions = db.query(DBSession).count()
    
    # Статистика по темам
    topics_stats = []
    topics = get_all_topics(db)
    
    for topic in topics:
        question_count = db.query(Question).filter(Question.topic_id == topic.id).count()
        
        # Количество отвеченных вопросов по теме
        answered_count = db.query(func.count(func.distinct(UserAnswer.question_id))).join(
            Question, UserAnswer.question_id == Question.id
        ).filter(Question.topic_id == topic.id).scalar()
        
        topics_stats.append({
            "id": topic.id,
            "name": topic.name,
            "total_questions": question_count,
            "answered_questions": answered_count or 0,
            "progress_percent": round((answered_count or 0) / question_count * 100, 1) if question_count > 0 else 0
        })
    
    # Активность по дням (последние 30 дней)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_activity = db.query(
        func.date(UserAnswer.answered_at).label('date'),
        func.count(UserAnswer.id).label('count')
    ).filter(
        UserAnswer.answered_at >= thirty_days_ago
    ).group_by(
        func.date(UserAnswer.answered_at)
    ).all()
    
    activity_data = [{"date": str(date), "count": count} for date, count in daily_activity]
    
    return {
        "total_questions": total_questions,
        "answered_questions": answered_questions or 0,
        "progress_percent": round((answered_questions or 0) / total_questions * 100, 1) if total_questions > 0 else 0,
        "total_sessions": total_sessions,
        "topics": topics_stats,
        "daily_activity": activity_data
    }

