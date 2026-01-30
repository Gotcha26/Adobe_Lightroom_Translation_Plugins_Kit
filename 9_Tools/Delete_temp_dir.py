#!/usr/bin/env python3
"""
Delete_temp_dir.py

Script pour supprimer le dossier temporaire i18n d'un plugin Lightroom.

Le dossier temporaire (par défaut __i18n_tmp__) contient:
  - Les extractions (Extractor/)
  - Les backups des fichiers modifiés (Applicator/)
  - Les sorties du gestionnaire de traductions (TranslationManager/)

ATTENTION: Cette opération est IRRÉVERSIBLE!
           Toutes les données dans ce dossier seront perdues.

Usage:
    python Delete_temp_dir.py

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-30
Version : 1.0
"""

import os
import sys
import shutil
from typing import Optional, Tuple

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import get_i18n_kit_path, get_i18n_dir, validate_plugin_path
from common.colors import Colors

# Instance couleurs
c = Colors()


def get_dir_size(path: str) -> Tuple[int, int]:
    """
    Calcule la taille totale et le nombre de fichiers d'un répertoire.

    Args:
        path: Chemin du répertoire

    Returns:
        Tuple (taille_en_octets, nombre_de_fichiers)
    """
    total_size = 0
    file_count = 0

    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
                file_count += 1
            except (OSError, IOError):
                pass

    return total_size, file_count


def format_size(size_bytes: int) -> str:
    """Formate une taille en octets en format lisible."""
    for unit in ['octets', 'Ko', 'Mo', 'Go']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} To"


def list_subdirs(path: str) -> list:
    """Liste les sous-dossiers d'un répertoire avec leurs infos."""
    subdirs = []

    if not os.path.isdir(path):
        return subdirs

    for name in os.listdir(path):
        subpath = os.path.join(path, name)
        if os.path.isdir(subpath):
            size, count = get_dir_size(subpath)
            subdirs.append({
                'name': name,
                'path': subpath,
                'size': size,
                'file_count': count
            })

    return subdirs


def clear_screen():
    """Efface l'écran."""
    os.system('cls' if os.name == 'nt' else 'clear')


def input_plugin_path() -> Optional[str]:
    """Demande le chemin du plugin."""
    print(c.title("Chemin du plugin Lightroom"))
    print(c.separator())
    print("Exemples:")
    print(f"  {c.VALUE}D:\\Lightroom\\plugin.lrplugin{c.RESET}")
    print(f"  {c.VALUE}./piwigoPublish.lrplugin{c.RESET}")
    print()

    path = input(c.prompt("Chemin du plugin: ")).strip()

    if not path:
        return None

    is_valid, normalized, warning = validate_plugin_path(path)

    if not is_valid:
        print(c.error(warning))
        return None

    # Avertissement si pas .lrplugin
    if warning:
        print(c.warning(warning))
        print("            Êtes-vous sûr que c'est un plugin Lightroom?")
        confirm = input(c.prompt("Continuer quand même? [o/N]: ")).strip().lower()
        if confirm not in ['o', 'oui', 'y', 'yes']:
            return None

    return normalized


def show_temp_dir_info(plugin_path: str) -> Optional[str]:
    """
    Affiche les informations sur le dossier temporaire.

    Returns:
        Chemin du dossier temporaire s'il existe, None sinon
    """
    temp_dir_name = get_i18n_dir()
    temp_dir_path = get_i18n_kit_path(plugin_path)

    print()
    print(c.config_line("Dossier temporaire", temp_dir_name))
    print(c.config_line("Chemin complet", temp_dir_path))
    print()

    if not os.path.isdir(temp_dir_path):
        print(c.info("Le dossier temporaire n'existe pas."))
        print("       Rien à supprimer.")
        return None

    # Calculer les statistiques
    total_size, total_files = get_dir_size(temp_dir_path)
    subdirs = list_subdirs(temp_dir_path)

    print(c.box_header("CONTENU DU DOSSIER TEMPORAIRE"))
    print()

    if subdirs:
        for subdir in subdirs:
            print(f"  {c.KEY}{subdir['name']:25}{c.RESET} : {c.VALUE}{subdir['file_count']:4}{c.RESET} fichiers, {c.VALUE}{format_size(subdir['size'])}{c.RESET}")
        print()

    print(c.separator())
    print(f"{c.BOLD}TOTAL: {total_files} fichiers, {format_size(total_size)}{c.RESET}")
    print(c.separator())

    return temp_dir_path


def confirm_deletion(temp_dir_path: str) -> bool:
    """
    Demande une triple confirmation avant la suppression.

    Returns:
        True si l'utilisateur confirme, False sinon
    """
    print()
    print(f"{c.ERROR}{'!' * 60}{c.RESET}")
    print(f"{c.ERROR}{c.BOLD}!!! ATTENTION - OPÉRATION IRRÉVERSIBLE !!!{c.RESET}")
    print(f"{c.ERROR}{'!' * 60}{c.RESET}")
    print()
    print(f"Cette opération va {c.ERROR}SUPPRIMER DÉFINITIVEMENT{c.RESET}:")
    print(f"  {c.VALUE}{temp_dir_path}{c.RESET}")
    print()
    print(f"{c.WARNING}Vous perdrez:{c.RESET}")
    print("  - Toutes les extractions précédentes")
    print("  - Tous les fichiers de backup (.bak)")
    print("  - Toutes les sorties des outils")
    print()

    # Première confirmation
    print(f"{c.BOLD}Étape 1/3: Confirmation initiale{c.RESET}")
    confirm1 = input(c.prompt("Voulez-vous vraiment supprimer ce dossier? [o/N]: ")).strip().lower()
    if confirm1 not in ['o', 'oui', 'y', 'yes']:
        print(c.success("Suppression annulée."))
        return False

    # Deuxième confirmation
    print(f"\n{c.BOLD}Étape 2/3: Confirmation de sécurité{c.RESET}")
    confirm2 = input(c.prompt(f"Tapez '{c.ERROR}SUPPRIMER{c.RESET}{c.YELLOW}' pour confirmer: ")).strip()
    if confirm2 != 'SUPPRIMER':
        print(c.success("Suppression annulée (mot de confirmation incorrect)."))
        return False

    # Troisième confirmation
    print(f"\n{c.BOLD}Étape 3/3: Dernière chance{c.RESET}")
    confirm3 = input(c.prompt("Dernière confirmation - Êtes-vous ABSOLUMENT sûr? [o/N]: ")).strip().lower()
    if confirm3 not in ['o', 'oui', 'y', 'yes']:
        print(c.success("Suppression annulée."))
        return False

    return True


def delete_temp_dir(temp_dir_path: str) -> bool:
    """
    Supprime le dossier temporaire.

    Returns:
        True si la suppression a réussi, False sinon
    """
    try:
        print(f"\nSuppression de {c.VALUE}{temp_dir_path}{c.RESET}...")
        shutil.rmtree(temp_dir_path)
        print(c.success("Dossier temporaire supprimé avec succès!"))
        return True
    except PermissionError as e:
        print(c.error(f"Permission refusée: {e}"))
        print("         Fermez tous les programmes qui utilisent ces fichiers.")
        return False
    except Exception as e:
        print(c.error(f"Échec de la suppression: {e}"))
        return False


def main():
    """Point d'entrée principal."""
    clear_screen()

    print()
    print(c.box_header("SUPPRESSION DU DOSSIER TEMPORAIRE"))
    print()

    # Demander le chemin du plugin
    plugin_path = input_plugin_path()

    if not plugin_path:
        print(c.error("Opération annulée."))
        input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
        sys.exit(1)

    # Afficher les informations sur le dossier temporaire
    temp_dir_path = show_temp_dir_info(plugin_path)

    if not temp_dir_path:
        input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
        sys.exit(0)

    # Demander confirmation
    if not confirm_deletion(temp_dir_path):
        input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
        sys.exit(0)

    # Supprimer le dossier
    success = delete_temp_dir(temp_dir_path)

    input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
