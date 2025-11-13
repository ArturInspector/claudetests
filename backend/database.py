from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
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
    
    # Связи
    topic = relationship("Topic", back_populates="questions")
    user_answers = relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan")


class UserAnswer(Base):
    """Ответы пользователя на вопросы"""
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    user_answer = Column(Text, nullable=True)
    answered_at = Column(DateTime, default=datetime.utcnow)
    
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

