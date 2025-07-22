from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from .models import Article

class ArticleListView(View):
    template_name = 'articles/article_list.html'

    def get(self, request):
        articles = Article.objects.all()
        return render(request, self.template_name, {'articles': articles})

    def post(self, request):
        # Delete link by id from form POST
        article_id = request.POST.get('article_id')
        if article_id:
            article = get_object_or_404(Article, id=article_id)
            article.delete()
        return redirect('article-list')
