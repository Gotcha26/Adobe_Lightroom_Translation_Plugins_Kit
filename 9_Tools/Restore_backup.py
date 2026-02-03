#!/usr/bin/env python3
"""
Nom du fichier : Restore_backup.py

Dépendances : common.paths, common.colors

Description :
Script pour restaurer les fichiers .lua à partir de leurs sauvegardes .bak
générées par Applicator.

Les backups sont stockés dans: <plugin>/__i18n_tmp__/2_Applicator/<timestamp>/backups/

Usage CLI :
    python Restore_backup.py                    # Menu interactif
    python Restore_backup.py /path/to/plugin    # Chemin direct

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import get_i18n_kit_path, get_i18n_dir, validate_plugin_path
from common.colors import Colors
from common.i18n import _

# Instance globale des couleurs
c = Colors()


def find_applicator_sessions(plugin_path: str) -> List[Tuple[str, str]]:
    """
    Trouve toutes les sessions Applicator avec des backups.

    Recherche dans les dossiers "Applicator" ou "X_Applicator"
    pour supporter les deux formats (avec et sans préfixe).

    Args:
        plugin_path: Chemin du plugin

    Returns:
        Liste de tuples (timestamp, chemin_backup_dir) triés du plus récent au plus ancien
    """
    sessions = []
    i18n_kit_path = get_i18n_kit_path(plugin_path)

    # Chercher tous les dossiers qui contiennent "Applicator" (avec ou sans préfixe)
    if not os.path.isdir(i18n_kit_path):
        return sessions

    applicator_dirs = []
    for name in os.listdir(i18n_kit_path):
        if "applicator" in name.lower():
            applicator_dirs.append(os.path.join(i18n_kit_path, name))

    # Si aucun dossier Applicator trouvé, retourner vide
    if not applicator_dirs:
        return sessions

    # Parcourir tous les dossiers Applicator trouvés
    for applicator_dir in applicator_dirs:
        if not os.path.isdir(applicator_dir):
            continue

        for item in os.listdir(applicator_dir):
            item_path = os.path.join(applicator_dir, item)
            backup_path = os.path.join(item_path, "backups")

            # Vérifier format timestamp (15 caractères: YYYYMMDD_HHMMSS)
            if (os.path.isdir(item_path) and len(item) == 15 and item[8] == '_'
                    and os.path.isdir(backup_path)):
                # Vérifier qu'il y a des fichiers .bak
                bak_files = [f for f in os.listdir(backup_path) if f.endswith('.bak')]
                if bak_files:
                    sessions.append((item, backup_path))

    # Trier du plus récent au plus ancien
    sessions.sort(key=lambda x: x[0], reverse=True)
    return sessions


def find_backup_pairs_in_dir(backup_dir: str, plugin_path: str) -> List[Tuple[str, str]]:
    """
    Trouve les paires (fichier.lua dans plugin, fichier.bak dans backup_dir).

    Args:
        backup_dir: Répertoire contenant les fichiers .bak
        plugin_path: Chemin du plugin où restaurer

    Returns:
        Liste de tuples (chemin_lua_cible, chemin_bak_source)
    """
    pairs = []

    if not os.path.isdir(backup_dir):
        return pairs

    for file in os.listdir(backup_dir):
        if file.endswith('.bak'):
            bak_path = os.path.join(backup_dir, file)
            # Le fichier original est dans le plugin avec le même nom sans .bak
            lua_filename = file[:-4]  # Enlever ".bak"
            lua_path = os.path.join(plugin_path, lua_filename)

            pairs.append((lua_path, bak_path))

    return sorted(pairs, key=lambda x: os.path.basename(x[0]))


def find_backup_pairs_legacy(directory: str) -> List[Tuple[str, str]]:
    """
    Trouve les paires (fichier.lua, fichier.lua.bak) dans un répertoire (mode legacy).
    Cherche les .bak à côté des .lua (ancienne structure).

    Returns:
        Liste de tuples (chemin_lua, chemin_bak)
    """
    pairs = []

    for root, dirs, files in os.walk(directory):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if d not in ['Locales', 'Resources', '.git', get_i18n_dir()]]

        for file in files:
            if file.endswith('.lua.bak'):
                bak_path = os.path.join(root, file)
                lua_path = bak_path[:-4]  # Enlever ".bak"

                if os.path.exists(lua_path):
                    pairs.append((lua_path, bak_path))

    return sorted(pairs, key=lambda x: x[0])


def restore_files(pairs: List[Tuple[str, str]]) -> int:
    """
    Restaure les fichiers .lua depuis leurs .bak.

    Returns:
        Nombre de fichiers restaurés
    """
    restored = 0

    for lua_path, bak_path in pairs:
        rel_path = os.path.basename(lua_path)

        try:
            shutil.copy2(bak_path, lua_path)
            print(f"  {c.OK}[OK]{c.RESET} {rel_path}")
            restored += 1
        except Exception as e:
            print(f"  {c.ERROR}[FAIL]{c.RESET} {rel_path} {c.DIM}- Erreur: {e}{c.RESET}")

    return restored


def delete_backups(pairs: List[Tuple[str, str]]) -> int:
    """
    Supprime les fichiers .bak après restauration.

    Returns:
        Nombre de fichiers supprimés
    """
    deleted = 0

    for lua_path, bak_path in pairs:
        rel_path = os.path.basename(bak_path)

        try:
            os.remove(bak_path)
            print(f"  {c.OK}[OK]{c.RESET} Supprimé: {rel_path}")
            deleted += 1
        except Exception as e:
            print(f"  {c.ERROR}[FAIL]{c.RESET} {rel_path} {c.DIM}- Erreur: {e}{c.RESET}")

    return deleted


def format_timestamp(timestamp: str) -> str:
    """Formate un timestamp YYYYMMDD_HHMMSS en format lisible."""
    try:
        date_part = timestamp[:8]
        time_part = timestamp[9:15]
        return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
    except:
        return timestamp


def select_backup_session(sessions: List[Tuple[str, str]]) -> Optional[Tuple[str, str]]:
    """
    Permet à l'utilisateur de sélectionner une session de backup.

    Returns:
        Tuple (timestamp, backup_dir) ou None si annulé
    """
    print()
    print(c.title("Sessions Applicator avec backups disponibles"))
    print(c.separator())
    print()

    # Afficher les sessions avec numérotation
    for i, (timestamp, backup_dir) in enumerate(sessions, 1):
        bak_count = len([f for f in os.listdir(backup_dir) if f.endswith('.bak')])
        formatted = format_timestamp(timestamp)

        # Marquer la plus récente (première)
        if i == 1:
            marker = f"{c.OK}[DERNIÈRE]{c.RESET} "
        else:
            marker = "           "

        print(f"  {c.YELLOW}{i}{c.RESET}. {marker}{c.VALUE}{formatted}{c.RESET} {c.DIM}({bak_count} fichier(s)){c.RESET}")

    print(f"  {c.YELLOW}0{c.RESET}. {c.DIM}Annuler{c.RESET}")
    print()

    # Suggestion par défaut: la plus récente
    default_choice = "1"

    while True:
        try:
            choice = input(f"{c.PROMPT}Choisir une session [{c.OK}{default_choice}{c.RESET}{c.PROMPT} par défaut]{c.RESET}: ").strip()

            # Si vide, utiliser le défaut
            if choice == '':
                choice = default_choice

            if choice == '0':
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                return sessions[idx]
            else:
                print(c.error(f"Choix invalide. Entrez un nombre entre 0 et {len(sessions)}"))
        except ValueError:
            print(c.error("Entrez un nombre valide"))


def interactive_menu(default_plugin_path: str = "") -> Tuple[str, Optional[str]]:
    """
    Menu interactif pour configurer la restauration.

    Args:
        default_plugin_path: Chemin du plugin pré-configuré (optionnel)

    Returns:
        (chemin_plugin, backup_dir ou None)
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print(c.box_header("RESTAURATION DES FICHIERS .bak"))
    print()

    # Si un plugin par défaut est fourni et valide, l'utiliser directement
    if default_plugin_path:
        is_valid, normalized, warning = validate_plugin_path(default_plugin_path)
        if is_valid:
            print(c.success(f"Plugin: {c.VALUE}{os.path.basename(normalized)}{c.RESET}"))
            print(f"{c.DIM}  Chemin: {normalized}{c.RESET}")
            print()
        else:
            # Le chemin par défaut est invalide, demander à l'utilisateur
            print(c.warning(f"Plugin par défaut invalide: {warning}"))
            print()
            default_plugin_path = ""

    # Si pas de plugin par défaut valide, demander à l'utilisateur
    if not default_plugin_path:
        print(c.title("Configuration du plugin"))
        print(c.separator())
        print()
        print(f"{c.DIM}Répertoire du plugin à restaurer:{c.RESET}")
        print(f"{c.DIM}  Exemples: ./piwigoPublish.lrplugin{c.RESET}")
        print(f"{c.DIM}            D:\\Lightroom\\plugin.lrplugin{c.RESET}")
        print()

        while True:
            path = input(f"{c.PROMPT}Chemin du plugin: {c.RESET}").strip()

            if not path:
                print(c.error("Chemin obligatoire"))
                print()
                continue

            # Utiliser validate_plugin_path pour validation
            is_valid, normalized, warning = validate_plugin_path(path)

            if not is_valid:
                print(c.error(warning))
                print()
                continue

            # Avertissement si pas .lrplugin
            if warning:
                print(c.warning(warning))
                confirm = input(f"{c.PROMPT}Continuer quand même? [o/N]: {c.RESET}").strip().lower()
                if confirm not in ['o', 'oui', 'y', 'yes']:
                    print()
                    continue

            break

        print()
        print(c.success(f"Plugin: {c.VALUE}{normalized}{c.RESET}"))
        print()
    else:
        # Utiliser le plugin par défaut validé
        normalized = default_plugin_path

    # Chercher les sessions Applicator avec backups
    sessions = find_applicator_sessions(normalized)
    backup_dir = None

    if sessions:
        print(c.info(f"{len(sessions)} session(s) Applicator trouvée(s) dans {get_i18n_dir()}/"))
        print()

        selected = select_backup_session(sessions)
        if selected:
            timestamp, backup_dir = selected
            print()
            print(c.success(f"Session sélectionnée: {c.VALUE}{format_timestamp(timestamp)}{c.RESET}"))
        else:
            print()
            print(c.warning("Restauration annulée"))
            sys.exit(0)
    else:
        print(c.warning(f"Aucune session Applicator trouvée dans {get_i18n_dir()}/"))
        print(f"{c.DIM}Recherche des backups legacy (.lua.bak à côté des fichiers)...{c.RESET}")

    return normalized, backup_dir


def main():
    """Point d'entrée principal."""

    # Parser les arguments
    directory = None
    backup_dir = None
    default_plugin = ""

    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)

    # Vérifier si --default-plugin est fourni (depuis LocalisationToolKit.py)
    if '--default-plugin' in args:
        idx = args.index('--default-plugin')
        if idx + 1 < len(args):
            default_plugin = args[idx + 1]
            args.remove('--default-plugin')
            args.remove(default_plugin)

    if args:
        # Mode CLI avec chemin direct
        directory = os.path.normpath(args[0])
        if not os.path.isdir(directory):
            print(c.error(f"Répertoire introuvable: {directory}"))
            sys.exit(1)

        # En mode CLI, chercher automatiquement la dernière session
        sessions = find_applicator_sessions(directory)
        if sessions:
            timestamp, backup_dir = sessions[0]  # La plus récente
            print(c.success(f"Session Applicator trouvée: {c.VALUE}{format_timestamp(timestamp)}{c.RESET}"))
    else:
        # Menu interactif (avec plugin par défaut si fourni)
        directory, backup_dir = interactive_menu(default_plugin)

    # Rechercher les paires
    print(c.separator("=", 60))
    print(c.title("RECHERCHE DES FICHIERS .bak"))
    print(c.separator("=", 60))
    print(f"{c.KEY}Plugin{c.RESET}: {c.VALUE}{directory}{c.RESET}")

    if backup_dir:
        print(f"{c.KEY}Source{c.RESET}: {c.VALUE}{backup_dir}{c.RESET}")
        pairs = find_backup_pairs_in_dir(backup_dir, directory)
    else:
        print(f"{c.KEY}Source{c.RESET}: {c.DIM}Legacy (fichiers .bak à côté des .lua){c.RESET}")
        pairs = find_backup_pairs_legacy(directory)

    print()

    if not pairs:
        print(c.warning("Aucun fichier .bak trouvé"))
        print()
        print(c.info("Rien à restaurer"))
        sys.exit(0)

    # Afficher les fichiers trouvés
    print(c.info(f"Fichiers trouvés: {c.VALUE}{len(pairs)}{c.RESET}"))
    print()

    for lua_path, bak_path in pairs:
        lua_name = os.path.basename(lua_path)
        if os.path.exists(lua_path):
            exists_marker = f"{c.OK}[REMPLACER]{c.RESET}"
        else:
            exists_marker = f"{c.INFO}[NOUVEAU]{c.RESET}"
        print(f"  {exists_marker} {lua_name}")

    # Confirmation
    print()
    confirm = input(f"{c.PROMPT}Restaurer ces {len(pairs)} fichier(s) ? [o/N]: {c.RESET}").strip().lower()
    if confirm not in ['o', 'oui', 'yes', 'y']:
        print()
        print(c.warning("Restauration annulée"))
        sys.exit(0)

    # Restaurer
    print()
    print(c.separator("=", 60))
    print(c.title("RESTAURATION"))
    print(c.separator("=", 60))
    print()

    restored = restore_files(pairs)

    # Demander si on supprime les .bak
    if restored > 0:
        print()
        delete_confirm = input(f"{c.PROMPT}Supprimer les fichiers .bak ? [o/N]: {c.RESET}").strip().lower()

        if delete_confirm in ['o', 'oui', 'yes', 'y']:
            print()
            print(c.info("Suppression des .bak"))
            print()
            deleted = delete_backups(pairs)
            print()
            print(c.success(f"{deleted} fichier(s) .bak supprimé(s)"))

    # Résumé
    print()
    print(c.separator("=", 60))
    print(c.title("RÉSUMÉ"))
    print(c.separator("=", 60))

    print(f"{c.KEY}Fichiers restaurés{c.RESET}: {c.VALUE}{restored}{c.RESET}")

    print()
    print(c.success("Terminé!"))


if __name__ == "__main__":
    main()
