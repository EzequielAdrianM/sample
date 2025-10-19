from fastapi import FastAPI, Form, File, UploadFile, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from database import engine, get_db, Base
import models, schemas
import boto3
import os
from dotenv import load_dotenv
from kafka_config import start_kafka, stop_kafka, publish_event
from auth import get_password_hash, verify_password, create_access_token, get_current_user, get_current_active_user, ACCESS_TOKEN_EXPIRE_MINUTES
from rate_limiting import limiter

load_dotenv()

# Uncomment this only when first starting the app, to create new tables.
#Base.metadata.create_all(bind=engine)

# S3 Client gets credentials from .env file
s3_client = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

#Sync kafka producer lifecycle with this fastapi worker.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await start_kafka()
    #Start any other services....
    print("✅ Kafka producer connected")
    yield
    # Shutdown
    await stop_kafka()
    print("❌ Kafka producer disconnected")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {"mensaje": "Hello world!"}

@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    usuarios = db.query(models.User).all()
    return usuarios

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_single_user(user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(models.User).filter(models.User.id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} does not exist"
        )
    return usuario

@app.post("/signup", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def create_user(request: Request, usuario: schemas.UserCreate, db: Session = Depends(get_db)):

    # Check if email already exists
    db_usuario = db.query(models.User).filter(models.User.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

    # Create inactive user, no profile pic
    db_usuario = models.User(nombre=usuario.nombre, email=usuario.email, hashed_password=get_password_hash(usuario.password), activo=False, profile_picture=False)

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

@app.post("/login", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    # Check user existence
    usuario = db.query(models.User).filter(models.User.email == login_data.email).first()
    
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

# ============================================
# Protected endpoints (requires authentication)
# ============================================

@app.post("/change-password")
def change_password(
    password_data: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
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

@app.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    
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