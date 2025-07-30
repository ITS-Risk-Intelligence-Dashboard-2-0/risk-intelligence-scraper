from rest_framework import viewsets, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Article
from .serializers import ArticleSerializer
from web_scraper.gdrive.api import GoogleDriveService
from googleapiclient.errors import HttpError

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['url']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        drive_id = instance.drive_id

        if drive_id:
            drive_service = GoogleDriveService()
            if not drive_service.service:
                return Response({"detail": "Failed to connect to Google Drive service."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            try:
                success = drive_service.delete_file(drive_id)
                if success:
                    self.perform_destroy(instance)
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    # This 'else' case is for non-HttpError failures from our service
                    return Response({"detail": "Google Drive reported a failure during file deletion."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            except HttpError as e:
                if e.resp.status == 404:
                    return Response(
                        {"detail": f"The file with ID '{drive_id}' was not found in Google Drive. This is likely a permissions issue. Please ensure the service account email is a 'Content manager' on the Shared Drive, as 'Contributor' is not sufficient for deletion."},
                        status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    return Response({"detail": f"A Google Drive API error occurred: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            except Exception as e:
                # Handle exceptions during the API call (e.g., network issues)
                return Response(
                    {"detail": f"An error occurred while communicating with Google Drive: {e}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # If there's no drive_id, just delete the local record
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
