#!/usr/bin/env python3
"""Serveur MCP pour la veille automatique des offres de thèse."""

import asyncio
import os
from pathlib import Path
from typing import Any

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Prompt, PromptMessage, TextContent as PromptTextContent

try:
    from .tools.analyzer import analyser_offre
    from .tools.notion_client import creer_candidature_notion
    from .tools.profile_extractor import extract_minimal_profile, add_cache_metadata
except ImportError:
    # Fallback pour import direct
    from tools.analyzer import analyser_offre
    from tools.notion_client import creer_candidature_notion
    from tools.profile_extractor import extract_minimal_profile, add_cache_metadata


# Chemins de configuration
CONFIG_DIR = Path(__file__).parent.parent / "config"
PROFIL_PATH = CONFIG_DIR / "profil.yaml"
SITES_PATH = CONFIG_DIR / "sites.yaml"
SETTINGS_PATH = CONFIG_DIR / "settings.yaml"


def load_config(path: Path) -> dict[str, Any]:
    """Charge un fichier de configuration YAML."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# Initialiser le serveur MCP
app = Server("veille-theses")


@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """Liste tous les prompts système disponibles."""
    return [
        Prompt(
            name="recherche_theses_silencieuse",
            description="Instructions pour effectuer une recherche de thèses de manière silencieuse et autonome",
            arguments=[],
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> list[PromptMessage]:
    """Retourne le contenu d'un prompt système."""

    if name == "recherche_theses_silencieuse":
        return [
            PromptMessage(
                role="user",
                content=PromptTextContent(
                    type="text",
                    text="""INSTRUCTIONS SYSTÈME - RECHERCHE DE THÈSES SILENCIEUSE

Vous allez effectuer une recherche automatique d'offres de thèse. Ce processus doit être COMPLÈTEMENT SILENCIEUX.

WORKFLOW À SUIVRE:

1. Charger le profil candidat (outil: lire_profil) - UNE SEULE FOIS
2. Charger la liste des sites à surveiller (outil: lire_sites_surveilles)
3. Pour chaque site, effectuer des recherches web pour trouver des offres de thèse
4. Pour chaque offre trouvée:
   - Vérifier la date limite de candidature (REJETER si passée)
   - Si valide: analyser avec l'outil analyser_offre
   - Si score ≥ 60: créer l'entrée Notion avec creer_candidature_notion

RÈGLES STRICTES:

⛔ NE PAS:
- Afficher les offres trouvées dans le chat
- Décrire chaque offre à l'utilisateur
- Demander confirmation pour chaque offre
- Commenter vos actions pendant le processus
- Expliquer ce que vous faites à chaque étape

✅ FAIRE:
- Travailler de manière autonome et TOTALEMENT silencieuse
- Utiliser les outils directement sans narration

VALIDATION DES DATES:
- Si une date limite de candidature est mentionnée ET passée: REJETER immédiatement
- Si aucune date limite n'est mentionnée: ACCEPTER l'offre

Commencez maintenant la recherche de manière silencieuse.""",
                ),
            )
        ]

    raise ValueError(f"Prompt inconnu: {name}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Liste tous les outils disponibles."""
    return [
        Tool(
            name="lire_profil",
            description="""Lit le profil du candidat depuis le fichier de configuration.

OPTIMISATION: Ce profil est optimisé pour réduire la consommation de tokens.
Il contient uniquement les champs nécessaires au matching (mots-clés, domaines, localisation, compétences).
Vous pouvez CACHER ce profil dans votre contexte et le réutiliser pour tous les appels suivants
sans avoir à rappeler cet outil. Passez-le directement à 'analyser_offre' quand vous l'appelez.""",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="lire_sites_surveilles",
            description="""Lit la liste des sites à surveiller pour les offres de thèse. Claude devra ensuite faire des recherches web pour trouver les offres pertinentes.

IMPORTANT - VALIDATION DES DATES DE CANDIDATURE:
Lors de la recherche web, vous DEVEZ vérifier la date limite de candidature pour chaque offre trouvée.
- Si une date limite de candidature est mentionnée ET qu'elle est passée: NE PAS analyser cette offre, NE PAS la proposer.
- Si aucune date limite de candidature n'est mentionnée: considérer l'offre comme valide et continuer l'analyse normalement.
La date du jour est automatiquement disponible dans votre contexte pour faire cette vérification.""",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="analyser_offre",
            description="Analyse une offre de thèse par rapport au profil du candidat et retourne un score",
            inputSchema={
                "type": "object",
                "properties": {
                    "offre": {"type": "object", "description": "L'offre à analyser (titre, description, lieu, etc.)"},
                    "profil": {
                        "type": "object",
                        "description": "Le profil du candidat (optionnel, sera chargé si absent)",
                    },
                },
                "required": ["offre"],
            },
        ),
        Tool(
            name="creer_candidature_notion",
            description="Crée une entrée dans la base Notion 'Suivi de Candidatures' pour une offre de thèse",
            inputSchema={
                "type": "object",
                "properties": {
                    "offre": {"type": "object", "description": "L'offre de thèse (titre, labo, url, lieu, etc.)"},
                    "analyse": {"type": "object", "description": "Résultat de l'analyse (score, justification, etc.)"},
                },
                "required": ["offre", "analyse"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Appelle un outil selon son nom."""

    if name == "lire_profil":
        profil_complet = load_config(PROFIL_PATH)
        profil_minimal = extract_minimal_profile(profil_complet)
        message_avec_metadata = add_cache_metadata(profil_minimal)
        return [TextContent(type="text", text=message_avec_metadata)]

    elif name == "lire_sites_surveilles":
        sites = load_config(SITES_PATH)
        return [TextContent(type="text", text=yaml.dump(sites, allow_unicode=True, default_flow_style=False))]

    elif name == "analyser_offre":
        offre = arguments["offre"]
        profil = arguments.get("profil") or load_config(PROFIL_PATH)
        settings = load_config(SETTINGS_PATH)

        analyse = analyser_offre(offre, profil, settings)

        return [TextContent(type="text", text=yaml.dump(analyse, allow_unicode=True, default_flow_style=False))]

    elif name == "creer_candidature_notion":
        offre = arguments["offre"]
        analyse = arguments["analyse"]
        settings = load_config(SETTINGS_PATH)

        notion_api_key = os.getenv("NOTION_API_KEY")
        if not notion_api_key:
            return [
                TextContent(
                    type="text", text="❌ Erreur: NOTION_API_KEY non définie dans les variables d'environnement"
                )
            ]

        result = await creer_candidature_notion(offre, analyse, settings, notion_api_key)

        if result["success"]:
            return [
                TextContent(type="text", text=f"✅ Entrée créée avec succès dans Notion\n\nURL: {result['notion_url']}")
            ]
        else:
            return [
                TextContent(
                    type="text", text=f"❌ Erreur lors de la création: {result.get('error', 'Erreur inconnue')}"
                )
            ]

    else:
        return [TextContent(type="text", text=f"❌ Outil inconnu: {name}")]


async def main():
    """Point d'entrée principal du serveur MCP."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
