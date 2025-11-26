# Automatisation Notion - Suivi de Candidatures

Script Python pour automatiser la gestion de candidatures dans Notion.

## Fonctionnalités

Ce script automatise deux tâches principales :

1. **Relance des candidatures** : Si une candidature a le statut "Envoyée" depuis plus de 10 jours, elle passe automatiquement en statut "À relancer"

2. **Suivi des entretiens** : Si une date d'entretien est dépassée, le statut passe automatiquement à "Entretien passé"

## Prérequis

- Python 3.10+
- Un compte Notion avec une base de données de suivi de candidatures
- Une clé API Notion

## Installation

1. Clonez ce dépôt :

```bash
git clone https://github.com/votre-username/Notion.git
cd Notion
```

2. Installez les dépendances :

```bash
pip install notion-client python-dotenv python-dateutil
```

3. Créez un fichier `.env` à partir du template :

```bash
cp .env.example .env
```

4. Éditez le fichier `.env` avec vos informations :

```
NOTION_API_KEY=votre_clé_api_notion
DATABASE_ID=id_de_votre_base_de_données
```

## Structure du projet

```
.
├── update_candidature.py   # Script principal
├── .env                     # Variables d'environnement (non versionné)
├── .env.example             # Template de configuration
├── .gitignore              # Fichiers à ignorer par Git
└── README.md               # Ce fichier
```
