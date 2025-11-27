#!/usr/bin/env python3
"""Serveur MCP pour la veille automatique des offres de thèse."""

import asyncio
import os
from pathlib import Path
from typing import Any

import yaml
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

try:
    from .tools.analyzer import analyser_offre
    from .tools.notion_client import creer_candidature_notion
except ImportError:
    # Fallback pour import direct
    from tools.analyzer import analyser_offre
    from tools.notion_client import creer_candidature_notion


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


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Liste tous les outils disponibles."""
    return [
        Tool(
            name="lire_profil",
            description="Lit le profil du candidat depuis le fichier de configuration",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="lire_sites_surveilles",
            description="Lit la liste des sites à surveiller pour les offres de thèse. Claude devra ensuite faire des recherches web pour trouver les offres pertinentes.",
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
        profil = load_config(PROFIL_PATH)
        return [TextContent(type="text", text=yaml.dump(profil, allow_unicode=True, default_flow_style=False))]

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
