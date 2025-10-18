from fastapi import FastAPI, Form, File, UploadFile, Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from kafka_config import start_kafka, stop_kafka, publish_event

# Lifespan para iniciar/cerrar Kafka
#Me da la impresion que esto abre y cierra el producer de kafka junto con el worker de FastAPI.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await start_kafka()
    print("✅ Kafka producer conectado")
    yield
    # Shutdown
    await stop_kafka()
    print("❌ Kafka producer desconectado")

app = FastAPI(lifespan=lifespan)

@app.get("/")
def home():
    return {"mensaje": "Hola mundo"}

@app.get("/usuarios/{id}")
def obtener_usuario(id: int):
    return {"id": id, "nombre": "Juan"}

@app.post("/usuarios")
def crear_usuario(nombre: str, email: str):
    return {"nombre": nombre, "email": email}