from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

Base = declarative_base()

engine = create_engine(
    settings.database_url,
    echo=True, 
    pool_pre_ping=True  
)

SessionLocal = sessionmaker(bind=engine)




