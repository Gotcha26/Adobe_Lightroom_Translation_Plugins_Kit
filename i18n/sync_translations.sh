#!/bin/bash
# sync_translations.sh - Lance la synchronisation i18n sur Linux/Mac
#
# Utilisation:
#   ./i18n/sync_translations.sh
#   ./i18n/sync_translations.sh en     (pour l'anglais uniquement)
#   ./i18n/sync_translations.sh fr     (pour le français uniquement)

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RESET='\033[0m'
BOLD='\033[1m'

# Aller au répertoire du projet
cd "$(dirname "$0")/.."

# En-tête
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                 SYNCHRONISATION DES TRADUCTIONS (i18n)                     ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

if [ -z "$1" ]; then
    echo "[i] Mode: Toutes les langues"
else
    echo "[i] Mode: Langue spécifique ($1)"
fi
echo ""

# Fonction pour afficher une erreur
error_exit() {
    echo ""
    echo -e "${RED}[X] $1${RESET}"
    exit 1
}

# Étape 1: Extraction
echo "────────────────────────────────────────────────────────────────────────────"
echo "ÉTAPE 1/3: EXTRACTION DES CHAÎNES"
echo "────────────────────────────────────────────────────────────────────────────"
python i18n/extract_strings.py || error_exit "Extraction échouée"
echo ""

# Étape 2: Mise à jour
echo "────────────────────────────────────────────────────────────────────────────"
echo "ÉTAPE 2/3: MISE À JOUR DES TRADUCTIONS"
echo "────────────────────────────────────────────────────────────────────────────"
if [ -z "$1" ]; then
    python i18n/update_po.py || error_exit "Mise à jour échouée"
else
    python i18n/update_po.py "$1" || error_exit "Mise à jour échouée"
fi
echo ""

# Étape 3: Compilation
echo "────────────────────────────────────────────────────────────────────────────"
echo "ÉTAPE 3/3: COMPILATION DES TRADUCTIONS"
echo "────────────────────────────────────────────────────────────────────────────"
if [ -z "$1" ]; then
    python i18n/compile_po.py || error_exit "Compilation échouée"
else
    python i18n/compile_po.py "$1" || error_exit "Compilation échouée"
fi
echo ""

echo "════════════════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ SYNCHRONISATION TERMINÉE AVEC SUCCÈS${RESET}"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
