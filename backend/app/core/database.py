from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Configure SQLite check_same_thread and timeout if using SQLite
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False, "timeout": 60}

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=60000")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base class for models
Base = declarative_base()

# Dependency to get db session in FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
