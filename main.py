from fastapi import FastAPI, Form, File, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from database import engine, get_db, Base
import models, schemas
import boto3
import os
from dotenv import load_dotenv
from kafka_config import start_kafka, stop_kafka, publish_event

load_dotenv()

# Crear tablas
Base.metadata.create_all(bind=engine)

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

@app.post("/users/create", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(usuario: schemas.UserCreate, db: Session = Depends(get_db)):

    # Check if email already exists
    db_usuario = db.query(models.User).filter(models.User.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado"
        )

    # Create inactive user, no profile pic
    db_usuario = models.User(nombre=usuario.nombre, email=usuario.email, activo=False, profile_picture=False)

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

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    usuario = db.query(models.User).filter(models.User.id == user_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} does not exist"
        )
    
    db.delete(usuario)
    db.commit()
    return None