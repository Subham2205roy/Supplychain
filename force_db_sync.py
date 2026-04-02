import os
import sys

# Add root directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.database import engine, Base
from backend.settings import settings

# Import ALL models so Base knows about them
from backend.models.user_model import User
from backend.models.company_model import Company
from backend.models.sales_model import Sale
from backend.models.inventory_model import Inventory
from backend.models.supplier_model import Supplier
from backend.models.customer_model import Customer
from backend.models.activity_model import Notification, ActivityLog
from backend.models.automation_model import Automation
# Add others as needed...

def main():
    print(f"--- Force Creating Tables via Base.metadata (using {settings.sqlalchemy_database_url[:30]}...) ---")
    try:
        # Create all tables that don't exist
        Base.metadata.create_all(bind=engine)
        print("SUCCESS: Tables created or already existed.")
    except Exception as e:
        print(f"FAILURE during forced creation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
