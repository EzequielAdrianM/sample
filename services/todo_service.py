from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.todo import TodoCreate, TodoResponse
from database.entities.todo import Todo
from database.entities.user import User

# I assume that if this gets called, user is already authenticated.
def create_todo(todo: TodoCreate, db: Session, current_user: User) -> Todo:
	#Try/catch?
	new_todo = Todo(**todo.model_dump())
	new_todo.user_id = current_user.id
	db.add(new_todo)
	db.commit()
	db.refresh(new_todo)
	return new_todo

def get_todos(db: Session, current_user: User) -> list[TodoResponse]:
	todos = db.query(Todo).filter(Todo.user_id == current_user.id).all()
	return todos

def get_todo_by_id(todo_id: int, db: Session, current_user: User) -> Todo:
	#get first Todo (if exists) and ONLY if it corresponds to myself. Otherwise you could delete other users todos.
	todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.user_id == current_user.id).first()
	if not todo:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Todo {todo_id} does not exist"
		)
	return todo

def update_todo(todo_id: int, todo_update: TodoCreate, db: Session, current_user: User) -> Todo:
	todo_data = todo_update.model_dump(exclude_unset=True)
	db.query(Todo).filter(Todo.id == todo_id).filter(Todo.user_id == current_user.id).update(todo_data)
	db.commit()
	return get_todo_by_id(todo_id, db, current_user)

def complete_todo(todo_id: int, db: Session, current_user: User) -> Todo:
	todo = get_todo_by_id(todo_id, db, current_user)
	if todo.is_completed:
		return todo
	todo.is_completed = True
	todo.completed_at = datetime.now()
	db.commit()
	db.refresh(todo)
	return todo

def delete_todo(todo_id: int, db: Session, current_user: User) -> None:
	todo = get_todo_by_id(db, current_user, todo_id)
	db.delete(todo)
	db.commit()