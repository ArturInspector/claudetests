from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"

# Создание engine и session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Topic(Base):
    """Темы вопросов (Solidity, Python, Web3, etc.)"""
    __tablename__ = "topics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")


class Question(Base):
    """Вопросы для практики"""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    title = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)  # Easy, Medium, Hard
    question_type = Column(String(20), nullable=False)  # Text, Code
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Новые поля для многоуровневой системы
    level = Column(Integer, default=1)  # 1-4 (L1: Surface, L2: Deeper, L3: Expert, L4: Master)
    parent_concept_id = Column(Integer, ForeignKey("questions.id"), nullable=True)  # Связь с родительским концептом
    tags = Column(JSON, nullable=True)  # ["security", "gas-optimization", ...]
    estimated_time = Column(Integer, nullable=True)  # Время в минутах
    
    # Связи
    topic = relationship("Topic", back_populates="questions")
    user_answers = relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="question", cascade="all, delete-orphan")
    user_notes = relationship("UserNote", back_populates="question", cascade="all, delete-orphan")
    
    # Связи для многоуровневых вопросов
    child_questions = relationship("Question", backref="parent_concept", remote_side=[id])


class UserAnswer(Base):
    """Ответы пользователя на вопросы"""
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    user_answer = Column(Text, nullable=True)
    answered_at = Column(DateTime, default=datetime.utcnow)
    
    time_spent = Column(Integer, nullable=True)  # Время в секундах
    showed_answer = Column(Boolean, default=False)  # Показывал ли ответ сразу
    confidence_level = Column(Integer, nullable=True)  # 1-5 (насколько уверен)
    next_review_date = Column(DateTime, nullable=True)  # Следующая дата повторения
    review_count = Column(Integer, default=0)  # Количество повторений
    
    # Связи
    question = relationship("Question", back_populates="user_answers")
    session = relationship("Session", back_populates="answers")


class Session(Base):
    """Сессии практики"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    questions_count = Column(Integer, default=0)
    duration_minutes = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    answers = relationship("UserAnswer", back_populates="session", cascade="all, delete-orphan")


class ConceptLink(Base):
    """Связи между концептами/вопросами"""
    __tablename__ = "concept_links"
    
    id = Column(Integer, primary_key=True, index=True)
    from_question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    to_question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # prerequisite, related, deeper, example, sibling
    created_at = Column(DateTime, default=datetime.utcnow)


class Resource(Base):
    """Ресурсы для углубленного изучения"""
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    type = Column(String(20), nullable=False)  # article, video, code, tool, docs
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    quality_score = Column(Float, default=0.0)  # Community rating 0-5
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь
    question = relationship("Question", back_populates="resources")


class UserNote(Base):
    """Личные заметки пользователя к вопросам"""
    __tablename__ = "user_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь
    question = relationship("Question", back_populates="user_notes")


def init_db():
    """Инициализация базы данных - создание всех таблиц"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Получение сессии базы данных для dependency injection в FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DATABASE_URL}")

