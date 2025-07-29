
import os
import sys

# --- Setup to use Django environment and models ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')

from web_scraper.gdrive.api import GoogleDriveService

def diagnose_shared_drive():
    """
    Connects to Google Drive and lists all files/folders in the root
    of the configured Shared Drive to help identify orphaned files.
    """
    shared_drive_id = os.environ.get("SHARED_DRIVE_ID")
    if not shared_drive_id:
        print("ERROR: SHARED_DRIVE_ID is not set in your .env file. Cannot run diagnostics.")
        return

    drive_service = GoogleDriveService()
    if not drive_service.service:
        print("Failed to authenticate with Google Drive. Aborting.")
        return

    contents = drive_service.list_drive_contents(shared_drive_id)

    if not contents:
        print("No files or folders found in the root of the Shared Drive.")
    else:
        print("Found the following items:")
        for item in contents:
            item_type = "Folder" if item.get('mimeType') == 'application/vnd.google-apps.folder' else "File"
            print(f"  - Name: '{item.get('name')}', ID: '{item.get('id')}', Type: {item_type}")
    
    print("\n--- Diagnostics Finished ---")
    print("Please compare this list with what you see in the Google Drive UI.")
    print("Manually delete any old, duplicate files or folders that should not be there.")

if __name__ == "__main__":
    diagnose_shared_drive() 