from django.db import models
from shared.core_lib.articles.models import Article
from shared.core_lib.category.models import Category

class ArticleScore(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE, db_column='article_id')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, db_column='category_name')
    relevance_score = models.FloatField()

    class Meta:
        unique_together = ('article', 'category')
