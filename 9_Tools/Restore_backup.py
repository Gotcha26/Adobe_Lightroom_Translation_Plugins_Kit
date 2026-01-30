#!/usr/bin/env python3
"""
Restore_backup.py

Script pour restaurer les fichiers .lua à partir de leurs sauvegardes .bak
générées par Applicator.

Les backups sont stockés dans: <plugin>/__i18n_kit__/2_Applicator/<timestamp>/backups/

Usage:
    python Restore_backup.py                    # Menu interactif
    python Restore_backup.py /path/to/plugin    # Chemin direct
    python Restore_backup.py --dry-run /path    # Simulation

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-29
Version : 2.0 - Support structure __i18n_kit__
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import get_i18n_kit_path, I18N_KIT_DIR


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
        dirs[:] = [d for d in dirs if d not in ['Locales', 'Resources', '.git', I18N_KIT_DIR]]

        for file in files:
            if file.endswith('.lua.bak'):
                bak_path = os.path.join(root, file)
                lua_path = bak_path[:-4]  # Enlever ".bak"

                if os.path.exists(lua_path):
                    pairs.append((lua_path, bak_path))

    return sorted(pairs, key=lambda x: x[0])


def restore_files(pairs: List[Tuple[str, str]], dry_run: bool = False) -> int:
    """
    Restaure les fichiers .lua depuis leurs .bak.

    Returns:
        Nombre de fichiers restaurés
    """
    restored = 0

    for lua_path, bak_path in pairs:
        rel_path = os.path.basename(lua_path)

        if dry_run:
            print(f"  [SIMULATION] {rel_path}")
        else:
            try:
                shutil.copy2(bak_path, lua_path)
                print(f"  [OK] {rel_path}")
                restored += 1
            except Exception as e:
                print(f"  [FAIL] {rel_path} - Erreur: {e}")

    return restored


def delete_backups(pairs: List[Tuple[str, str]], dry_run: bool = False) -> int:
    """
    Supprime les fichiers .bak après restauration.

    Returns:
        Nombre de fichiers supprimés
    """
    deleted = 0

    for lua_path, bak_path in pairs:
        rel_path = os.path.basename(bak_path)

        if dry_run:
            print(f"  [SIMULATION] Suppression: {rel_path}")
        else:
            try:
                os.remove(bak_path)
                print(f"  [OK] Supprime: {rel_path}")
                deleted += 1
            except Exception as e:
                print(f"  [FAIL] {rel_path} - Erreur: {e}")

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
    print("\nSessions Applicator avec backups disponibles:")
    print("-" * 60)

    for i, (timestamp, backup_dir) in enumerate(sessions, 1):
        bak_count = len([f for f in os.listdir(backup_dir) if f.endswith('.bak')])
        formatted = format_timestamp(timestamp)
        print(f"  {i}. {formatted} ({bak_count} fichier(s))")

    print(f"  0. Annuler")
    print()

    while True:
        try:
            choice = input("Choisir une session (0 pour annuler): ").strip()

            if choice == '0' or choice == '':
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(sessions):
                return sessions[idx]
            else:
                print("[ERREUR] Choix invalide")
        except ValueError:
            print("[ERREUR] Entrez un nombre")


def interactive_menu() -> Tuple[str, Optional[str], bool]:
    """
    Menu interactif pour configurer la restauration.

    Returns:
        (chemin_plugin, backup_dir ou None, dry_run)
    """
    print("\n" + "=" * 60)
    print("  RESTAURATION DES FICHIERS .bak (v2.0)")
    print("=" * 60 + "\n")

    # Demander le répertoire du plugin
    print("Repertoire du plugin a restaurer:")
    print("  Exemples: ./piwigoPublish.lrplugin")
    print("            C:\\Lightroom\\plugin")
    print()

    while True:
        path = input("Chemin: ").strip()

        if not path:
            print("[ERREUR] Chemin obligatoire\n")
            continue

        normalized = os.path.normpath(path)

        if not os.path.isdir(normalized):
            print(f"[ERREUR] Repertoire introuvable: {normalized}\n")
            continue

        break

    print(f"\n[OK] Repertoire: {normalized}\n")

    # Chercher les sessions Applicator avec backups
    sessions = find_applicator_sessions(normalized)
    backup_dir = None

    if sessions:
        print(f"[OK] {len(sessions)} session(s) Applicator trouvee(s) dans __i18n_kit__/")

        selected = select_backup_session(sessions)
        if selected:
            timestamp, backup_dir = selected
            print(f"\n[OK] Session selectionnee: {format_timestamp(timestamp)}")
    else:
        print("Aucune session Applicator trouvee dans __i18n_kit__/")
        print("Recherche des backups legacy (.lua.bak a cote des fichiers)...")

    # Mode dry-run ?
    print()
    while True:
        response = input("Mode simulation (dry-run) ? [O/n]: ").strip().lower()

        if response in ['o', 'y', '', 'oui', 'yes']:
            dry_run = True
            print("[OK] Mode simulation active\n")
            break
        elif response in ['n', 'non', 'no']:
            dry_run = False
            print("[OK] Mode reel - Les fichiers seront modifies\n")
            break
        else:
            print("[ERREUR] Entrez 'o' ou 'n'\n")

    return normalized, backup_dir, dry_run


def main():
    """Point d'entrée principal."""

    # Parser les arguments
    dry_run = False
    directory = None
    backup_dir = None

    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)

    if '--dry-run' in args:
        dry_run = True
        args.remove('--dry-run')

    if args:
        directory = os.path.normpath(args[0])
        if not os.path.isdir(directory):
            print(f"[ERREUR] Repertoire introuvable: {directory}")
            sys.exit(1)

        # En mode CLI, chercher automatiquement la dernière session
        sessions = find_applicator_sessions(directory)
        if sessions:
            timestamp, backup_dir = sessions[0]  # La plus récente
            print(f"[OK] Session Applicator trouvee: {format_timestamp(timestamp)}")
    else:
        # Menu interactif
        directory, backup_dir, dry_run = interactive_menu()

    # Rechercher les paires
    print("=" * 60)
    print("RECHERCHE DES FICHIERS .bak")
    print("=" * 60)
    print(f"Plugin: {directory}")

    if backup_dir:
        print(f"Source: {backup_dir}")
        pairs = find_backup_pairs_in_dir(backup_dir, directory)
    else:
        print("Source: Legacy (fichiers .bak a cote des .lua)")
        pairs = find_backup_pairs_legacy(directory)

    print()

    if not pairs:
        print("Aucun fichier .bak trouve.")
        print("\nRien a restaurer.")
        sys.exit(0)

    # Afficher les fichiers trouvés
    print(f"Fichiers trouves: {len(pairs)}\n")

    for lua_path, bak_path in pairs:
        lua_name = os.path.basename(lua_path)
        exists_marker = "[OK]" if os.path.exists(lua_path) else "[NEW]"
        print(f"  {exists_marker} {lua_name}")

    # Confirmation
    print()
    if not dry_run:
        confirm = input(f"Restaurer ces {len(pairs)} fichier(s) ? [o/N]: ").strip().lower()
        if confirm not in ['o', 'oui', 'yes', 'y']:
            print("\nRestauration annulee")
            sys.exit(0)

    # Restaurer
    print("\n" + "=" * 60)
    print("RESTAURATION" + (" (SIMULATION)" if dry_run else ""))
    print("=" * 60 + "\n")

    restored = restore_files(pairs, dry_run)

    # Demander si on supprime les .bak
    if not dry_run and restored > 0:
        print()
        delete_confirm = input("Supprimer les fichiers .bak ? [o/N]: ").strip().lower()

        if delete_confirm in ['o', 'oui', 'yes', 'y']:
            print("\nSuppression des .bak:")
            deleted = delete_backups(pairs, dry_run)
            print(f"\n[OK] {deleted} fichier(s) .bak supprime(s)")

    # Résumé
    print("\n" + "=" * 60)
    print("RESUME")
    print("=" * 60)

    if dry_run:
        print(f"Fichiers qui seraient restaures: {len(pairs)}")
        print("\n!!! MODE SIMULATION - Aucun fichier modifie")
    else:
        print(f"Fichiers restaures: {restored}")

    print("\nTermine!")


if __name__ == "__main__":
    main()
