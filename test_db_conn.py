import os
import sys
from sqlalchemy import create_engine, text
from backend.settings import settings

print("Checking settings...")
url = settings.sqlalchemy_database_url
print(f"URL: {url[:50]}...")

print("Attempting to connect...")
engine = create_engine(url)
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).fetchone()
        print(f"SUCCESS! Result: {result}")
except Exception as e:
    print(f"FAILURE: {e}")
    import traceback
    traceback.print_exc()
