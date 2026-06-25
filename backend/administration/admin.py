from django.contrib import admin
from .models import JournalAudit

@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ["id_audit", "table_cible", "action", "id_utilisateur", "date_action"]
    list_filter = ["table_cible", "action"]
    ordering = ["-date_action"]
