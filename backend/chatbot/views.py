import re
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


FAQ = [
    {
        "keywords": ["signaler", "signalement", "arnaque", "arnaquer", "fraude", "signal"],
        "response": "Pour signaler une arnaque, allez sur la page \"Signaler\" en cliquant sur le bouton Remplissez le formulaire avec le numéro de téléphone ou le profil du vendeur, décrivez l'arnaque en détail et joignez des preuves (captures d'écran, reçus, etc.). Votre signalement sera examiné par nos modérateurs.",
    },
    {
        "keywords": ["compte", "inscription", "s'inscrire", "register", "créer un compte"],
        "response": "Pour créer un compte, rendez-vous sur la page \"S'inscrire\" en haut à droite de l'accueil. Vous aurez besoin d'une adresse email et d'un mot de passe d'au moins 8 caractères. L'inscription est gratuite et rapide.",
    },
    {
        "keywords": ["connexion", "connecter", "login", "mot de passe", "oublié", "perdu"],
        "response": "Pour vous connecter, utilisez votre adresse email et votre mot de passe sur la page de connexion. Si vous avez oublié votre mot de passe, contactez un administrateur pour réinitialisation.",
    },
    {
        "keywords": ["preuve", "preuves", "image", "photo", "capture", "screenshot", "pdf", "document", "upload", "fichier"],
        "response": "Lors de la création d'un signalement, vous pouvez joindre des preuves en cliquant sur la zone de dépôt dans la section \"Preuves\". Formats acceptés : images (JPG, PNG, GIF) et PDF. Taille maximale : 10 Mo par fichier.",
    },
    {
        "keywords": ["vote", "voter", "confirmer", "refuser", "utile", "pas utile"],
        "response": "Vous pouvez voter sur un signalement pour indiquer si vous le confirmez ou non. Cliquez sur ♥ \"Confirme\" ou ✕ \"Je refuse\" sur la page de détail d'un signalement. Les votes aident à évaluer la crédibilité des signalements.",
    },
    {
        "keywords": ["commentaire", "commenter", "répondre", "discussion"],
        "response": "Vous pouvez laisser des commentaires sur les signalements pour partager votre expérience ou apporter des informations complémentaires. Utilisez la section \"Commentaires\" en bas de la page de détail d'un signalement.",
    },
    {
        "keywords": ["profil", "modifier", "compte", "informations", "nom", "email"],
        "response": "Pour modifier vos informations de compte, allez sur votre page profil en cliquant sur votre prénom dans la barre de navigation. Cliquez ensuite sur \"Modifier\" dans la section \"Information sur le compte\".",
    },
    {
        "keywords": ["vérifier", "verifier", "numéro", "téléphone", "vendeur", "cherche", "recherche"],
        "response": "Pour vérifier un vendeur ou un numéro de téléphone, utilisez la barre de recherche sur la page d'accueil. Entrez le numéro ou le profil du vendeur et cliquez sur \"Vérifier\". Vous verrez tous les signalements associés.",
    },
    {
        "keywords": ["score", "crédibilité", "credibilite", "fiabilité", "fiabilite"],
        "response": "Le score d'un signalement (0-100) est calculé automatiquement en fonction des votes, du statut et du type d'arnaque. Un score élevé indique un signalement plus fiable.",
    },
    {
        "keywords": ["statut", "état", "en attente", "approuvé", "rejeté", "transmis", "confirmé"],
        "response": "Les statuts d'un signalement sont : En attente (soumis), Approuvé (validé par un admin), Rejeté, Transmis (envoyé aux autorités), Confirmé (par les autorités) ou Infirmé. Vous pouvez suivre l'évolution sur la page de détail.",
    },
    {
        "keywords": ["autorité", "autorite", "police", "gendarmerie", "justice"],
        "response": "Les signalements approuvés par les administrateurs peuvent être transmis aux autorités compétentes. Celles-ci examinent le dossier et confirment ou infirment l'arnaque.",
    },
    {
        "keywords": ["sécurité", "securite", "protéger", "protection", "arnaqueur", "escroc"],
        "response": "Pour vous protéger : vérifiez toujours le numéro du vendeur avant un achat, ne payez jamais d'avance sans preuve, méfiez-vous des prix trop bas, et consultez les signalements existants sur notre plateforme.",
    },
    {
        "keywords": ["bonjour", "salut", "hello", "hey", "bonsoir"],
        "response": "Bonjour ! 👋 Je suis l'assistant Anti-Arnaque. Comment puis-je vous aider ? Vous pouvez me poser des questions sur le signalement d'arnaque, la création de compte, les preuves, les votes, etc.",
    },
    {
        "keywords": ["merci", "thanks", "super", "génial", "parfait"],
        "response": "Avec plaisir ! N'hésitez pas si vous avez d'autres questions. Restez vigilant en ligne ! 🛡️",
    },
    {
        "keywords": ["aide", "help", "comment", "quoi", "besoin"],
        "response": "Je peux vous aider sur : signaler une arnaque, créer un compte, ajouter des preuves, voter, commenter, vérifier un vendeur, ou modifier votre profil. Posez-moi votre question !",
    },
]

DEFAULT_RESPONSE = "Je ne suis pas sûr de comprendre votre question. Voici ce que je peux vous aider avec :\n\n• Signaler une arnaque\n• Créer un compte\n• Ajouter des preuves\n• Voter sur un signalement\n• Vérifier un vendeur\n• Modifier votre profil\n\nEssayez de reformuler ou tapez un de ces mots-clés."


def find_response(message):
    msg = message.lower().strip()
    msg = re.sub(r'[^\w\sàâäéèêëïîôùûüÿçœæ]', '', msg)

    best_match = None
    best_score = 0

    for entry in FAQ:
        score = 0
        for kw in entry["keywords"]:
            if kw in msg:
                score += len(kw)
        if score > best_score:
            best_score = score
            best_match = entry

    if best_match and best_score > 0:
        return best_match["response"]
    return DEFAULT_RESPONSE


@api_view(["POST"])
@permission_classes([AllowAny])
def chat(request):
    message = request.data.get("message", "").strip()
    if not message:
        return Response({"error": "Le message ne peut pas être vide."}, status=400)

    response_text = find_response(message)
    return Response({"response": response_text})
