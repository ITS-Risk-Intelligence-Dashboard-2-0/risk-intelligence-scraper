from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Article
from .serializers import ArticleSerializer
from web_scraper.gdrive.api import delete_file_from_drive

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        drive_id = instance.drive_id

        if drive_id:
            try:
                success = delete_file_from_drive(drive_id)
                self.perform_destroy(instance)
                if not success:
                    # Log but don't block deletion
                    print(f"Warning: Failed to delete file from Google Drive for drive_id={drive_id}")
            except Exception as e:
                # Log error but continue deletion anyway
                print(f"Error deleting file from Google Drive: {e}")

        # self.perform_destroy(instance) # if you want to delete locally regardless if the file is in drive
        return Response(status=status.HTTP_204_NO_CONTENT)
