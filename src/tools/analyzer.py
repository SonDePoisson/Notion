"""Outil d'analyse de correspondance entre offres et profil candidat."""

from typing import Any


def analyser_offre(offre: dict, profil: dict, settings: dict) -> dict[str, Any]:
    """
    Analyse une offre de thèse par rapport au profil du candidat.

    Args:
        offre: L'offre à analyser (titre, description, lieu, etc.)
        profil: Le profil du candidat
        settings: Les paramètres de configuration

    Returns:
        Dictionnaire contenant:
        - score: int (0-100)
        - justification: str
        - points_forts: list[str]
        - points_faibles: list[str]
    """
    score = 0
    points_forts = []
    points_faibles = []

    # Texte complet à analyser
    texte_offre = " ".join([
        offre.get("titre", ""),
        offre.get("description", ""),
        offre.get("labo", "")
    ]).lower()

    # 1. Analyse des mots-clés positifs
    mots_cles_positifs = profil.get("mots_cles_positifs", [])
    mots_trouves = [mot for mot in mots_cles_positifs if mot.lower() in texte_offre]

    if mots_trouves:
        bonus = min(len(mots_trouves) * 5, 40)  # Max 40 points
        score += bonus
        points_forts.append(f"Mots-clés pertinents trouvés: {', '.join(mots_trouves[:5])}")

    # 2. Analyse des mots-clés négatifs
    mots_cles_negatifs = profil.get("mots_cles_negatifs", [])
    mots_negatifs_trouves = [mot for mot in mots_cles_negatifs if mot.lower() in texte_offre]

    if mots_negatifs_trouves:
        malus = min(len(mots_negatifs_trouves) * 10, 30)
        score -= malus
        points_faibles.append(f"Domaines non souhaités: {', '.join(mots_negatifs_trouves)}")

    # 3. Analyse de la localisation
    lieu = offre.get("lieu", "").lower()

    # Support pour profil minimal (localisation directement dans profil)
    # ou profil complet (localisation dans criteres_these)
    if "localisation" in profil:
        localisation = profil["localisation"]
    else:
        criteres_these = profil.get("criteres_these", {})
        localisation = criteres_these.get("localisation", {})

    preferences = [v.lower() for v in localisation.get("preferences", [])]
    acceptables = [v.lower() for v in localisation.get("acceptables", [])]

    if any(pref in lieu for pref in preferences):
        score += 20
        points_forts.append(f"Localisation préférée: {offre.get('lieu', 'Non spécifié')}")
    elif any(acc in lieu for acc in acceptables):
        score += 10
        points_forts.append(f"Localisation acceptable: {offre.get('lieu', 'Non spécifié')}")
    elif lieu:
        score -= 5
        points_faibles.append(f"Localisation non prioritaire: {offre.get('lieu', 'Non spécifié')}")

    # 4. Bonus pour les compétences techniques
    # Support pour profil minimal (competences en liste aplatie)
    # ou profil complet (competences_techniques en dict)
    if "competences" in profil and isinstance(profil["competences"], list):
        toutes_competences = [c.lower() for c in profil["competences"]]
    else:
        competences = profil.get("competences_techniques", {})
        toutes_competences = []
        for categorie, items in competences.items():
            if isinstance(items, list):
                toutes_competences.extend([c.lower() for c in items])

    competences_trouvees = [comp for comp in toutes_competences if comp in texte_offre]

    if competences_trouvees:
        bonus = min(len(competences_trouvees) * 3, 20)
        score += bonus
        points_forts.append(f"Compétences requises correspondantes: {', '.join(competences_trouvees[:3])}")

    # 5. Bonus pour les domaines d'intérêt
    domaines = profil.get("domaines_interet", {})
    principaux = [d.lower() for d in domaines.get("principaux", [])]
    secondaires = [d.lower() for d in domaines.get("secondaires", [])]

    domaines_trouves_principaux = [d for d in principaux if d in texte_offre]
    domaines_trouves_secondaires = [d for d in secondaires if d in texte_offre]

    if domaines_trouves_principaux:
        score += 15
        points_forts.append(f"Domaine principal d'intérêt: {', '.join(domaines_trouves_principaux)}")
    elif domaines_trouves_secondaires:
        score += 8
        points_forts.append(f"Domaine secondaire d'intérêt: {', '.join(domaines_trouves_secondaires)}")

    # 6. S'assurer que le score est entre 0 et 100
    score = max(0, min(100, score))

    # 7. Générer la justification
    if score >= settings["matching"]["seuil_haute_priorite"]:
        justification = "🔥 Excellente correspondance avec votre profil ! Cette offre mérite une attention particulière."
    elif score >= settings["matching"]["seuil_suggestion"]:
        justification = "✅ Bonne correspondance. Cette offre pourrait vous intéresser."
    else:
        justification = "⚠️ Correspondance limitée. À évaluer avec attention."

    # Ajouter les détails
    if not points_forts:
        points_faibles.append("Peu de mots-clés pertinents trouvés dans l'offre")

    return {
        "score": score,
        "justification": justification,
        "points_forts": points_forts,
        "points_faibles": points_faibles if points_faibles else ["Aucun point faible identifié"]
    }
