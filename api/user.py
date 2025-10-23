from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from models.user import UserResponse, UserCreate, Token, LoginRequest, PasswordChange
from database.connection import get_db
from database.entities.user import User
from services import user_service
from services import auth_service
from services.auth_service import get_current_user, get_current_active_user
from rate_limiting import limiter

router = APIRouter(
	prefix="/users",
	tags=["Users"]
)

@router.get("/hi")
def home():
    return {"mensaje": "Hello world!"}

@router.get("/all")
def list_users(db: Session = Depends(get_db)):
    return user_service.list_users(db)

@router.get("/{user_id}", response_model=UserResponse)
def get_single_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.get_user_by_id(db, user_id)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def create_user(request: Request, usuario: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, usuario)

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    return user_service.login(login_data, db)

# ============================================
# Protected endpoints (requires authentication)
# ============================================

@router.get("/activate", response_model=UserResponse)
def activate_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	return auth_service.activate_account(current_user, db)

@router.post("/change-password")
def change_password(password_data: PasswordChange, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    return user_service.change_password(password_data, db, current_user)

@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user_service.delete_account(db, current_user)