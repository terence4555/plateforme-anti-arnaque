from django.contrib import admin
from .models import Signalement, Preuve

class PreuveInline(admin.TabularInline):
    model = Preuve
    extra = 0

@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ["id_signalement", "type_arnaque", "numero_telephone", "profil_vendeur", "statut", "score", "date_signalement"]
    list_filter = ["type_arnaque", "statut"]
    search_fields = ["numero_telephone", "profil_vendeur", "description"]
    ordering = ["-date_signalement"]
    inlines = [PreuveInline]

@admin.register(Preuve)
class PreuveAdmin(admin.ModelAdmin):
    list_display = ["id_preuve", "id_signalement", "type_fichier", "date_upload"]
