from django.db import models
from shared.core_lib.category.models import Category

class Source(models.Model):
    netloc = models.CharField(max_length=255)
    #category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_name')
    path = models.CharField(max_length=255)
    depth = models.IntegerField(default=0)
    target = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        unique_together = ('netloc', 'path')
