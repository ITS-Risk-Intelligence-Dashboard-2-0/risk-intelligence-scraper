import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# --- Configuration ---
SERVICE_ACCOUNT_FILE = '/Users/hrychen/Desktop/Google API/risk-intel-db-f19a1b90a785.json'
FOLDER_ID = '1-3cTCANoUdWEc-jTArx1Kpzy9cpmA5ad'
SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive.metadata.readonly']
# Added drive.metadata.readonly scope for listing purposes

# --- 1. Authenticate with Google Drive API ---
def authenticate_drive():
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=creds)
        print('Successfully authenticated with Google Drive API.')
        return service
    except Exception as e:
        print(f'Authentication failed: {e}')
        return None

# --- DIAGNOSTIC FUNCTION: List Folder Contents ---
def list_folder_contents(service, folder_id):
    try:
        print(f"\nAttempting to list contents of folder ID: {folder_id}")
        # Query for files whose parents include the specified folder_id
        # 'q' parameter is used for search queries
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType)",
            pageSize=10
        ).execute()
        items = results.get('files', [])

        if not items:
            print(f"No files found in folder '{folder_id}' or folder is empty/inaccessible.")
        else:
            print(f"Files found in folder '{folder_id}':")
            for item in items:
                print(f"  - {item['name']} ({item['mimeType']}, ID: {item['id']})")
        return True
    except HttpError as error:
        print(f"HTTP Error when listing folder '{folder_id}': {error}")
        print(f"This likely means the service account cannot see or access this folder ID.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred while listing folder contents: {e}")
        return False

# --- Upload PDF to Google Drive (Unchanged from your last version) ---
def upload_pdf_to_drive(service, pdf_filename, folder_id):
    file_metadata = {
        'name': os.path.basename(pdf_filename),
        'parents': [folder_id],
        'mimeType': 'application/pdf'
    }
    media = MediaFileUpload(pdf_filename, mimetype='application/pdf')

    try:
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webContentLink'
        ).execute()
        print(f"PDF uploaded successfully! File ID: {file.get('id')}")
        print(f"Direct link: {file.get('webContentLink')}")
        return file.get('id')
    except HttpError as error: # Catch HttpError specifically
        print(f'An HTTP error occurred during upload: {error}')
        if error.resp.status == 404:
            print("Error details: The target folder was not found or accessible to the service account.")
        return None
    except Exception as e:
        print(f'An unexpected error occurred during upload: {e}')
        return None

# --- Main Execution ---
if __name__ == '__main__':
    # 1. Authenticate
    drive_service = authenticate_drive()

    if drive_service:
        # Diagnostic step: Try to list contents of the folder
        can_access_folder = list_folder_contents(drive_service, FOLDER_ID)

        if can_access_folder:
            print("\nProceeding with upload attempt...")
            # 2. Specify the path to your PDF file
            pdf_file_path = 'path/to/your/local/pdf/file.pdf'

            # 3. Upload the PDF
            uploaded_file_id = upload_pdf_to_drive(drive_service, pdf_file_path, FOLDER_ID)

            if uploaded_file_id:
                print('PDF upload complete.')
            else:
                print('PDF upload failed.')
        else:
            print("\nCannot proceed with upload as folder access failed during diagnostics.")
    else:
        print('Google Drive authentication failed.')