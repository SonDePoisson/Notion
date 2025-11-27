# Automatisation Notion - Suivi de Candidatures & Recherche de Thèses

Outils Python pour automatiser la gestion de candidatures et la recherche de thèses dans Notion.

## Fonctionnalités

### 1. Script d'automatisation quotidienne

Script Python qui s'exécute automatiquement tous les jours à 8h30 pour :

- **Relance des candidatures** : Si une candidature a le statut "Envoyée" depuis plus de 10 jours, elle passe automatiquement en statut "À relancer"
- **Suivi des entretiens** : Si une date d'entretien est dépassée, le statut passe automatiquement à "Entretien passé"

### 2. MCP Veille Thèses

Serveur MCP (Model Context Protocol) qui permet à Claude de :

- **Rechercher automatiquement** des offres de thèse via des recherches web
- **Analyser la correspondance** entre les offres et votre profil de candidat (score 0-100)
- **Créer automatiquement** des entrées dans votre base Notion pour les offres pertinentes

#### Outils MCP disponibles

- `lire_profil` : Charge votre profil candidat
- `lire_sites_surveilles` : Liste les sites à surveiller (Claude fera ensuite des recherches web)
- `analyser_offre` : Analyse une offre par rapport à votre profil
- `creer_candidature_notion` : Crée une entrée Notion

## Prérequis

- Python 3.10+
- Un compte Notion avec une base de données de suivi de candidatures
- Une clé API Notion

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/SonDePoisson/Notion.git
cd Notion
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration

#### Variables d'environnement

Créez un fichier `.env` à partir du template :

```bash
cp .env.example .env
```

Éditez le fichier `.env` avec vos informations :

```
NOTION_API_KEY=votre_clé_api_notion
DATABASE_ID=id_de_votre_base_de_données
```

#### Configuration du MCP

Copiez les fichiers de configuration exemples :

```bash
cp config/profil.example.yaml config/profil.yaml
cp config/sites.example.yaml config/sites.yaml
cp config/settings.example.yaml config/settings.yaml
```

Éditez chaque fichier avec vos informations personnelles :

- **`config/profil.yaml`** : Votre profil (compétences, domaines d'intérêt, critères de thèse)
- **`config/sites.yaml`** : Sites web à surveiller
- **`config/settings.yaml`** : Paramètres (seuils de matching, Database ID)

## Configuration de la base de données Notion

Votre base de données Notion doit contenir les propriétés suivantes :

- **Entreprise** (Titre) : Nom de l'entreprise ou du laboratoire
- **Statut** (Statut) : Statut de la candidature (Envoyée, À relancer, Entretien passé, À évaluer, etc.)
- **Date de candidature** (Date) : Date d'envoi de la candidature
- **Date d'entretien** (Date) : Date de l'entretien (optionnel)
- **Type** (Select) : Type de poste (Thèse, Stage, CDI, etc.)
- **Poste** (Text) : Titre du poste
- **Ville** (Select) : Ville
- **Lien de l'offre** (URL) : URL de l'offre
- **Note** (Text) : Notes et analyse

**Important** : Créez le statut **"À évaluer"** dans la propriété Statut pour les offres automatiques.

## Utilisation

### Script d'automatisation quotidienne

#### Exécution manuelle

```bash
python src/update_candidature.py
```

#### Automatisation avec launchd (macOS)

Le script s'exécute automatiquement tous les jours à 8h30 via launchd.

**Commandes utiles :**

```bash
# Vérifier le statut du service
launchctl list | grep notion

# Démarrer le service manuellement (pour tester)
launchctl start com.notion.automation

# Arrêter le service
launchctl stop com.notion.automation

# Désactiver l'automatisation
launchctl unload ~/Library/LaunchAgents/com.notion.automation.plist

# Réactiver l'automatisation
launchctl load ~/Library/LaunchAgents/com.notion.automation.plist
```

**Consulter les logs :**

```bash
# Logs de sortie standard
tail -f ~/Library/Logs/notion_automation.log

# Logs d'erreur
tail -f ~/Library/Logs/notion_automation_error.log
```

### MCP Veille Thèses

#### Configuration Claude Desktop

Ajoutez le serveur MCP dans `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) :

```json
{
  "mcpServers": {
    "veille-theses": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/Users/votre-nom/Code/Notion",
      "env": {
        "NOTION_API_KEY": "votre_clé_api_notion"
      }
    }
  }
}
```

Redémarrez Claude Desktop.

#### Utilisation avec Claude

**Lancer une veille complète :**

> "Lance la veille des offres de thèse"

Claude va automatiquement :

1. Charger votre profil
2. Lire les sites à surveiller
3. Faire des recherches web pour trouver des offres
4. Analyser chaque offre trouvée
5. Créer des entrées Notion pour les offres pertinentes (score ≥ 60)

**Autres commandes :**

> "Recherche des offres de thèse pour moi sur [thématique]"

> "Analyse cette offre pour moi : [URL]"

> "Ajoute cette thèse à mon suivi Notion : [URL]"

## Analyse de correspondance

Le MCP calcule un score (0-100) basé sur :

- **Mots-clés positifs** : +5 points par mot-clé trouvé (max 40)
- **Mots-clés négatifs** : -10 points par mot-clé trouvé (max -30)
- **Localisation** : +20 (préférée), +10 (acceptable), -5 (autre)
- **Compétences** : +3 points par compétence correspondante (max 20)
- **Domaines d'intérêt** : +15 (principal), +8 (secondaire)

**Seuils par défaut :**

- Score ≥ 80 : 🔥 Haute priorité
- Score ≥ 60 : ✅ Pertinent (ajouté à Notion)
- Score < 60 : ⚠️ Non ajouté

## Structure du projet

```
.
├── src/                         # Code source
│   ├── mcp_server.py           # Serveur MCP principal
│   ├── update_candidature.py   # Script d'automatisation quotidienne
│   └── tools/
│       ├── analyzer.py         # Analyse de correspondance
│       └── notion_client.py    # Intégration Notion
├── config/                      # Configuration du MCP
│   ├── profil.yaml             # Votre profil (ignoré par git)
│   ├── sites.yaml              # Sites à surveiller (ignoré par git)
│   ├── settings.yaml           # Paramètres (ignoré par git)
│   ├── profil.example.yaml     # Template de profil
│   ├── sites.example.yaml      # Template de sites
│   └── settings.example.yaml   # Template de paramètres
├── run_notion_automation.sh    # Script wrapper pour launchd
├── requirements.txt            # Dépendances Python
├── .env                        # Variables d'environnement (ignoré par git)
├── .env.example                # Template de variables
├── .gitignore                 # Fichiers ignorés par git
└── README.md                  # Ce fichier
```

## Dépannage

### Script d'automatisation

**Le script ne trouve pas de candidatures :**

- Vérifiez que la base Notion est bien partagée avec l'intégration
- Vérifiez les noms des propriétés (Entreprise, Statut, etc.)

**Le service launchd ne démarre pas :**

- Vérifiez les logs : `tail ~/Library/Logs/notion_automation_error.log`
- Vérifiez que l'environnement conda est bien activé dans le script wrapper

### MCP Veille Thèses

**Le serveur ne démarre pas :**

- Vérifiez que Python 3.10+ est installé
- Vérifiez que toutes les dépendances sont installées : `pip install -r requirements.txt`
- Vérifiez que les fichiers de config existent (profil.yaml, sites.yaml, settings.yaml)

**Erreur Notion :**

- Vérifiez que `NOTION_API_KEY` est définie
- Vérifiez que l'intégration Notion a accès à votre base
- Vérifiez que le `database_id` dans `settings.yaml` est correct
- Vérifiez que le statut "À évaluer" existe dans votre base

## Licence

MIT
