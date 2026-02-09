import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from datetime import datetime

Base = declarative_base()

# Таблица Источников (Чаты/Группы)
class Source(Base):
    __tablename__ = 'sources'
    id = Column(Integer, primary_key=True)
    platform = Column(String) # 'telegram', 'vk'
    link = Column(String, unique=True)
    title = Column(String)
    is_active = Column(Boolean, default=True)

# Таблица Лидов
class Lead(Base):
    __tablename__ = 'leads'
    id = Column(Integer, primary_key=True)
    source_link = Column(String)
    user_id = Column(String)       # ID пользователя в соцсети
    username = Column(String)
    raw_text = Column(Text)
    
    # AI Analysis
    score = Column(Integer, default=0) # 0-2
    city = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    
    status = Column(String, default='new') # new, sold
    created_at = Column(DateTime, default=datetime.utcnow)

# Таблица Партнеров
class Partner(Base):
    __tablename__ = 'partners'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    balance = Column(Float, default=0.0)

# Инициализация
engine = create_async_engine('sqlite+aiosqlite:///leads.db', echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
