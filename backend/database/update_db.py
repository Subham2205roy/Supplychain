import sqlite3
import os

# Get the folder where this script is running
current_dir = os.path.dirname(os.path.abspath(__file__))

# Look for the database in the SAME folder
db_path = os.path.join(current_dir, 'supplychain.db')

print(f"🔍 Looking for database at: {db_path}")

if not os.path.exists(db_path):
    print("❌ ERROR: Database file not found!")
    print("   Make sure 'supplychain.db' is inside the 'backend/database' folder.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Attempting to add 'email' column...")
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR")
        conn.commit()
        print("✅ SUCCESS! The 'email' column was added.")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✅ GOOD NEWS: The 'email' column already exists!")
        else:
            print(f"⚠️ Error: {e}")
            
    finally:
        conn.close()