import os
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

class GoogleDriveService:
    """A service class to encapsulate all Google Drive API interactions."""

    def __init__(self, service_account_file='./risk-intel-db-f19a1b90a785.json'):
        self.service = self._authenticate(service_account_file)

    def _authenticate(self, sa_file):
        """Authenticates with the Google Drive API using a service account."""
        scopes = ['https://www.googleapis.com/auth/drive']
        try:
            creds = service_account.Credentials.from_service_account_file(sa_file, scopes=scopes)
            service = build('drive', 'v3', credentials=creds)
            print('Successfully authenticated with Google Drive API.')
            return service
        except Exception as e:
            print(f'Authentication failed: {e}')
            return None

    def find_folder(self, shared_drive_id, parent_id, folder_name):
        """Finds a folder by name within a parent and returns its ID."""
        if not self.service: return None
        try:
            q = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
            response = self.service.files().list(
                q=q,
                corpora="drive",
                driveId=shared_drive_id, # This should be the top-level Shared Drive ID
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields='files(id)'
            ).execute()
            files = response.get('files', [])
            return files[0].get('id') if files else None
        except HttpError as e:
            print(f"An error occurred while finding folder '{folder_name}': {e}")
            return None

    def find_or_create_folder(self, parent_id, folder_name):
        """Finds a folder by name within a parent, creates it if it doesn't exist."""
        # Note: For this method, parent_id is assumed to be the Shared Drive ID for top-level folders
        folder_id = self.find_folder(parent_id, parent_id, folder_name)
        if folder_id:
            return folder_id
        
        # If not found, create it
        if not self.service: return None
        try:
            file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
            folder = self.service.files().create(body=file_metadata, supportsAllDrives=True, fields='id').execute()
            return folder.get('id')
        except HttpError as e:
            print(f"An error occurred while creating folder '{folder_name}': {e}")
            return None

    def list_drive_contents(self, drive_id):
        """Lists all files and folders in the root of a specific Shared Drive."""
        if not self.service: return None
        try:
            print(f"\n--- Listing Contents of Shared Drive (ID: {drive_id}) ---")
            response = self.service.files().list(
                corpora="drive",
                driveId=drive_id,
                q=f"'{drive_id}' in parents and trashed=false",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields='files(id, name, mimeType)'
            ).execute()
            files = response.get('files', [])
            return files
        except HttpError as e:
            print(f"An error occurred while listing drive contents: {e}")
            return []

    def empty_folder(self, shared_drive_id, folder_id):
        """Finds all files and subfolders in a folder and deletes them."""
        if not self.service: return False
        try:
            print(f"--- Emptying contents of folder (ID: {folder_id}) ---")
            response = self.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                corpora="drive",
                driveId=shared_drive_id, # CRITICAL FIX: Use the correct Shared Drive ID
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields='files(id, name)'
            ).execute()
            
            files = response.get('files', [])
            if not files:
                print("Folder is already empty.")
                return True

            for file in files:
                print(f"  - Deleting '{file.get('name')}' (ID: {file.get('id')})")
                self.delete_file(file.get('id'))
            
            print("Successfully emptied folder.")
            return True
        except HttpError as e:
            print(f"An error occurred while emptying folder: {e}")
            return False

    def upload_file(self, folder_id, file_name, file_content, mimetype='application/pdf'):
        """
        Uploads a file to a specific Google Drive folder.
        Can handle both a local file path and an in-memory BytesIO object.
        """
        if not self.service: return None
        
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = None
        
        if isinstance(file_content, str) and os.path.exists(file_content):
            # It's a file path
            media = MediaFileUpload(file_content, mimetype=mimetype)
        elif isinstance(file_content, BytesIO):
            # It's an in-memory file
            media = MediaIoBaseUpload(file_content, mimetype=mimetype)
        else:
            print("Error: file_content must be a valid file path or a BytesIO object.")
            return None
            
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                supportsAllDrives=True,
                fields='id'
            ).execute()
            print(f"File '{file_name}' uploaded successfully. File ID: {file.get('id')}")
            return file.get('id')
        except HttpError as e:
            print(f"An error occurred during file upload: {e}")
            return None

    def get_file_metadata(self, file_id, fields='id, name, parents'):
        """Gets metadata for a specific file to check for its existence and permissions."""
        if not self.service: return None
        try:
            # supportsAllDrives is crucial for this to work in Shared Drives
            file = self.service.files().get(fileId=file_id, supportsAllDrives=True, fields=fields).execute()
            return file
        except HttpError as e:
            # Return the error object itself for inspection
            return e

    def delete_file(self, file_id):
        """Deletes a file from Google Drive by its file ID."""
        if not self.service: return False

        print(self.get_file_metadata(file_id))
        try:
            # supportsAllDrives=True is CRITICAL for operating on files in Shared Drives
            self.service.files().update(
                fileId=file_id,
                body={'trashed': True},
                supportsAllDrives=True
            ).execute()
            print(f"File or folder with ID '{file_id}' successfully deleted from Google Drive.")
            return True
        except HttpError as e:
            # Gracefully handle cases where the file is already gone or permissions are wrong
            if e.resp.status == 404:
                print(f"Warning: The file/folder with ID '{file_id}' was not found. This can happen if it was already deleted, or if you are trying to delete a folder without 'Content manager' permissions on the Shared Drive.")
                # We return True so that the calling script can continue, e.g., to recreate the folder.
                return True
            print(f"An error occurred while deleting file ID '{file_id}': {e}")
            return False
