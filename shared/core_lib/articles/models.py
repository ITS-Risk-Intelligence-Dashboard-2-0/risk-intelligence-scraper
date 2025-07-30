import uuid
from django.db import models

class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drive_id = models.CharField(max_length=100, blank=True, null=True)
    url = models.URLField()  # original url
    creation_date = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.url

    class Meta:
        db_table = 'articles'