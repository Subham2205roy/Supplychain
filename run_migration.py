"""Script to run alembic migration against Supabase.
Reads DB credentials from .env via settings — no hardcoded passwords.
"""
import os
import sys

# Load .env first
from dotenv import load_dotenv
load_dotenv()

# Build connection URL from .env variables
from sqlalchemy.engine import URL

db_host = os.getenv("DB_HOST")
db_port = int(os.getenv("DB_PORT", "5432"))
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME", "postgres")

if not db_host or not db_password:
    print("ERROR: DB_HOST and DB_PASSWORD must be set in .env for Supabase migration.")
    print("Uncomment the Supabase section in your .env file and set the values.")
    sys.exit(1)

url = URL.create(
    drivername="postgresql",
    username=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    database=db_name,
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
