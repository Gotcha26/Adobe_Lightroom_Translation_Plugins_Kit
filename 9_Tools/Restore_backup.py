#!/usr/bin/env python3
"""
Restore_backup.py

Script pour restaurer les fichiers .lua à partir de leurs sauvegardes .bak
générées par Applicator.

Usage:
    python Restore_backup.py                    # Menu interactif
    python Restore_backup.py /path/to/plugin    # Chemin direct
    python Restore_backup.py --dry-run /path    # Simulation

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-27
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Tuple


def find_backup_pairs(directory: str) -> List[Tuple[str, str]]:
    """
    Trouve toutes les paires (fichier.lua, fichier.lua.bak) dans un répertoire.
    
    Returns:
        Liste de tuples (chemin_lua, chemin_bak)
    """
    pairs = []
    
    for root, dirs, files in os.walk(directory):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if d not in ['Locales', 'Resources', '.git']]
        
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
                print(f"  ✓ {rel_path}")
                restored += 1
            except Exception as e:
                print(f"  ✗ {rel_path} - Erreur: {e}")
    
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
                print(f"  ✓ Supprimé: {rel_path}")
                deleted += 1
            except Exception as e:
                print(f"  ✗ {rel_path} - Erreur: {e}")
    
    return deleted


def interactive_menu() -> Tuple[str, bool]:
    """
    Menu interactif pour configurer la restauration.
    
    Returns:
        (chemin_plugin, dry_run)
    """
    print("\n" + "=" * 60)
    print("  RESTAURATION DES FICHIERS .bak")
    print("=" * 60 + "\n")
    
    # Demander le répertoire
    print("Répertoire du plugin à restaurer:")
    print("  Exemples: ./piwigoPublish.lrplugin")
    print("            C:\\Lightroom\\plugin")
    print()
    
    while True:
        path = input("Chemin: ").strip()
        
        if not path:
            print("❌ Chemin obligatoire\n")
            continue
        
        normalized = os.path.normpath(path)
        
        if not os.path.isdir(normalized):
            print(f"❌ Répertoire introuvable: {normalized}\n")
            continue
        
        break
    
    print(f"\n✓ Répertoire: {normalized}\n")
    
    # Mode dry-run ?
    while True:
        response = input("Mode simulation (dry-run) ? [O/n]: ").strip().lower()
        
        if response in ['o', 'y', '', 'oui', 'yes']:
            dry_run = True
            print("✓ Mode simulation activé\n")
            break
        elif response in ['n', 'non', 'no']:
            dry_run = False
            print("✓ Mode réel - Les fichiers seront modifiés\n")
            break
        else:
            print("❌ Entrez 'o' ou 'n'\n")
    
    return normalized, dry_run


def main():
    """Point d'entrée principal."""
    
    # Parser les arguments
    dry_run = False
    directory = None
    
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
            print(f"❌ Répertoire introuvable: {directory}")
            sys.exit(1)
    else:
        # Menu interactif
        directory, dry_run = interactive_menu()
    
    # Rechercher les paires
    print("=" * 60)
    print("RECHERCHE DES FICHIERS .bak")
    print("=" * 60)
    print(f"Répertoire: {directory}\n")
    
    pairs = find_backup_pairs(directory)
    
    if not pairs:
        print("Aucun fichier .bak trouvé avec un .lua correspondant.")
        print("\n👋 Rien à restaurer.")
        sys.exit(0)
    
    # Afficher les fichiers trouvés
    print(f"Fichiers trouvés: {len(pairs)}\n")
    
    for lua_path, bak_path in pairs:
        rel_lua = os.path.relpath(lua_path, directory)
        print(f"  • {rel_lua}")
    
    # Confirmation
    print()
    if not dry_run:
        confirm = input(f"Restaurer ces {len(pairs)} fichier(s) ? [o/N]: ").strip().lower()
        if confirm not in ['o', 'oui', 'yes', 'y']:
            print("\n❌ Restauration annulée")
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
            print(f"\n✓ {deleted} fichier(s) .bak supprimé(s)")
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    
    if dry_run:
        print(f"Fichiers qui seraient restaurés: {len(pairs)}")
        print("\n⚠️  MODE SIMULATION - Aucun fichier modifié")
    else:
        print(f"Fichiers restaurés: {restored}")
    
    print("\n👋 Terminé!")


if __name__ == "__main__":
    main()