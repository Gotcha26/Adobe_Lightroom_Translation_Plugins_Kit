#!/usr/bin/env python3
"""
Nom du fichier : sync_translations.py

Dépendances : core.colors

Description :
Orchestrateur de la synchronisation complète des traductions.
Lance automatiquement les quatre étapes successives : pré-vérification des chaînes
non traduites, extraction des chaînes, mise à jour des fichiers .po, et compilation
en fichiers .mo binaires. Peut cibler une langue spécifique ou traiter toutes les langues.

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


def run_checks() -> int:
    """Lance les pré-vérifications (check_ui + check_reports).

    Returns:
        Nombre total de chaînes HIGH détectées (0 = tout est bon)
    """
    i18n_dir = Path(__file__).parent
    project_root = i18n_dir.parent

    scan_dirs = [project_root / "tools", project_root / "core"]
    high_count = 0

    # Check UI (print, input, etc.)
    try:
        from check_ui import scan_directory as scan_ui
        print(f"  {c.DIM}check_ui ...{c.RESET}", end=" ", flush=True)
        ui_results = {}
        for d in scan_dirs:
            if d.exists():
                ui_results.update(scan_ui(d))
        ui_high = sum(
            1 for strings in ui_results.values()
            for s in strings if s.confidence == "HIGH"
        )
        high_count += ui_high
        total = sum(len(v) for v in ui_results.values())
        print(f"{total} chaînes ({c.ERROR}{ui_high} HIGH{c.RESET})" if ui_high
              else f"{c.SUCCESS}{total} chaînes (0 HIGH){c.RESET}")
    except Exception as e:
        print(f"  {c.WARNING}[!] check_ui indisponible: {e}{c.RESET}")

    # Check reports (f.write dans with open)
    try:
        from check_reports import scan_directory as scan_reports
        print(f"  {c.DIM}check_reports ...{c.RESET}", end=" ", flush=True)
        report_results = {}
        for d in scan_dirs:
            if d.exists():
                report_results.update(scan_reports(d))
        report_high = sum(
            1 for strings in report_results.values()
            for s in strings if s.confidence == "HIGH"
        )
        high_count += report_high
        total = sum(len(v) for v in report_results.values())
        print(f"{total} chaînes ({c.ERROR}{report_high} HIGH{c.RESET})" if report_high
              else f"{c.SUCCESS}{total} chaînes (0 HIGH){c.RESET}")
    except Exception as e:
        print(f"  {c.WARNING}[!] check_reports indisponible: {e}{c.RESET}")

    return high_count


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

    # Étape 0: Pré-vérification
    print(c.separator("-", 70))
    print(f"{c.HEADER}ÉTAPE 0/4: PRÉ-VÉRIFICATION DES CHAÎNES{c.RESET}")
    print(c.separator("-", 70))

    warnings = run_checks()
    if warnings:
        print()
        print(f"{c.WARNING}[!] {warnings} chaîne(s) HIGH non enrobée(s) de _(){c.RESET}")
        print(f"{c.DIM}    Détails : python i18n/check_ui.py --confidence HIGH -v{c.RESET}")
        print(f"{c.DIM}             python i18n/check_reports.py --confidence HIGH -v{c.RESET}")
    else:
        print(f"{c.SUCCESS}[OK] Aucune chaîne HIGH détectée{c.RESET}")

    print()

    # Étape 1: Extraction
    print(c.separator("-", 70))
    print(f"{c.HEADER}ÉTAPE 1/4: EXTRACTION DES CHAÎNES{c.RESET}")
    print(c.separator("-", 70))

    if not run_command("extract_strings.py"):
        print()
        print(f"{c.ERROR}[X] Extraction échouée{c.RESET}")
        return 1

    print()

    # Étape 2: Mise à jour
    print(c.separator("-", 70))
    print(f"{c.HEADER}ÉTAPE 2/4: MISE À JOUR DES TRADUCTIONS{c.RESET}")
    print(c.separator("-", 70))

    args = [target_lang] if target_lang else []
    if not run_command("update_po.py", args):
        print()
        print(f"{c.ERROR}[X] Mise à jour échouée{c.RESET}")
        return 1

    print()

    # Étape 3: Compilation
    print(c.separator("-", 70))
    print(f"{c.HEADER}ÉTAPE 3/4: COMPILATION DES TRADUCTIONS{c.RESET}")
    print(c.separator("-", 70))

    args = [target_lang] if target_lang else []
    if not run_command("compile_po.py", args):
        print()
        print(f"{c.ERROR}[X] Compilation échouée{c.RESET}")
        return 1

    print()
    print(c.separator("=", 70))
    if warnings:
        print(c.warning(f"[OK] SYNCHRONISATION TERMINÉE ({warnings} alerte(s) HIGH)"))
    else:
        print(c.success("[OK] SYNCHRONISATION TERMINÉE AVEC SUCCÈS"))
    print(c.separator("=", 70))
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
