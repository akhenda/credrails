from rest_framework.routers import DefaultRouter

from .views import BookViewSet, ReconciliationViewSet

router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'reconciliation', ReconciliationViewSet, basename='reconciliation')

urlpatterns = router.urls
