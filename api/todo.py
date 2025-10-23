from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from models.todo import TodoResponse, TodoCreate
from services import todo_service
from database.connection import get_db
from database.entities.user import User
from services.auth_service import get_current_active_user

router = APIRouter(
	prefix="/todo",
	tags=["Todo"]
)

# ============================================
# Protected endpoints (requires authentication)
# ============================================

@router.post("/create", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
	return todo_service.create_todo(todo, db, current_user)

@router.get("/", response_model=list[TodoResponse])
def get_todos(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
	return todo_service.get_todos(db, current_user)

@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
	return todo_service.get_todo_by_id(todo_id, db, current_user)


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
	return todo_service.update_todo(todo_id, todo_update, db, current_user)

@router.put("/{todo_id}/complete", response_model=TodoResponse)
def complete_todo(todo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
	return todo_service.complete_todo(todo_id, db, current_user)

@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
	todo_service.delete_todo(todo_id, db, current_user)