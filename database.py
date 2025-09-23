from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    phone_number = Column(String(20))
    first_name = Column(String(100))
    username = Column(String(100))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Voice(Base):
    __tablename__ = 'voices'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(String(200), nullable=False)
    file_path = Column(String(500))
    tags = Column(Text)  # JSON string of tags
    title = Column(String(200))
    duration = Column(Integer)  # in seconds
    usage_count = Column(Integer, default=0)
    created_by = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class VoiceRequest(Base):
    __tablename__ = 'voice_requests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    description = Column(Text)
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
engine = create_engine('sqlite:///sootfun.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

