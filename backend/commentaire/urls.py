from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentaireViewSet

router = DefaultRouter()
router.register("", CommentaireViewSet, basename="commentaire")

urlpatterns = [path("", include(router.urls))]
