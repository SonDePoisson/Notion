"""Outil de scraping des offres de thèse."""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp
from bs4 import BeautifulSoup


# Chemin du cache
CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "offres_vues.json"


def load_cache() -> list[dict]:
    """Charge le cache des offres déjà vues."""
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_cache(cache: list[dict]):
    """Sauvegarde le cache des offres."""
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def hash_offre(offre: dict) -> str:
    """Génère un hash unique pour une offre."""
    key = f"{offre.get('titre', '')}_{offre.get('labo', '')}_{offre.get('url', '')}"
    return hashlib.md5(key.encode()).hexdigest()


def is_offre_nouvelle(offre: dict, cache: list[dict]) -> bool:
    """Vérifie si une offre n'a pas déjà été vue."""
    offre_hash = hash_offre(offre)
    return not any(item["hash"] == offre_hash for item in cache)


async def fetch_url(session: aiohttp.ClientSession, url: str, timeout: int = 30) -> str:
    """Récupère le contenu HTML d'une URL."""
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        print(f"❌ Erreur lors du fetch de {url}: {e}")
        return ""


def parse_generic_page(html: str, url: str) -> list[dict]:
    """Parser générique pour extraire des offres depuis une page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    offres = []

    # Stratégie 1: Chercher des mots-clés dans les titres
    keywords = ["thèse", "doctorat", "phd", "doctoral"]

    # Chercher tous les liens
    links = soup.find_all("a", href=True)

    for link in links:
        text = link.get_text(strip=True).lower()
        href = link["href"]

        # Vérifier si le texte contient un mot-clé
        if any(kw in text for kw in keywords):
            # Construire l'URL complète si nécessaire
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(url, href)

            offre = {
                "titre": link.get_text(strip=True),
                "url": href,
                "labo": extract_labo_from_url(url),
                "description": extract_description(link),
                "date_publication": None,
                "lieu": None
            }
            offres.append(offre)

    return offres


def extract_labo_from_url(url: str) -> str:
    """Extrait le nom du laboratoire depuis l'URL."""
    # Mapper quelques URLs connues
    labo_map = {
        "laas.fr": "LAAS-CNRS",
        "ims-bordeaux.fr": "IMS Bordeaux",
        "gipsa-lab.grenoble-inp.fr": "GIPSA-Lab",
        "timc.fr": "TIMC",
        "ampere-lab.fr": "Ampère",
        "labri.fr": "LaBRI"
    }

    for domain, labo in labo_map.items():
        if domain in url:
            return labo

    # Sinon, extraire le domaine
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc


def extract_description(link_element) -> str:
    """Extrait une description depuis l'élément parent."""
    # Chercher un paragraphe ou div proche
    parent = link_element.parent
    if parent:
        desc = parent.get_text(strip=True)
        return desc[:300]  # Limiter à 300 caractères
    return ""


async def scrape_sites_theses(urls: list[str], depuis_jours: int = 7) -> list[dict]:
    """
    Scrape une liste d'URLs pour trouver des offres de thèse.

    Args:
        urls: Liste des URLs à scraper
        depuis_jours: Nombre de jours à remonter dans l'historique

    Returns:
        Liste des offres trouvées
    """
    cache = load_cache()
    toutes_offres = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        for url in urls:
            print(f"🔍 Scraping {url}...")

            html = await fetch_url(session, url)
            if not html:
                continue

            offres = parse_generic_page(html, url)

            # Filtrer les nouvelles offres
            nouvelles_offres = [o for o in offres if is_offre_nouvelle(o, cache)]

            print(f"   ✅ {len(nouvelles_offres)} nouvelle(s) offre(s)")

            toutes_offres.extend(nouvelles_offres)

            # Mettre à jour le cache
            for offre in nouvelles_offres:
                cache.append({
                    "hash": hash_offre(offre),
                    "date_vue": datetime.now().isoformat(),
                    "titre": offre.get("titre", "")
                })

            # Délai entre les requêtes
            await asyncio.sleep(2)

    # Sauvegarder le cache
    save_cache(cache)

    return toutes_offres
