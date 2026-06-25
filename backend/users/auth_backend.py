"""
Backend d'authentification : SHA256(mot_de_passe) puis SHA256(mot_de_passe + sel)
"""
import hashlib
from django.contrib.auth.backends import BaseBackend
from .models import User


class SHA256SaltBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        if not email or not password:
            return None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None

        if not user.est_actif:
            return None

        password_bytes = password.encode("utf-8")
        actual_hash = bytes(user.password)

        # Méthode 1 : SHA256(password) — données de test existantes
        if hashlib.sha256(password_bytes).digest() == actual_hash:
            return user

        # Méthode 2 : SHA256(password + sel) — nouvelles inscriptions
        salt_bytes = user.sel.bytes
        if hashlib.sha256(password_bytes + salt_bytes).digest() == actual_hash:
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
