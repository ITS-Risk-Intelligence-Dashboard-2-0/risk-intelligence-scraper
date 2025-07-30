from django.db import models
from django.utils import timezone

class Source(models.Model):
    class TargetType(models.TextChoices):
        BOTH = "BOTH", "Both"
        PDF = "PDF", "PDFs Only"
        WEBSITE = "WEBSITE", "Websites Only"

    netloc = models.CharField(max_length=255)
    #category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_name')
    path = models.CharField(max_length=255)
    depth = models.IntegerField(default=0)
    target = models.CharField(
        max_length=10,
        choices=TargetType.choices,
        default=TargetType.BOTH,
        help_text="Specify what type of content to scrape from this source."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active sources will be used when the scraper is run."
    )
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.netloc + self.path

    class Meta:
        db_table = 'sources'
        unique_together = ('netloc', 'path')
# >>>>>>> main
