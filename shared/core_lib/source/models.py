from django.db import models
from django.utils import timezone

class Source(models.Model):
    """
    Represents a starting point for the web scraper.
    """
    class TargetType(models.TextChoices):
        BOTH = 'BOTH', 'Both'
        PDF = 'PDF', 'PDFs Only'
        WEBSITE = 'WEBSITE', 'Websites Only'

    # Reverted to a standard AutoField to avoid migration errors with existing data.
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="A user-friendly name for the source, e.g., 'Example News Site'.")
    url = models.URLField(max_length=2048, unique=True, help_text="The starting URL for the scraper.")
    target_type = models.CharField(
        max_length=10,
        choices=TargetType.choices,
        default=TargetType.BOTH,
        help_text="Specify what content to scrape from this source."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only active sources will be used when the scraper is run."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
