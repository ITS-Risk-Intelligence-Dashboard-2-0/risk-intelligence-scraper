from django.db import models

class Category(models.Model):
    category_name = models.CharField(max_length=255, primary_key=True)
    min_relevance_threshold = models.FloatField()

    
    def __str__(self):
        return self.category_name
