from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

db_engine = create_engine(DATABASE_URL, echo=True)

# Base class for declarative models (the ones from models.py
Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
