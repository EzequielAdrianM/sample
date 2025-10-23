from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from datetime import datetime
import enum
from database.connection import Base

class Priority(enum.Enum):
	Normal = 0
	Low = 1
	Medium = 2
	High = 3
	Top = 4

class Todo(Base):
	__tablename__ = "todos"

	id = Column(Integer, primary_key=True, index=True)
	user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
	description = Column(String(255), nullable=False)
	due_date = Column(DateTime, nullable=True)#Can be undefined deadline
	is_completed = Column(Boolean, nullable=False, default=False)
	created_at = Column(DateTime, nullable=False, default=lambda: datetime.now())
	completed_at = Column(DateTime, nullable=True)
	priority = Column(Enum(Priority), nullable=False, default=Priority.Normal)