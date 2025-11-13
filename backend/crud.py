from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import random

from database import Topic, Question, UserAnswer, Session as DBSession, Resource, UserNote, ConceptLink


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
    answer_text: str,
    level: int = 1,
    parent_concept_id: int = None,
    tags: List[str] = None,
    estimated_time: int = None
) -> Question:
    """Создать новый вопрос"""
    question = Question(
        topic_id=topic_id,
        title=title,
        difficulty=difficulty,
        question_type=question_type,
        question_text=question_text,
        answer_text=answer_text,
        level=level,
        parent_concept_id=parent_concept_id,
        tags=tags,
        estimated_time=estimated_time
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
    session_id: int = None,
    time_spent: int = None,
    showed_answer: bool = False,
    confidence_level: int = None
) -> UserAnswer:
    """Сохранить ответ пользователя с расширенной аналитикой"""
    # Вычисляем next_review_date на основе confidence и showed_answer
    next_review = calculate_next_review_date(confidence_level, showed_answer)
    
    answer = UserAnswer(
        question_id=question_id,
        user_answer=user_answer,
        session_id=session_id,
        time_spent=time_spent,
        showed_answer=showed_answer,
        confidence_level=confidence_level,
        next_review_date=next_review,
        review_count=1
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


# ==================== SPACED REPETITION ====================

def calculate_next_review_date(confidence_level: Optional[int] = None, showed_answer: bool = False) -> datetime:
    """
    Вычисляет следующую дату повторения на основе confidence level
    
    Алгоритм (упрощенный SM-2):
    - Показал ответ сразу: 1 день
    - Confidence 1-2: 1 день
    - Confidence 3: 3 дня
    - Confidence 4: 7 дней
    - Confidence 5: 14 дней
    """
    now = datetime.utcnow()
    
    if showed_answer or confidence_level is None or confidence_level < 3:
        return now + timedelta(days=1)
    elif confidence_level == 3:
        return now + timedelta(days=3)
    elif confidence_level == 4:
        return now + timedelta(days=7)
    else:  # confidence_level == 5
        return now + timedelta(days=14)


def get_questions_for_review(db: Session, limit: int = 20) -> List[Question]:
    """
    Получить вопросы на повторение сегодня
    Sorted по срочности (overdue first)
    """
    now = datetime.utcnow()
    
    # Получаем последние ответы на вопросы где next_review_date <= now
    subquery = db.query(
        UserAnswer.question_id,
        func.max(UserAnswer.answered_at).label('last_answered')
    ).group_by(UserAnswer.question_id).subquery()
    
    questions_to_review = db.query(Question).join(
        UserAnswer, Question.id == UserAnswer.question_id
    ).join(
        subquery, 
        (UserAnswer.question_id == subquery.c.question_id) & 
        (UserAnswer.answered_at == subquery.c.last_answered)
    ).filter(
        UserAnswer.next_review_date <= now
    ).order_by(
        UserAnswer.next_review_date
    ).limit(limit).all()
    
    return questions_to_review


def update_review_status(
    db: Session,
    question_id: int,
    confidence_level: int,
    time_spent: int = None
) -> UserAnswer:
    """Обновить статус повторения вопроса"""
    # Получаем последний ответ на этот вопрос
    last_answer = db.query(UserAnswer).filter(
        UserAnswer.question_id == question_id
    ).order_by(desc(UserAnswer.answered_at)).first()
    
    # Увеличиваем review_count
    review_count = (last_answer.review_count + 1) if last_answer else 1
    
    # Вычисляем следующую дату с учетом количества повторений
    base_interval = calculate_next_review_date(confidence_level, False)
    # Увеличиваем интервал с каждым повторением
    interval_multiplier = min(review_count, 5)  # Макс 5x
    next_review = base_interval + timedelta(days=(interval_multiplier - 1) * 3)
    
    # Создаем новую запись ответа (для истории)
    new_answer = UserAnswer(
        question_id=question_id,
        user_answer="",  # При review не сохраняем ответ
        confidence_level=confidence_level,
        next_review_date=next_review,
        review_count=review_count,
        time_spent=time_spent,
        showed_answer=False
    )
    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)
    return new_answer


def get_review_stats(db: Session) -> Dict:
    """Получить статистику по повторениям"""
    now = datetime.utcnow()
    
    # Вопросы на сегодня
    today_count = db.query(func.count(func.distinct(UserAnswer.question_id))).filter(
        UserAnswer.next_review_date <= now
    ).scalar()
    
    # Вопросы на завтра
    tomorrow = now + timedelta(days=1)
    tomorrow_count = db.query(func.count(func.distinct(UserAnswer.question_id))).filter(
        UserAnswer.next_review_date > now,
        UserAnswer.next_review_date <= tomorrow
    ).scalar()
    
    # Всего вопросов в системе повторений
    total_in_review = db.query(func.count(func.distinct(UserAnswer.question_id))).filter(
        UserAnswer.next_review_date.isnot(None)
    ).scalar()
    
    return {
        "due_today": today_count or 0,
        "due_tomorrow": tomorrow_count or 0,
        "total_in_review": total_in_review or 0
    }


# ==================== RESOURCES ====================

def create_resource(
    db: Session,
    question_id: int,
    type: str,
    title: str,
    url: str,
    description: str = None
) -> Resource:
    """Создать ресурс для вопроса"""
    resource = Resource(
        question_id=question_id,
        type=type,
        title=title,
        url=url,
        description=description
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


def get_resources_by_question(db: Session, question_id: int) -> List[Resource]:
    """Получить все ресурсы для вопроса"""
    return db.query(Resource).filter(Resource.question_id == question_id).all()


# ==================== USER NOTES ====================

def save_or_update_note(db: Session, question_id: int, note_text: str) -> UserNote:
    """Сохранить или обновить заметку к вопросу"""
    note = db.query(UserNote).filter(UserNote.question_id == question_id).first()
    
    if note:
        note.note_text = note_text
        note.updated_at = datetime.utcnow()
    else:
        note = UserNote(
            question_id=question_id,
            note_text=note_text
        )
        db.add(note)
    
    db.commit()
    db.refresh(note)
    return note


def get_note_by_question(db: Session, question_id: int) -> Optional[UserNote]:
    """Получить заметку по вопросу"""
    return db.query(UserNote).filter(UserNote.question_id == question_id).first()


def delete_note(db: Session, question_id: int) -> bool:
    """Удалить заметку"""
    note = db.query(UserNote).filter(UserNote.question_id == question_id).first()
    if note:
        db.delete(note)
        db.commit()
        return True
    return False


# ==================== CONCEPT LINKS ====================

def create_concept_link(
    db: Session,
    from_question_id: int,
    to_question_id: int,
    relationship_type: str
) -> ConceptLink:
    """Создать связь между вопросами"""
    link = ConceptLink(
        from_question_id=from_question_id,
        to_question_id=to_question_id,
        relationship_type=relationship_type
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def get_related_questions(db: Session, question_id: int) -> Dict[str, List[Question]]:
    """Получить связанные вопросы, сгруппированные по типу связи"""
    links = db.query(ConceptLink).filter(
        (ConceptLink.from_question_id == question_id) | 
        (ConceptLink.to_question_id == question_id)
    ).all()
    
    related = {}
    for link in links:
        # Определяем направление связи
        if link.from_question_id == question_id:
            related_id = link.to_question_id
        else:
            related_id = link.from_question_id
        
        question = get_question_by_id(db, related_id)
        if question:
            if link.relationship_type not in related:
                related[link.relationship_type] = []
            related[link.relationship_type].append(question)
    
    return related


def get_questions_by_level(db: Session, topic_id: int, level: int) -> List[Question]:
    """Получить вопросы определенного уровня по теме"""
    return db.query(Question).filter(
        Question.topic_id == topic_id,
        Question.level == level
    ).all()


def get_concept_children(db: Session, parent_concept_id: int) -> List[Question]:
    """Получить подвопросы концепта (для progressive disclosure)"""
    return db.query(Question).filter(
        Question.parent_concept_id == parent_concept_id
    ).order_by(Question.level).all()

