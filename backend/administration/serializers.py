from rest_framework import serializers
from .models import JournalAudit


class JournalAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalAudit
        fields = ["id_audit", "table_cible", "action", "id_utilisateur", "date_action", "details"]
        read_only_fields = fields
