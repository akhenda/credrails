from rest_framework.routers import DefaultRouter

from .views import ReconciliationViewSet

app_name = 'api'

router = DefaultRouter()
router.register(r'reconciliation', ReconciliationViewSet, basename='reconciliation')

urlpatterns = router.urls
