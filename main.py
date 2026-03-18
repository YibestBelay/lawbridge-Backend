from fastapi import FastAPI
from database import engine
from models import Base
import models
from routers import users

# creates all tables in PostgreSQL automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LawBridge API")

app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "LawBridge API is running!"}