from rest_framework import serializers
from .models import User


class LoginSerializer(serializers.Serializer):
    """POST /api/auth/login/ — email + mot de passe."""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.ModelSerializer):
    """POST /api/auth/register/ — inscription."""
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["nom", "prenom", "email", "password"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Profil complet (connecté)."""
    signalements_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id_utilisateur", "nom", "prenom", "email",
            "role", "est_actif",
            "date_inscription", "last_login",
            "signalements_count",
        ]
        read_only_fields = ["id_utilisateur", "role", "date_inscription"]

    def get_signalements_count(self, obj):
        return obj.signalements.count()


class UserPublicSerializer(serializers.ModelSerializer):
    """Profil public — limité."""
    class Meta:
        model = User
        fields = ["id_utilisateur", "nom", "prenom", "date_inscription"]
        read_only_fields = fields

