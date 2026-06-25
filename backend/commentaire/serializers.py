from rest_framework import serializers
from .models import Commentaire


class CommentaireSerializer(serializers.ModelSerializer):
    auteur_nom = serializers.SerializerMethodField()

    class Meta:
        model = Commentaire
        fields = [
            "id_commentaire", "id_signalement", "id_utilisateur",
            "auteur_nom", "contenu", "est_masque", "date_commentaire",
        ]
        read_only_fields = ["id_commentaire", "auteur_nom", "est_masque", "date_commentaire"]

    def get_auteur_nom(self, obj):
        return f"{obj.id_utilisateur.prenom} {obj.id_utilisateur.nom}"


class CommentaireCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commentaire
        fields = ["id_signalement", "contenu"]
