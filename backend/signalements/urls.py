from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignalementViewSet

router = DefaultRouter()
router.register("", SignalementViewSet, basename="signalement")

urlpatterns = [path("", include(router.urls))]
