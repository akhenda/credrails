from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookViewSet, ReconciliationDownloadView, ReconciliationView

router = DefaultRouter()
router.register(r'books', BookViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Endpoint for uploading the two CSV files and performing reconciliation
    path('reconcile/', ReconciliationView.as_view(), name='reconcile'),
    # Endpoint for downloading the final reconciliation result in a chosen format
    path(
        'reconcile/download/',
        ReconciliationDownloadView.as_view(),
        name='reconcile-download',
    ),
]
