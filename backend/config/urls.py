from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/signalements/", include("signalements.urls")),
    path("api/commentaires/", include("commentaire.urls")),
    path("api/votes/", include("votes.urls")),
    path("api/audit/", include("administration.urls")),
]
