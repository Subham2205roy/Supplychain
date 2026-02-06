import os
import time
from imap_tools import MailBox, A
import requests

# --- Configuration (Ei jayga gulo apnake fillup korte hobe) ---
# ⚠️ Apnar notun email account-er details din
EMAIL_SERVER = 'imap.gmail.com'
EMAIL_ADDRESS = 'my.supplychain.app@gmail.com'
EMAIL_PASSWORD = 'gqsq nnoa dtsw ruyx'
SENDER_TO_WATCH = 'subham2205roy@gmail.com' # Shudhu ei sender theke email process hobe
API_UPLOAD_URL = 'http://127.0.0.1:8000/upload/csv'
# -----------------------------------------------------------

def download_and_upload_attachments():
    """Connects to the email, downloads CSVs, and sends them to the API."""
    try:
        # Mailbox-e connect kora
        with MailBox(EMAIL_SERVER).login(EMAIL_ADDRESS, EMAIL_PASSWORD, 'INBOX') as mailbox:
            print(f"Logged in as {EMAIL_ADDRESS}, watching for emails from {SENDER_TO_WATCH}...")
            
            # Shudhu matro nirdishto sender theke asha notun email khuje ber kora
            for msg in mailbox.fetch(A(from_=SENDER_TO_WATCH, seen=False)):
                print(f"Processing new email with subject: '{msg.subject}'")
                
                for att in msg.attachments:
                    # Check kora je attachment ti CSV file kina
                    if att.filename.lower().endswith('.csv'):
                        print(f"  Found CSV attachment: {att.filename}")
                        
                        # Attachment-ti ke temporary bhabe save kora
                        temp_filepath = os.path.join('.', att.filename)
                        with open(temp_filepath, 'wb') as f:
                            f.write(att.payload)
                        
                        # --- FastAPI app-e file-ti upload kora ---
                        try:
                            with open(temp_filepath, 'rb') as f:
                                files = {'file': (att.filename, f, 'text/csv')}
                                response = requests.post(API_UPLOAD_URL, files=files)
                            
                            if response.status_code == 200:
                                print(f"  ✅ Successfully uploaded {att.filename} to the API.")
                                # Email-ti ke "seen" mark kora, jate abar process na hoy
                                mailbox.seen([msg.uid], True)
                            else:
                                print(f"  ❌ Error uploading file. API response: {response.status_code} - {response.text}")
                        except requests.exceptions.RequestException as e:
                            print(f"  ❌ Failed to connect to the API: {e}")
                        
                        # Temporary file-ti delete kora
                        os.remove(temp_filepath)

    except Exception as e:
        print(f"An error occurred: {e}")

# --- Main Loop ---
if __name__ == "__main__":
    print("Starting email watcher service...")
    while True:
        download_and_upload_attachments()
        print("Waiting for 30 seconds before checking again...")
        time.sleep(30) 