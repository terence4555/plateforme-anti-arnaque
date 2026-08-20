from django.db import models


class ClusterEmergent(models.Model):
    """Groupe de signalements 'Incertain' détecté automatiquement par
    clustering (K-Means). Représente un phénomène potentiellement nouveau,
    non couvert par les 7 catégories connues, à valider par un modérateur."""

    mots_cles = models.CharField(
        max_length=500,
        help_text="Mots/expressions dominants du cluster (séparés par des virgules)"
    )
    nb_signalements = models.PositiveIntegerField(default=0)
    silhouette_score = models.FloatField(
        null=True, blank=True,
        help_text="Score de cohérence interne du clustering (plus proche de 1 = mieux)"
    )

    # Renseigné par un modérateur une fois le cluster examiné et confirmé
    # comme un vrai nouveau type d'arnaque (ou rejeté comme bruit).
    nom_valide = models.CharField(
        max_length=100, blank=True, null=True,
        help_text="Nom donné par un modérateur si ce cluster est confirmé comme nouvelle catégorie"
    )
    STATUT_CHOICES = [
        ("a_examiner", "À examiner"),
        ("confirme", "Confirmé comme nouvelle catégorie"),
        ("rejete", "Rejeté (bruit / faux positif)"),
    ]
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default="a_examiner")

    date_analyse = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_analyse"]

    def __str__(self):
        nom = self.nom_valide or "(non nommé)"
        return f"Cluster #{self.id} — {nom} ({self.nb_signalements} signalements)"


class Dossier(models.Model):
    """
    Un dossier d'infraction transmis à l'Autorité compétente, à partir d'un
    signalement jugé suffisamment sérieux par un modérateur. Couvre les cas
    d'utilisation de l'acteur "Autorité compétente" du diagramme :
    consulter les dossiers, confirmer/infirmer la véracité, mettre à jour
    le statut du dossier.
    """

    signalement = models.OneToOneField(
        "Signalement", on_delete=models.CASCADE, related_name="dossier"
    )

    STATUT_CHOICES = [
        ("recu", "Reçu"),
        ("en_examen", "En cours d'examen"),
        ("transmis_police", "Transmis à la police / justice"),
        ("classe_sans_suite", "Classé sans suite"),
        ("resolu", "Résolu"),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="recu")

    VERACITE_CHOICES = [
        ("non_examine", "Non examinée"),
        ("confirme", "Confirmée : c'est une arnaque"),
        ("infirme", "Infirmée : signalement non fondé"),
    ]
    veracite = models.CharField(max_length=15, choices=VERACITE_CHOICES, default="non_examine")

    commentaire_autorite = models.TextField(
        blank=True,
        help_text="Notes de l'autorité compétente sur ce dossier"
    )

    date_transmission = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_transmission"]

    def __str__(self):
        return f"Dossier #{self.id} — signalement #{self.signalement_id} ({self.get_statut_display()})"


class Signalement(models.Model):
    """Un signalement d'arnaque soumis par un utilisateur, avec la prédiction
    du modèle et le score de risque calculé au moment de la soumission."""

    texte = models.TextField(verbose_name="Texte du signalement")

    categorie_predite = models.CharField(max_length=50)
    confiance = models.FloatField(help_text="Confiance du modèle (0 à 1)")

    # Boucle de correction humaine : un modérateur peut corriger la
    # catégorie via l'admin Django. Sert de base pour un ré-entraînement
    # périodique du modèle.
    categorie_corrigee = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Renseigné par un modérateur si la prédiction était fausse"
    )

    score_risque = models.FloatField()
    canal_detecte = models.CharField(max_length=30, blank=True)

    campagne_detectee = models.BooleanField(default=False)
    signalements_lies = models.PositiveIntegerField(
        default=0,
        help_text="Nombre d'autres signalements partageant le même numéro/lien"
    )

    cluster_emergent = models.ForeignKey(
        ClusterEmergent, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="signalements",
        help_text="Renseigné automatiquement si ce signalement 'Incertain' a été rattaché à un cluster émergent"
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"#{self.id} [{self.categorie_predite}] {self.texte[:50]}"


class EntiteSignalement(models.Model):
    """Entité extraite d'un signalement (téléphone ou lien), stockée
    séparément pour permettre une détection de campagne fiable par requête
    SQL, plutôt qu'un état en mémoire qui disparaîtrait au redémarrage du
    serveur ou serait incohérent entre plusieurs workers."""

    TYPE_CHOICES = [
        ("telephone", "Téléphone"),
        ("lien", "Lien"),
    ]

    signalement = models.ForeignKey(
        Signalement, on_delete=models.CASCADE, related_name="entites"
    )
    type_entite = models.CharField(max_length=15, choices=TYPE_CHOICES)
    valeur = models.CharField(max_length=255, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["type_entite", "valeur"])]

    def __str__(self):
        return f"{self.type_entite}: {self.valeur}"
class Signalement(models.Model):
    TYPE_CHOICES = [
        ("faux_vendeur", "Faux vendeur"),
        ("phishing", "Hameconnage (phishing)"),
        ("usurpation_identite", "Usurpation d'identite"),
        ("produit_non_livre", "Produit non livre"),
        ("autre", "Autre type d'arnaque"),
    ]
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("approuve", "Approuve"),
        ("rejete", "Rejete"),
        ("transmis", "Transmis a l'autorite"),
        ("confirme", "Confirme par l'autorite"),
        ("infirme", "Infirme par l'autorite"),
    ]

    id_signalement = models.AutoField(primary_key=True)
    id_utilisateur = models.ForeignKey(
        "users.User", on_delete=models.CASCADE,
        db_column="id_utilisateur", related_name="signalements",
    )
    numero_telephone = models.CharField(max_length=20, blank=True, null=True)
    profil_vendeur = models.CharField(max_length=100, blank=True, null=True)
    type_arnaque = models.CharField(max_length=30, choices=TYPE_CHOICES)
    description = models.TextField()
    date_signalement = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default="en_attente")
    score = models.PositiveSmallIntegerField(default=100)

    class Meta:
        db_table = "Signalement"
        managed = False
        ordering = ["-date_signalement"]

    def __str__(self):
        identifiant = self.profil_vendeur or self.numero_telephone or f"#{self.id_signalement}"
        return f"{self.get_type_arnaque_display()} - {identifiant}"


class Preuve(models.Model):
    TYPE_CHOICES = [("image", "Image"), ("pdf", "PDF"), ("document", "Document")]

    id_preuve = models.AutoField(primary_key=True)
    id_signalement = models.ForeignKey(
        Signalement, on_delete=models.CASCADE,
        db_column="id_signalement", related_name="preuves",
    )
    fichier_url = models.CharField(max_length=300)
    type_fichier = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Preuve"
        managed = False
        ordering = ["date_upload"]

    def __str__(self):
        return f"Preuve {self.id_preuve} - Signalement #{self.id_signalement_id}"
