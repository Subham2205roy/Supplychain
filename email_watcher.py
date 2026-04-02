import os
import sys
import time
from datetime import datetime
from imap_tools import MailBox, A
import requests

# Adds the project root to the Python path so it can find backend models
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.database.database import SessionLocal
from backend.models.automation_model import Automation
from backend.settings import settings

# --- Configuration ---
EMAIL_SERVER = 'imap.gmail.com'
EMAIL_ADDRESS = 'my.supplychain.app@gmail.com'
EMAIL_PASSWORD = 'gqsq nnoa dtsw ruyx'
API_UPLOAD_URL = 'http://127.0.0.1:8000/upload/internal/csv'

def get_active_automations():
    """Fetches verified sender-to-user mappings from the database."""
    db = SessionLocal()
    try:
        now = datetime.utcnow().date()
        automations = db.query(Automation).filter(
            Automation.is_verified == True,
            (Automation.expires_at == None) | (Automation.expires_at >= now)
        ).all()
        # Return a dict {sender_email: user_id}
        return {a.sender_email.lower(): a.user_id for a in automations}
    finally:
        db.close()

def download_and_upload_attachments():
    """Connects to the email, checks against authorized senders, and uploads CSVs."""
    automation_map = get_active_automations()
    if not automation_map:
        print("No active automations found. Skipping check.")
        return

    active_senders = list(automation_map.keys())

    try:
        with MailBox(EMAIL_SERVER).login(EMAIL_ADDRESS, EMAIL_PASSWORD, 'INBOX') as mailbox:
            print(f"Logged in, watching for emails from {len(active_senders)} authorized senders...")
            
            for msg in mailbox.fetch(A(seen=False)):
                sender = msg.from_.lower()
                
                if sender not in automation_map:
                    continue

                user_id = automation_map[sender]
                print(f"Processing authorized email from: {sender} (User ID: {user_id})")
                
                for att in msg.attachments:
                    if att.filename.lower().endswith('.csv'):
                        print(f"  Found CSV attachment: {att.filename}")
                        
                        temp_filepath = os.path.join('.', att.filename)
                        with open(temp_filepath, 'wb') as f:
                            f.write(att.payload)
                        
                        try:
                            with open(temp_filepath, 'rb') as f:
                                files = {'file': (att.filename, f, 'text/csv')}
                                params = {
                                    'user_id': user_id,
                                    'internal_key': settings.internal_service_key
                                }
                                response = requests.post(API_UPLOAD_URL, files=files, params=params)
                            
                            if response.status_code == 200:
                                print(f"  ✅ Successfully uploaded {att.filename} for User {user_id}")
                                mailbox.seen([msg.uid], True)
                            else:
                                print(f"  ❌ API Error: {response.status_code} - {response.text}")
                        except requests.exceptions.RequestException as e:
                            print(f"  ❌ Connection Error: {e}")
                        
                        if os.path.exists(temp_filepath):
                            os.remove(temp_filepath)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    print("Starting Multi-User Email Automation Service...")
    while True:
        download_and_upload_attachments()
        time.sleep(30)
