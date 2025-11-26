#!/usr/bin/env python3
"""
Script d'automatisation des candidatures Notion
- Si une candidature est "Envoyée" depuis plus de 10 jours, elle passe en "À relancer"
- Si une date d'entretien est dépassée, le statut passe à "Entretien passé"
"""

import os
from notion_client import Client
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# ============== CONFIGURATION ==============
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")

# Nombre de jours avant relance
JOURS_AVANT_RELANCE = 10
# ===========================================


def get_entreprise_name(candidature):
    """Récupère le nom de l'entreprise d'une candidature."""
    entreprise_prop = candidature["properties"].get("Entreprise", {})
    titre = entreprise_prop.get("title", [])
    return titre[0]["plain_text"] if titre else "Sans nom"


def get_date_property(candidature, property_name):
    """Récupère une date depuis une propriété de candidature."""
    date_prop = candidature["properties"].get(property_name, {})
    date_info = date_prop.get("date")

    if not date_info or not date_info.get("start"):
        return None

    return parser.parse(date_info["start"])


def normalize_datetime(dt, reference_dt=None):
    """Normalise un datetime pour le rendre comparable (gestion timezone)."""
    if reference_dt is None:
        reference_dt = datetime.now()

    # Si dt n'a pas de timezone, on retire aussi la timezone de reference_dt
    if dt.tzinfo is None:
        return dt, reference_dt.replace(tzinfo=None)
    else:
        return dt, reference_dt


def update_status(notion, page_id, new_status):
    """Met à jour le statut d'une page Notion."""
    notion.pages.update(
        page_id=page_id,
        properties={"Statut": {"status": {"name": new_status}}}
    )


def process_candidatures_a_relancer(notion):
    """
    Traite les candidatures 'Envoyée' datant de plus de JOURS_AVANT_RELANCE jours
    et les passe en statut 'À relancer'.
    """
    date_limite = datetime.now() - timedelta(days=JOURS_AVANT_RELANCE)

    print(f"🔍 Recherche des candidatures 'Envoyée' datant de plus de {JOURS_AVANT_RELANCE} jours...")
    print(f"   (Date limite : {date_limite.strftime('%d/%m/%Y')})")
    print()

    # Requête pour récupérer les candidatures avec statut "Envoyée"
    response = notion.data_sources.query(
        data_source_id=DATABASE_ID,
        filter={"property": "Statut", "status": {"equals": "Envoyée"}},
    )

    candidatures = response.get("results", [])
    print(f"📋 {len(candidatures)} candidature(s) avec statut 'Envoyée' trouvée(s)")
    print()

    mises_a_jour = 0

    for candidature in candidatures:
        nom_entreprise = get_entreprise_name(candidature)
        date_candidature = get_date_property(candidature, "Date de candidature")

        if not date_candidature:
            print(f"⚠️  {nom_entreprise} : Pas de date de candidature, ignorée")
            continue

        # Normaliser les dates pour comparaison
        date_candidature_norm, date_limite_norm = normalize_datetime(date_candidature, date_limite)

        # Vérifier si la date dépasse la limite
        if date_candidature_norm < date_limite_norm:
            print(f"🔄 {nom_entreprise} : Candidature du {date_candidature.strftime('%d/%m/%Y')} → À relancer")
            update_status(notion, candidature["id"], "À relancer")
            mises_a_jour += 1
        else:
            jours_restants = (date_candidature_norm - date_limite_norm).days
            print(f"✅ {nom_entreprise} : Candidature du {date_candidature.strftime('%d/%m/%Y')} → OK (encore {jours_restants} jour(s))")

    print()
    return mises_a_jour


def process_entretiens_passes(notion):
    """
    Traite les candidatures dont la date d'entretien est dépassée
    et les passe en statut 'Entretien passé'.
    """
    aujourd_hui = datetime.now()

    print("🔍 Recherche des entretiens passés...")
    print(f"   (Date actuelle : {aujourd_hui.strftime('%d/%m/%Y')})")
    print()

    # Requête pour récupérer toutes les candidatures (on filtrera après)
    # Note: on pourrait filtrer sur les statuts pertinents si connus
    response = notion.data_sources.query(
        data_source_id=DATABASE_ID,
    )

    candidatures = response.get("results", [])
    mises_a_jour = 0
    entretiens_trouves = 0

    for candidature in candidatures:
        nom_entreprise = get_entreprise_name(candidature)
        date_entretien = get_date_property(candidature, "Date d'entretien")

        if not date_entretien:
            continue

        entretiens_trouves += 1

        # Récupérer le statut actuel
        statut_prop = candidature["properties"].get("Statut", {})
        statut_actuel = statut_prop.get("status", {}).get("name", "")

        # Si déjà en "Entretien passé", on ignore
        if statut_actuel == "Entretien passé":
            continue

        # Normaliser les dates pour comparaison
        date_entretien_norm, aujourd_hui_norm = normalize_datetime(date_entretien, aujourd_hui)

        # Vérifier si la date d'entretien est dépassée
        if date_entretien_norm < aujourd_hui_norm:
            print(f"🔄 {nom_entreprise} : Entretien du {date_entretien.strftime('%d/%m/%Y')} → Entretien passé")
            update_status(notion, candidature["id"], "Entretien passé")
            mises_a_jour += 1
        else:
            jours_restants = (date_entretien_norm - aujourd_hui_norm).days
            print(f"📅 {nom_entreprise} : Entretien prévu le {date_entretien.strftime('%d/%m/%Y')} (dans {jours_restants} jour(s))")

    print(f"📋 {entretiens_trouves} candidature(s) avec date d'entretien trouvée(s)")
    print()
    return mises_a_jour


def main():
    """Fonction principale qui exécute toutes les automatisations."""
    # Initialiser le client Notion
    notion = Client(auth=NOTION_API_KEY)

    print("=" * 60)
    print("🤖 AUTOMATISATION DES CANDIDATURES NOTION")
    print("=" * 60)
    print()

    # Automatisation 1: Candidatures à relancer
    print("📌 AUTOMATISATION 1 : Candidatures à relancer")
    print("-" * 60)
    mises_a_jour_relance = process_candidatures_a_relancer(notion)

    # Automatisation 2: Entretiens passés
    print("📌 AUTOMATISATION 2 : Entretiens passés")
    print("-" * 60)
    mises_a_jour_entretiens = process_entretiens_passes(notion)

    # Résumé final
    total_mises_a_jour = mises_a_jour_relance + mises_a_jour_entretiens
    print("=" * 60)
    print("✨ RÉSUMÉ")
    print("=" * 60)
    print(f"   • Candidatures passées à 'À relancer' : {mises_a_jour_relance}")
    print(f"   • Candidatures passées à 'Entretien passé' : {mises_a_jour_entretiens}")
    print(f"   • Total de mises à jour : {total_mises_a_jour}")
    print("=" * 60)


if __name__ == "__main__":
    main()
