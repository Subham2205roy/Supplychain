import sqlite3
import os

db_path = "supplychain.db"

if not os.path.exists(db_path):
    print("❌ Error: Can't find supplychain.db")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Adding 'owner_id' column to sales table...")
        
        # 1. Add the column (Allowing NULL temporarily)
        cursor.execute("ALTER TABLE sales ADD COLUMN owner_id INTEGER")
        
        # 2. Assign all current data to User #1 (So it doesn't disappear)
        print("🏠 Assigning existing data to User ID 1...")
        cursor.execute("UPDATE sales SET owner_id = 1 WHERE owner_id IS NULL")
        
        conn.commit()
        print("✅ SUCCESS! Your database is now SaaS-ready.")
        print("   Column 'owner_id' added and filled.")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✅ 'owner_id' already exists! You are good to go.")
        else:
            print(f"⚠️ Error: {e}")
            
    finally:
        conn.close()