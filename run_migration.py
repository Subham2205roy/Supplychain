"""Temporary script to run alembic migration against Supabase.
Sets DATABASE_URL BEFORE any imports that read .env.
"""
import os
import sys

# MUST set env var BEFORE importing anything from backend
from sqlalchemy.engine import URL
url = URL.create(
    drivername="postgresql",
    username="postgres",
    password="Subham5062@_",
    host="db.ndwnwzwuomwwyfthhdwb.supabase.co",
    port=5432,
    database="postgres",
)
# render_as_string with hide_password=False keeps the %40 encoding
os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)

# Now test the connection
from sqlalchemy import create_engine, text
print("Testing connection to Supabase...")
engine = create_engine(url)
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("Connection successful!")
    engine.dispose()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# Now run alembic
print("Running alembic migration...")
from alembic.config import Config
from alembic import command

alembic_cfg = Config("alembic.ini")
command.upgrade(alembic_cfg, "head")
print("Migration complete! All tables created in Supabase.")
