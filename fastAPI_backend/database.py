from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from config import SQL_ECHO
import os

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

DB_PASSWORD = os.getenv("AZURE_DB_PASS")
DB_TABLE = os.getenv("AZURE_DB_TABLE")
DB_USER = os.getenv("AZURE_DB_USER")
DB_HOST = os.getenv("AZURE_DB_HOST")
DB_PORT = os.getenv("AZURE_DB_PORT")

if not DB_PASSWORD:
  raise ValueError("Missing environment variable: AZURE_DB_PASS")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_TABLE}"

# Use configurable SQL echo setting
engine = create_async_engine(DATABASE_URL, echo=SQL_ECHO)

AsyncSessionLocal = sessionmaker(
  engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
  async with AsyncSessionLocal() as session:
    yield session