from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/signalements/", include("signalements.urls")),
    path("api/commentaires/", include("commentaire.urls")),
    path("api/votes/", include("votes.urls")),
    path("api/admin/", include("administration.urls")),
    path("api/chat/", include("chatbot.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
