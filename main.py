from fastapi import FastAPI
from contextlib import asynccontextmanager
from database.connection import engine, get_db, Base
from dotenv import load_dotenv
from kafka_config import start_kafka, stop_kafka
from api import user, todo

load_dotenv()

# Uncomment this only when first starting the app, to create new tables.
Base.metadata.create_all(bind=engine)



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

#Register routes
app.include_router(user.router, prefix="/api")
app.include_router(todo.router, prefix="/api")