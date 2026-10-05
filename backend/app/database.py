from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings

# SQLite specific connect args to allow multithreading and enforce foreign keys
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import backend.app.models  # Ensure models are registered
    Base.metadata.create_all(bind=engine)
    # Safe additive migration for existing SQLite installations.
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.begin() as connection:
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(evidences)").fetchall()}
            if "file_name" not in columns:
                connection.exec_driver_sql("ALTER TABLE evidences ADD COLUMN file_name VARCHAR(255)")
            if "added_at" not in columns:
                connection.exec_driver_sql("ALTER TABLE evidences ADD COLUMN added_at DATETIME")
            case_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(cases)").fetchall()}
            if "priority" not in case_columns:
                connection.exec_driver_sql("ALTER TABLE cases ADD COLUMN priority VARCHAR(20) NOT NULL DEFAULT 'Medium'")
            if "objective" not in case_columns:
                connection.exec_driver_sql("ALTER TABLE cases ADD COLUMN objective TEXT")
            if "additional_context" not in case_columns:
                connection.exec_driver_sql("ALTER TABLE cases ADD COLUMN additional_context TEXT")
