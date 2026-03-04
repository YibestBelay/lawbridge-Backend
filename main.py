from fastapi import FastAPI
from database import engine
from models import Base

# creates all tables in PostgreSQL automatically
Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "LawBridge API is running!"}