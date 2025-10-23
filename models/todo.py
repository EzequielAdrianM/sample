from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from database.entities.todo import Priority

class TodoBase(BaseModel):
	description: str
	due_date: Optional[datetime] = None
	priority: Priority = Priority.Normal

class TodoCreate(TodoBase):
	pass

class TodoResponse(TodoBase):
	id: str
	is_completed: bool
	completed_at: Optional[datetime] = None

	model_config = ConfigDict(from_attributes=True)