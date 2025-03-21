from django.http import HttpResponse
from django.template import loader
from rest_framework import viewsets
from rest_framework.response import Response

from .models import Book
from .serializers import BookSerializer


def welcome(request):
    template = loader.get_template('welcome.html')
    return HttpResponse(template.render())


# Create your views here.
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class ReconciliationViewSet(viewsets.ViewSet):
    def list(self, request, format=None):
        """
        List reconciliation results that were previously computed.
        Given more time, we could store results in a proper DB like Postgres or Redis.
        For assement purposes, we'll use in-memory or SQLite.
        """
        # This is just a placeholder for illustration.
        # Possibly read from a model or cache, then return.
        return Response(
            {'detail': "We'll come back to this if we have time."}, status=200
        )

    def create(self, request, format=None):
        """
        Accepts two CSV files, performs reconciliation, and returns the results
        in JSON, CSV, or HTML. The default format is JSON.
        """
        return Response({'detail': 'Not yet implemented'}, status=201)

    def retrieve(self, request, pk=None, format=None):
        """
        Download results that were previously computed. Given more time, we could store
        results in a proper DB like Postgres or Redis. For assement purposes, we'll use
        in-memory or SQLite.
        """
        # This is just a placeholder for illustration.
        # Possibly read from a model or cache, then return.
        return Response(
            {'detail': "We'll come back to this if we have time."}, status=200
        )
