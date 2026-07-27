# -*- coding: utf-8 -*-
"""
preprocessing.py
-----------------
Nettoyage de texte + extraction d'entités (numéros de téléphone, liens,
montants) à partir des signalements bruts.

L'extraction d'entités par regex est volontairement séparée du modèle NLP :
- elle sert à la détection de campagne (regrouper les signalements qui
  partagent le même numéro/lien, ce qui est beaucoup plus fiable qu'une
  similarité de texte) ;
- elle peut aussi nourrir le score de risque (ex: présence d'un lien suspect).
"""

import re

# ---------------------------------------------------------------------------
# Regex d'extraction d'entités
# ---------------------------------------------------------------------------

PHONE_RE = re.compile(r"(?:\+228\s?)?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}\b")
URL_RE = re.compile(
    r"\b(?:https?://)?(?:www\.)?[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b"
)
# Un montant doit soit contenir un séparateur de milliers (ex: 500 000,
# 1.500.000), soit être suivi explicitement de FCFA/francs. Ça évite de
# capturer des bouts de numéros de téléphone ou de liens comme "228".
AMOUNT_RE = re.compile(
    r"\d{1,3}(?:[ .]\d{3})+\s?(?:FCFA|F\s?CFA|francs?)?|\d+\s?(?:FCFA|F\s?CFA|francs?)"
)

# Mots-clés qui indiquent qu'un "nombre.point" trouvé est bien une URL et pas
# un artefact (évite de capturer des montants comme "500.000" comme URL)
URL_TLD_WHITELIST = {"com", "net", "org", "io", "online", "tg", "fr"}


def extract_entities(text: str) -> dict:
    """Extrait téléphones, liens et montants d'un texte de signalement."""
    phones = PHONE_RE.findall(text)
    urls = [
        u for u in URL_RE.findall(text)
        if u.split(".")[-1].lower() in URL_TLD_WHITELIST
    ]

    # On retire d'abord téléphones et liens du texte avant de chercher les
    # montants, pour ne pas confondre des chiffres de numéro/lien avec un
    # montant en FCFA.
    remainder = PHONE_RE.sub(" ", text)
    remainder = URL_RE.sub(" ", remainder)
    amounts = [a.strip() for a in AMOUNT_RE.findall(remainder) if a.strip()]

    return {
        "telephones": list(set(phones)),
        "liens": list(set(urls)),
        "montants": list(set(amounts)),
    }


# ---------------------------------------------------------------------------
# Nettoyage de texte pour le modèle NLP (TF-IDF)
# ---------------------------------------------------------------------------

# Petite liste de stopwords français + anglais courants (volontairement
# légère : on garde les mots porteurs de sens même très courts, utiles pour
# ce cas d'usage : "or", "vous", "il" etc. sont bien filtrés)
STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "de", "du", "et", "en", "je",
    "tu", "il", "elle", "on", "nous", "vous", "ils", "elles", "que", "qui",
    "avec", "pour", "dans", "sur", "au", "aux", "ce", "cette", "ces",
    "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa", "ses", "est",
    "être", "avoir", "a", "à", "ne", "pas", "plus", "se", "sont", "était",
    "the", "a", "an", "and", "of", "to", "in", "for", "is", "on", "with",
}


def clean_text(text: str) -> str:
    """
    Nettoyage léger avant vectorisation :
    - minuscule
    - remplace téléphones/liens/montants par des tokens génériques
      (le modèle apprend le PATTERN "il y a un lien suspect", pas le lien
      exact, ce qui généralise mieux à de nouveaux liens/numéros jamais vus)
    - retire la ponctuation
    - retire les stopwords très courants
    """
    text = text.lower()

    text = PHONE_RE.sub(" __telephone__ ", text)
    text = URL_RE.sub(" __lien__ ", text)
    text = AMOUNT_RE.sub(" __montant__ ", text)

    text = re.sub(r"[^\w\sàâäéèêëïîôöùûüç_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = [t for t in text.split() if t not in STOPWORDS]
    return " ".join(tokens)


if __name__ == "__main__":
    exemple = (
        "J'ai reçu un message sur WhatsApp d'une personne qui m'a dit être "
        "ingénieur en France, on a parlé pendant 2 mois, elle m'a demandé "
        "500 000 FCFA pour venir me rejoindre. Contact: +228 90 12 34 56, "
        "lien envoyé: promo-orange123.net"
    )
    print("Entités :", extract_entities(exemple))
    print("Texte nettoyé :", clean_text(exemple))
