from rest_framework import serializers
from .models import ScoreSignalement


class ScoreSignalementSerializer(serializers.ModelSerializer):
    """Score de fiabilité — lecture seule, calculé automatiquement."""
    signalement_title = serializers.CharField(source="signalement.title", read_only=True)

    class Meta:
        model = ScoreSignalement
        fields = [
            "id", "signalement", "signalement_title",
            "fiabilite_score", "total_votes", "votes_utiles",
            "votes_dangereux", "total_commentaires",
            "last_calculated",
        ]
        read_only_fields = fields
