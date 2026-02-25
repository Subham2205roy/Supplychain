from sqlalchemy.orm import Session
from backend.database.database import SessionLocal, engine, Base
from backend.models.inventory_model import Inventory
from backend.models.company_model import Company
from backend.models.user_model import User

def seed_inventory():
    # 1. Ensure table exists
    print("🛠️ Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        # Get the first user/company in the system for testing
        user = db.query(User).first()
        if not user:
            print("❌ No user found. Please register a user first.")
            return

        company_id = user.company_id
        
        # Clear existing test data for this company
        db.query(Inventory).filter(Inventory.company_id == company_id).delete()
        
        test_items = [
            Inventory(company_id=company_id, product_name="Laptop", stock_level=5, reorder_point=10),
            Inventory(company_id=company_id, product_name="Mouse", stock_level=50, reorder_point=20),
            Inventory(company_id=company_id, product_name="Keyboard", stock_level=2, reorder_point=5),
            Inventory(company_id=company_id, product_name="Monitor", stock_level=15, reorder_point=5),
        ]
        
        db.add_all(test_items)
        db.commit()
        print(f"✅ Successfully seeded 4 inventory items for company {company_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_inventory()
