"""Outil de création d'entrées dans Notion."""

from typing import Any

from notion_client import Client


async def creer_candidature_notion(offre: dict, analyse: dict, settings: dict, notion_api_key: str) -> dict[str, Any]:
    """
    Crée une entrée dans la base Notion pour une offre de thèse.

    Args:
        offre: L'offre de thèse (titre, labo, url, lieu, etc.)
        analyse: Résultat de l'analyse (score, justification, etc.)
        settings: Paramètres de configuration
        notion_api_key: Clé API Notion

    Returns:
        Dictionnaire contenant:
        - success: bool
        - notion_url: str (si succès)
        - error: str (si échec)
    """
    try:
        notion = Client(auth=notion_api_key)
        database_id = settings["notion"]["database_id"]

        # Préparer le contenu de la note
        score = analyse.get("score", 0)
        justification = analyse.get("justification", "")
        points_forts = analyse.get("points_forts", [])
        points_faibles = analyse.get("points_faibles", [])

        note_content = f"[Score: {score}/100]\n\n{justification}\n\n"
        note_content += "Points forts:\n" + "\n".join([f"• {p}" for p in points_forts])
        note_content += "\n\nPoints faibles:\n" + "\n".join([f"• {p}" for p in points_faibles])

        # Préparer les propriétés
        properties = {
            "Entreprise": {"title": [{"text": {"content": offre.get("labo", "Laboratoire non spécifié")}}]},
            "Statut": {"status": {"name": settings["notion"]["statut_nouveau"]}},
            "Note": {
                "rich_text": [
                    {
                        "text": {
                            "content": note_content[:2000]  # Limiter à 2000 caractères
                        }
                    }
                ]
            },
        }

        # Ajouter le type si le champ existe
        if "Type" in properties:
            properties["Type"] = {"select": {"name": settings["notion"]["type_these"]}}

        # Ajouter le titre de la thèse dans "Poste" si le champ existe
        if offre.get("titre"):
            properties["Poste"] = {"rich_text": [{"text": {"content": offre["titre"][:2000]}}]}

        # Ajouter l'URL si disponible
        if offre.get("url"):
            properties["Lien de l'offre"] = {"url": offre["url"]}

        # Ajouter la ville si disponible et si le champ existe
        if offre.get("lieu"):
            properties["Ville"] = {"select": {"name": offre["lieu"]}}

        # Créer la page dans Notion
        response = notion.pages.create(parent={"database_id": database_id}, properties=properties)

        return {"success": True, "notion_url": response["url"], "page_id": response["id"]}

    except Exception as e:
        return {"success": False, "error": str(e)}
