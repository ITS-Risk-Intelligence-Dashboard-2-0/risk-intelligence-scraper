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
                # Attempt to delete the file from Google Drive first
                success = delete_file_from_drive(drive_id)
                if success:
                    # If successful, proceed to delete the database record
                    self.perform_destroy(instance)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    # If Drive deletion fails, return an error and do NOT delete from DB
                    return Response(
                        {"detail": "Failed to delete file from Google Drive. The article was not deleted."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            except Exception as e:
                # Handle exceptions during the API call (e.g., network issues)
                return Response(
                    {"detail": f"An error occurred while communicating with Google Drive: {e}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # If there's no drive_id, just delete the local record
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
