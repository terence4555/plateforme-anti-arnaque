from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignalementViewSet, upload_preuve

router = DefaultRouter()
router.register("", SignalementViewSet, basename="signalement")

urlpatterns = [
    path("upload/", upload_preuve, name="upload-preuve"),
    path("", include(router.urls)),
]
