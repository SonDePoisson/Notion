#!/bin/bash

# Script d'automatisation pour l'exécution quotidienne du script Notion
# Ce script active l'environnement conda et exécute le script Python

# Obtenir le répertoire du script (là où se trouve ce fichier .sh)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Détecter le chemin de conda
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "/opt/homebrew/anaconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/homebrew/anaconda3/etc/profile.d/conda.sh"
else
    echo "❌ Erreur: Impossible de trouver conda"
    echo "Vérifiez que conda est installé dans ~/miniconda3 ou ~/anaconda3"
    exit 1
fi

# Activer l'environnement notion
conda activate notion

# Exécuter le script Python
python "$SCRIPT_DIR/update_candidature.py"

# Capturer le code de sortie
EXIT_CODE=$?

# Afficher un message de fin
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Script exécuté avec succès à $(date)"
else
    echo "❌ Erreur lors de l'exécution du script à $(date) - Code: $EXIT_CODE"
fi

exit $EXIT_CODE
