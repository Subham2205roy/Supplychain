import sqlite3
import os

# --- USE THE EXACT ABSOLUTE PATH ---
# Based on your error message, this is exactly where your database lives.
db_path = r"C:\Users\HP\OneDrive\Desktop\supplychain\backend\supplychain.db"

print(f"📂 Connecting to database at: {db_path}")

if not os.path.exists(db_path):
    print("❌ ERROR: The file 'supplychain.db' was not found at that path.")
    print("   Please check if the file name is correct or if it was deleted.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔧 Attempting to add 'email' column...")
        cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR")
        conn.commit()
        print("✅ SUCCESS! 'email' column added.")
        print("   You can now restart your server and Login with Email!")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✅ GOOD NEWS: The 'email' column already exists!")
            print("   You don't need to do anything else.")
        else:
            print(f"⚠️ Error: {e}")
            
    finally:
        if 'conn' in locals():
            conn.close()