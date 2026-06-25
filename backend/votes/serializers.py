from rest_framework import serializers
from .models import Vote


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ["id_vote", "id_signalement", "id_utilisateur", "type_vote", "date_vote"]
        read_only_fields = ["id_vote", "id_utilisateur", "date_vote"]


class VoteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ["id_signalement", "type_vote"]
