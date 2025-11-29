"""Extracteur de profil minimal pour réduire la consommation de tokens."""

from typing import Any


def extract_minimal_profile(full_profile: dict) -> dict[str, Any]:
    """
    Extrait uniquement les champs du profil utilisés pour le matching.

    Réduit la taille du profil de ~300-500 tokens à ~100-150 tokens.

    Args:
        full_profile: Le profil complet chargé depuis profil.yaml

    Returns:
        Dictionnaire contenant uniquement les champs nécessaires au matching:
        - mots_cles_positifs: liste des mots-clés à favoriser
        - mots_cles_negatifs: liste des mots-clés à éviter
        - domaines: domaines d'intérêt (principaux et secondaires)
        - localisation: préférences de localisation
        - competences: liste aplatie de toutes les compétences techniques
    """
    # Extraire les compétences techniques (toutes catégories aplaties)
    competences = []
    competences_tech = full_profile.get("competences_techniques", {})
    for categorie, items in competences_tech.items():
        if isinstance(items, list):
            competences.extend(items)

    # Extraire les domaines d'intérêt
    domaines_interet = full_profile.get("domaines_interet", {})

    # Extraire les préférences de localisation
    criteres_these = full_profile.get("criteres_these", {})
    localisation = criteres_these.get("localisation", {})

    # Construire le profil minimal
    minimal_profile = {
        "mots_cles_positifs": full_profile.get("mots_cles_positifs", []),
        "mots_cles_negatifs": full_profile.get("mots_cles_negatifs", []),
        "domaines_interet": {
            "principaux": domaines_interet.get("principaux", []),
            "secondaires": domaines_interet.get("secondaires", [])
        },
        "localisation": {
            "preferences": localisation.get("preferences", []),
            "acceptables": localisation.get("acceptables", [])
        },
        "competences": competences
    }

    return minimal_profile


def add_cache_metadata(minimal_profile: dict) -> str:
    """
    Ajoute des métadonnées pour signaler à Claude de cacher ce profil.

    Args:
        minimal_profile: Le profil minimal extrait

    Returns:
        Message formaté avec le profil et les instructions de cache
    """
    import json

    profile_json = json.dumps(minimal_profile, ensure_ascii=False, indent=2)

    message = f"""# PROFIL CANDIDAT (À CACHER POUR TOUS LES APPELS SUIVANTS)

Ce profil contient les critères de matching. Vous pouvez le cacher dans votre contexte
et le réutiliser pour tous les appels à 'analyser_offre' sans le recharger.

{profile_json}

---
REMARQUE: Ce profil est optimisé pour réduire la consommation de tokens.
Il contient uniquement les champs utilisés par l'analyseur de matching.
"""

    return message
