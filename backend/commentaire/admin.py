from django.contrib import admin
from .models import Commentaire

@admin.register(Commentaire)
class CommentaireAdmin(admin.ModelAdmin):
    list_display = ["id_commentaire", "id_signalement", "id_utilisateur", "contenu_preview", "est_masque", "date_commentaire"]
    list_filter = ["est_masque"]
    search_fields = ["contenu"]
    ordering = ["-date_commentaire"]

    def contenu_preview(self, obj):
        return obj.contenu[:80] + ("..." if len(obj.contenu) > 80 else "")
    contenu_preview.short_description = "Aperçu"
