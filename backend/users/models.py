import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("role", "admin")
        extra.setdefault("est_actif", True)
        return self.create_user(email, password, **extra)

    def get_by_natural_key(self, email):
        return self.get(email=email)


class User(AbstractBaseUser):
    id_utilisateur = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    email = models.EmailField(max_length=150, unique=True)

    password = models.BinaryField(max_length=256, db_column="mot_de_passe_hash")
    last_login = models.DateTimeField(null=True, blank=True, db_column="derniere_connexion")
    sel = models.UUIDField()

    ROLE_CHOICES = (
        ("user", "Utilisateur"),
        ("admin", "Administrateur"),
        ("autorite", "Autorite competente"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")
    est_actif = models.BooleanField(default=True)
    date_inscription = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "prenom"]

    @property
    def is_staff(self):
        return self.role in ("admin", "autorite")

    @property
    def is_active(self):
        return self.est_actif

    @property
    def is_superuser(self):
        return self.role == "admin"

    @property
    def is_moderator(self):
        return self.role == "admin"

    @property
    def is_autorite(self):
        return self.role == "autorite"

    def set_password(self, raw_password):
        self.sel = self.sel or __import__("uuid").uuid4()
        self.password = hashlib.sha256(raw_password.encode() + self.sel.bytes).digest()

    def check_password(self, raw_password):
        actual = bytes(self.password)
        if hashlib.sha256(raw_password.encode()).digest() == actual:
            return True
        if hashlib.sha256(raw_password.encode() + self.sel.bytes).digest() == actual:
            return True
        return False

    def has_usable_password(self):
        return bool(self.password)

    def has_perm(self, perm, obj=None):
        return self.role in ("admin", "autorite")

    def has_module_perms(self, app_label):
        return self.role in ("admin", "autorite")

    class Meta:
        db_table = "Utilisateur"
        managed = False

    def __str__(self):
        return f"{self.prenom} {self.nom}"
