from rest_framework import serializers
from .models import Signalement, Preuve


class PreuveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preuve
        fields = ["id_preuve", "fichier_url", "type_fichier", "date_upload"]
        read_only_fields = ["id_preuve", "date_upload"]


class SignalementListSerializer(serializers.ModelSerializer):
    """Liste allégée."""
    type_display = serializers.CharField(source="get_type_arnaque_display", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    auteur_nom = serializers.SerializerMethodField()

    class Meta:
        model = Signalement
        fields = [
            "id_signalement", "numero_telephone", "profil_vendeur",
            "type_arnaque", "type_display", "statut", "statut_display",
            "score", "auteur_nom", "date_signalement",
        ]
        read_only_fields = fields

    def get_auteur_nom(self, obj):
        return f"{obj.id_utilisateur.prenom} {obj.id_utilisateur.nom}"


class SignalementDetailSerializer(serializers.ModelSerializer):
    """Détail complet avec preuves."""
    type_display = serializers.CharField(source="get_type_arnaque_display", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    auteur_nom = serializers.SerializerMethodField()
    preuves = PreuveSerializer(many=True, read_only=True)
    votes_up = serializers.SerializerMethodField()
    votes_down = serializers.SerializerMethodField()
    commentaires_count = serializers.SerializerMethodField()

    class Meta:
        model = Signalement
        fields = [
            "id_signalement", "id_utilisateur", "auteur_nom",
            "numero_telephone", "profil_vendeur",
            "type_arnaque", "type_display",
            "description",
            "statut", "statut_display", "score",
            "preuves", "votes_up", "votes_down", "commentaires_count",
            "date_signalement",
        ]
        read_only_fields = ["id_signalement", "statut", "score", "date_signalement"]

    def get_auteur_nom(self, obj):
        return f"{obj.id_utilisateur.prenom} {obj.id_utilisateur.nom}"

    def get_votes_up(self, obj):
        return obj.votes.filter(type_vote="up").count()

    def get_votes_down(self, obj):
        return obj.votes.filter(type_vote="down").count()

    def get_commentaires_count(self, obj):
        return obj.commentaires.filter(est_masque=False).count()


class SignalementCreateSerializer(serializers.ModelSerializer):
    """Création d'un signalement."""
    class Meta:
        model = Signalement
        fields = [
            "numero_telephone", "profil_vendeur", "type_arnaque",
            "description",
        ]
