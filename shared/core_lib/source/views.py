from django.shortcuts import render
from rest_framework import viewsets
from .models import Source
from .serializers import SourceSerializer

# Create your views here.

class SourceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sources to be viewed or edited.
    """
    queryset = Source.objects.all().order_by('name')
    serializer_class = SourceSerializer
