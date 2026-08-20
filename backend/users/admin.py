from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["id_utilisateur", "email", "nom", "prenom", "role", "est_actif", "date_inscription"]
    list_filter = ["role", "est_actif"]
    search_fields = ["email", "nom", "prenom"]
    ordering = ["-date_inscription"]
