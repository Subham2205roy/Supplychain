from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.settings import settings

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

# Render/Supabase sometimes provide "postgres://" which SQLAlchemy 2.0+ requires as "postgresql://"
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

is_sqlite = SQLALCHEMY_DATABASE_URL.startswith("sqlite") if SQLALCHEMY_DATABASE_URL else True
connect_args = {"check_same_thread": False} if is_sqlite else {}

# Connection pool settings for production Postgres
pool_args = {}
if not is_sqlite:
    pool_args = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    **pool_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


from sqlalchemy import func

def date_format(column, format_str: str):
    """
    Returns a database-specific date formatting function.
    Supports 'YYYY-MM' and 'YYYY'.
    """
    if is_sqlite:
        # SQLite: strftime(format, timestring)
        if format_str == 'YYYY-MM':
            return func.strftime('%Y-%m', column)
        elif format_str == 'YYYY':
            return func.strftime('%Y', column)
        else:
            # Fallback for other formats
            return func.strftime(format_str.replace('YYYY', '%Y').replace('MM', '%m').replace('DD', '%d'), column)
    else:
        # PostgreSQL: to_char(timestamp, format)
        return func.to_char(column, format_str)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
