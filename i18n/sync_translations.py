#!/usr/bin/env python3
"""
Nom du fichier : sync_translations.py

Dépendances : core.colors

Description :
Orchestrateur de la synchronisation complète des traductions.
Lance automatiquement les trois étapes successives : extraction des chaînes,
mise à jour des fichiers .po, et compilation en fichiers .mo binaires.
Peut cibler une langue spécifique ou traiter toutes les langues.

Usage CLI :
    python i18n/sync_translations.py              # Toutes les langues
    python i18n/sync_translations.py en           # Anglais uniquement
    python i18n/sync_translations.py fr           # Français uniquement

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.colors import Colors

c = Colors()


def run_command(script_name: str, args: Optional[list] = None) -> bool:
    """Exécute un script i18n.

    Args:
        script_name: Nom du script à exécuter
        args: Arguments à passer au script

    Returns:
        True si succès, False sinon
    """
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print(f"{c.ERROR}[X] Script introuvable: {script_path}{c.RESET}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(cmd, cwd=str(Path(__file__).parent.parent))
        return result.returncode == 0
    except Exception as e:
        print(f"{c.ERROR}[X] Erreur lors de l'exécution: {e}{c.RESET}")
        return False


def main():
    """Point d'entrée principal."""
    print()
    print(c.box_header("SYNCHRONISATION DES TRADUCTIONS"))
    print()

    # Récupérer les arguments
    target_lang = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if target_lang:
        print(f"{c.INFO}[i] Mode langue spécifique: {target_lang}{c.RESET}")
    else:
        print(f"{c.INFO}[i] Mode toutes les langues{c.RESET}")

    print()

    # Étape 1: Extraction
    print(c.separator("-", 70))
    print(f"{c.HEADER}ÉTAPE 1/3: EXTRACTION DES CHAÎNES{c.RESET}")
    print(c.separator("-", 70))

    if not run_command("extract_strings.py"):
        print()
        print(f"{c.ERROR}[X] Extraction échouée{c.RESET}")
        return 1

    print()

    # Étape 2: Mise à jour
    print(c.separator("-", 70))
    print(f"{c.HEADER}ÉTAPE 2/3: MISE À JOUR DES TRADUCTIONS{c.RESET}")
    print(c.separator("-", 70))

    args = [target_lang] if target_lang else []
    if not run_command("update_po.py", args):
        print()
        print(f"{c.ERROR}[X] Mise à jour échouée{c.RESET}")
        return 1

    print()

    # Étape 3: Compilation
    print(c.separator("-", 70))
    print(f"{c.HEADER}ÉTAPE 3/3: COMPILATION DES TRADUCTIONS{c.RESET}")
    print(c.separator("-", 70))

    args = [target_lang] if target_lang else []
    if not run_command("compile_po.py", args):
        print()
        print(f"{c.ERROR}[X] Compilation échouée{c.RESET}")
        return 1

    print()
    print(c.separator("=", 70))
    print(c.success("[OK] SYNCHRONISATION TERMINEE AVEC SUCCES"))
    print(c.separator("=", 70))
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
