from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from models.user import UserResponse, UserCreate, LoginRequest, Token, PasswordChange
from database.entities.user import User
from kafka_config import publish_event
from services.auth import get_password_hash, verify_password, create_access_token, get_current_user, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
import boto3
import os

#Business logic goes here.

# S3 Client gets credentials from .env file
s3_client = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def list_users(db: Session) -> list[UserResponse]:
    usuarios = db.query(User).all()
    return usuarios

def get_user_by_id(db: Session, user_id: int) -> UserResponse:
    usuario = db.query(User).filter(User.id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} does not exist"
        )
    return usuario

async def create_user(db: Session, usuario: UserCreate) -> UserResponse:
    # Check if email already exists
    db_usuario = db.query(User).filter(User.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Create inactive user, no profile pic
    db_usuario = User(nombre=usuario.nombre, email=usuario.email, hashed_password=get_password_hash(usuario.password), activo=False, profile_picture=False)

    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)

    # Publish signup event to Kafka
    await publish_event('user_created', {
        'user_id': db_usuario.id,
        'nombre': db_usuario.nombre,
        'email': db_usuario.email,
    })

    return db_usuario

def login(db: Session, login_data: LoginRequest) -> Token:
    # Check user existence
    usuario = db.query(User).filter(User.email == login_data.email).first()
    
    # check password
    if not usuario or not verify_password(login_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # create JWT token for the session
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

def change_password(db: Session, password_data: PasswordChange, current_user: User) -> str:
    # Check current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wrong password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"mensaje": "Password updated"}

async def delete_account(db: Session, current_user: User):
    # Publish account deletion Kafka event
    await publish_event('account_deleted', {
        'user_id': current_user.id,
        'email': current_user.email,
        'nombre': current_user.nombre
    })
    
    # Remove S3 profile pic
    '''
    if current_user.profile_picture:
        try:
            s3_key = f"profile_photos/{current_user.id}.jpg"
            bucket = os.getenv("AWS_S3_BUCKET")
            s3_client.delete_object(Bucket=bucket, Key=s3_key)
        except Exception as e:
            print(f"Error eliminando foto de S3: {e}")
    '''
    
    # Delete user account
    db.delete(current_user)
    db.commit()
    
    return None