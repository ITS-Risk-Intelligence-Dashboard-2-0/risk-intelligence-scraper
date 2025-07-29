
import os
import sys
import django
from django.utils import timezone
from datetime import timedelta
import random
from io import BytesIO
from googleapiclient.http import MediaIoBaseUpload

# --- Django Setup ---
# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from shared.core_lib.articles.models import Article
from web_scraper.gdrive.api import authenticate_drive

# --- Configuration ---
# IMPORTANT: Replace this with your actual Shared Drive ID
SHARED_DRIVE_ID = os.environ.get("SHARED_DRIVE_ID", "YOUR_SHARED_DRIVE_ID")
TEST_DATA_FOLDER_NAME = "Test Data"

# --- Helper Functions for GDrive (moved here for script self-sufficiency) ---
def find_or_create_folder(service, parent_id, folder_name):
    """Finds a folder by name within a parent, creates it if not found."""
    try:
        q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
        response = service.files().list(q=q, corpora="drive", driveId=parent_id, includeItemsFromAllDrives=True, supportsAllDrives=True, fields='files(id, name)').execute()
        files = response.get('files', [])
        if files:
            return files[0].get('id')
        else:
            file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
            folder = service.files().create(body=file_metadata, supportsAllDrives=True, fields='id').execute()
            return folder.get('id')
    except Exception as e:
        print(f"An error occurred in find_or_create_folder: {e}")
        return None

def upload_file_to_folder(service, folder_id, filename, file_buffer, mimetype):
    """Uploads an in-memory file buffer to a specific Google Drive folder."""
    try:
        file_metadata = {'name': filename, 'parents': [folder_id]}
        media = MediaIoBaseUpload(file_buffer, mimetype=mimetype, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, supportsAllDrives=True, fields='id').execute()
        return file.get('id')
    except Exception as e:
        print(f"An error occurred during file upload: {e}")
        return None
        
# --- Sample Data ---
SAMPLE_ARTICLES = [
    {"url": "https://www.example-news.com/breaking-story-one", "approved": True},
    {"url": "https://www.tech-updates.com/new-gadget-review", "approved": False},
    {"url": "https://www.finance-insights.com/market-trends-2024", "approved": True},
    {"url": "https://www.health-and-wellness.com/5-tips-for-a-better-sleep", "approved": False},
    {"url": "https://www.sports-daily.com/championship-recap", "approved": True},
]

def create_dummy_pdf(url):
    """Creates a simple PDF file in memory for testing purposes."""
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, f"This is a test PDF for the article at:")
    p.drawString(100, 735, url)
    p.showPage()
    p.save()
    buffer.seek(0)
    
    # Sanitize URL to create a valid filename
    filename = url.replace("https://www.", "").replace("http://www.", "").replace("/", "_") + ".pdf"
    return filename, buffer

def clear_existing_test_data():
    """Deletes articles that seem to be test data to avoid duplicates."""
    print("Clearing previously seeded test data...")
    count = 0
    for article_data in SAMPLE_ARTICLES:
        deleted, _ = Article.objects.filter(url=article_data["url"]).delete()
        if deleted:
            count += 1
    print(f"Deleted {count} existing test articles from the database.")


def seed_data():
    """
    Main function to seed the database and Google Drive with test articles.
    """
    if SHARED_DRIVE_ID == "YOUR_SHARED_DRIVE_ID":
        print("\nERROR: SHARED_DRIVE_ID is not set. Please check your .env file.")
        return

    print("--- Starting Data Seeding Process ---")
    
    # 1. Clear out old test data to prevent duplicates
    clear_existing_test_data()

    # 2. Get Google Drive Service
    try:
        service = authenticate_drive()
        print("Successfully authenticated with Google Drive API.")
    except Exception as e:
        print(f"Error authenticating with Google Drive: {e}")
        return

    # 3. Find or Create the "Test Data" folder in the Shared Drive
    try:
        test_folder_id = find_or_create_folder(service, SHARED_DRIVE_ID, TEST_DATA_FOLDER_NAME)
        if not test_folder_id:
            print("Could not find or create the 'Test Data' folder. Aborting.")
            return
        print(f"Using test data folder with ID: {test_folder_id}")
    except Exception as e:
        print(f"Error managing Google Drive folder: {e}")
        return

    # 4. Create and upload articles
    print("\nSeeding articles...")
    for i, article_data in enumerate(SAMPLE_ARTICLES):
        url = article_data["url"]
        
        # Check if an article with this URL already exists
        if Article.objects.filter(url=url).exists():
            print(f"Skipping '{url}' as it already exists.")
            continue

        print(f"  - Processing: {url}")

        # Create a dummy PDF file
        filename, pdf_buffer = create_dummy_pdf(url)

        try:
            # Upload to Google Drive
            drive_id = upload_file_to_folder(service, test_folder_id, filename, pdf_buffer, "application/pdf")
            if drive_id:
                # Create the article in the database
                Article.objects.create(
                    url=url,
                    drive_id=drive_id,
                    approved=article_data["approved"],
                    # Make creation dates look more realistic by offsetting them
                    creation_date=timezone.now() - timedelta(days=random.randint(1, 30))
                )
                print(f"    -> Successfully created article and uploaded to Drive with ID: {drive_id}")
            else:
                print(f"    -> Failed to upload file for {url}.")
        except Exception as e:
            print(f"    -> An error occurred while processing {url}: {e}")

    print("\n--- Seeding Process Finished ---")

if __name__ == "__main__":
    # This allows the script to be run from the command line.
    seed_data() 