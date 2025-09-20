from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings
import os
import json

os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{settings.DB_PATH}", connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class UserDoc(Base):
    __tablename__ = "user_docs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    path = Column(String)
    meta = Column(Text)  

Base.metadata.create_all(bind=engine)
