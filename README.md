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

## Configuration de la base de données Notion

Votre base de données Notion doit contenir les propriétés suivantes :

- **Entreprise** (Titre) : Nom de l'entreprise
- **Statut** (Statut) : Statut de la candidature (Envoyée, À relancer, Entretien passé, etc.)
- **Date de candidature** (Date) : Date d'envoi de la candidature
- **Date d'entretien** (Date) : Date de l'entretien (optionnel)

## Utilisation

### Exécution manuelle

Exécutez le script :

```bash
python update_candidature.py
```

Le script affichera :

- Les candidatures trouvées
- Les mises à jour effectuées
- Un résumé des modifications

## Automatisation

Le script peut s'exécuter automatiquement tous les jours à 8h30 du matin.

### macOS (Launchd)

Le service launchd est déjà configuré et actif sur ce système.

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

## Structure du projet

```
.
├── update_candidature.py        # Script principal
├── run_notion_automation.sh     # Script wrapper pour l'automatisation
├── .env                          # Variables d'environnement (non versionné)
├── .env.example                  # Template de configuration
├── .gitignore                   # Fichiers à ignorer par Git
└── README.md                    # Ce fichier
```
