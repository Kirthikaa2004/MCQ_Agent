from sqlalchemy.orm import  declarative_base
from datetime import datetime
from sqlalchemy import Column,String,Boolean,DateTime,Text,ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from src.repositories.database import Base
import uuid




class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True,nullable=False)
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default="system")

class UserThread(Base):
    __tablename__ = "users_thread"
    user_thread_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True),ForeignKey("users.user_id"),nullable=False)
    thread_id = Column(UUID(as_uuid=True),nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default="system")

class ErrLog(Base):
    __tablename__ = "err_logs"

    id= Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=True)
    function_name = Column(String(255), nullable=True)
    message = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), default="system")
