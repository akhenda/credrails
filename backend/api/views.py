from django.http import HttpResponse
from django.template import loader
from rest_framework import viewsets
from .models import Book
from .serializers import BookSerializer

# Create your views here.
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

def welcome(request):
    template = loader.get_template('welcome.html')
    return HttpResponse(template.render())
