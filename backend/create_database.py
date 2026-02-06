# File: backend/create_database.py

# This script's only job is to create the database tables.
# It does NOT add any data.

import sys
import os

# Adds the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.database import engine, Base
from backend.models.user_model import User
from backend.models.company_model import Company
from backend.models.team_invite_model import TeamInvite
from backend.models.sales_model import Sale # Models need to be imported to be recognized

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully. The database is now ready and empty.")
