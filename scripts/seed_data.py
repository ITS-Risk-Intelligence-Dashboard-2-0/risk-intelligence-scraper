
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
from web_scraper.gdrive.api import GoogleDriveService

# --- Configuration ---
SHARED_DRIVE_ID = os.environ.get("SHARED_DRIVE_ID", "YOUR_SHARED_DRIVE_ID")
TEST_DATA_FOLDER_NAME = "Test Data"
        
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
    filename = url.replace("https://www.", "").replace("http://www.", "").replace("/", "_") + ".pdf"
    return filename, buffer

def seed_data():
    """
    Main function to COMPLETELY WIPE and re-seed the database and Google Drive 
    with a fresh set of test articles in a new "Test Data" folder.
    """
    if SHARED_DRIVE_ID == "YOUR_SHARED_DRIVE_ID":
        print("\nERROR: SHARED_DRIVE_ID is not set. Please check your .env file.")
        return

    drive_service = GoogleDriveService()
    if not drive_service.service:
        print("Failed to authenticate with Google Drive. Aborting.")
        return

    print("--- Clearing All Test Data ---")
    
    # 1. Clear ALL articles from the database to prevent orphaned records.
    deleted_count, _ = Article.objects.all().delete()
    print(f"Deleted {deleted_count} articles from the database.")

    # 2. Find and DELETE the old "Test Data" folder from Google Drive.
    print(f"Searching for existing '{TEST_DATA_FOLDER_NAME}' folder to delete it...")
    # The parent for a top-level folder in a Shared Drive is the Shared Drive ID itself.
    old_folder_id = drive_service.find_folder(SHARED_DRIVE_ID, SHARED_DRIVE_ID, TEST_DATA_FOLDER_NAME)

    if old_folder_id:
        print(f"Found old folder (ID: {old_folder_id}). Deleting it now...")
        # The `delete_file` method works for folders as well.
        delete_success = drive_service.delete_file(old_folder_id)
        if delete_success:
            print("Old 'Test Data' folder deleted successfully.")
        else:
            print("Could not delete the old 'Test Data' folder. See previous errors for details. This can sometimes be a permissions issue.")
    else:
        print("No old 'Test Data' folder found. Skipping deletion.")

    # 3. Create a fresh "Test Data" folder.
    print(f"\n--- Creating New '{TEST_DATA_FOLDER_NAME}' Folder ---")
    test_folder_id = drive_service.find_or_create_folder(SHARED_DRIVE_ID, TEST_DATA_FOLDER_NAME)
    if not test_folder_id:
        print("Could not create the new 'Test Data' folder. Aborting.")
        return
    print(f"Successfully created new '{TEST_DATA_FOLDER_NAME}' folder with ID: {test_folder_id}")

    print("\n--- Seeding New Articles ---")
    for article_data in SAMPLE_ARTICLES:
        url = article_data["url"]
        print(f"  - Processing: {url}")
        filename, pdf_buffer = create_dummy_pdf(url)
        
        drive_id = drive_service.upload_file(test_folder_id, filename, pdf_buffer, 'application/pdf')
        if drive_id:
            Article.objects.create(
                url=url,
                drive_id=drive_id,
                approved=article_data["approved"],
                creation_date=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            print(f"    -> Successfully created article and uploaded to Drive with ID: {drive_id}")
        else:
            print(f"    -> Failed to upload file for {url}.")

    print("\n--- Seeding Process Finished ---")

if __name__ == "__main__":
    seed_data() 