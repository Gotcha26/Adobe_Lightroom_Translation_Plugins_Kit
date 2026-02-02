#!/usr/bin/env python3
"""
Delete_temp_dir.py

Script pour supprimer le dossier temporaire i18n d'un plugin Lightroom.

Le dossier temporaire (par défaut __i18n_tmp__) contient:
  - Les extractions (Extractor/)
  - Les backups des fichiers modifiés (Applicator/)
  - Les sorties du gestionnaire de traductions (Translator/)

ATTENTION: Cette opération peut être IRRÉVERSIBLE!
           Les données supprimées seront perdues.

Options:
  - Supprimer uniquement les backups (Applicator/)
  - Supprimer tout le dossier temporaire

Usage:
    python Delete_temp_dir.py                           # Menu interactif
    python Delete_temp_dir.py --default-plugin <path>   # Avec plugin pré-configuré

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-02-01
Version : 2.0 - Intégration menu_generator + suppression sélective
"""

import os
import sys
import shutil
from typing import Optional, Tuple, List

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import get_i18n_kit_path, get_i18n_dir, validate_plugin_path

# Ajouter le chemin du skill menu_generator
MENU_GENERATOR_PATH = r"C:\Users\Gotcha\.claude\skills\menu_generator.py"
if os.path.exists(MENU_GENERATOR_PATH):
    skill_dir = os.path.dirname(MENU_GENERATOR_PATH)
    if skill_dir not in sys.path:
        sys.path.insert(0, skill_dir)
    from menu_generator import MenuGenerator, Colors
else:
    # Fallback si menu_generator n'est pas disponible
    from common.colors import Colors

    class MenuGenerator:
        def __init__(self, title="", enable_colors=None):
            self.c = Colors()
        def clear_screen(self): os.system('cls' if os.name == 'nt' else 'clear')

# Instance globale des couleurs
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


def find_backup_dirs(temp_dir_path: str) -> List[dict]:
    """
    Trouve tous les dossiers de backup dans Applicator/.

    Returns:
        Liste de dossiers de backup avec leurs infos
    """
    backups = []

    if not os.path.isdir(temp_dir_path):
        return backups

    # Chercher les dossiers Applicator (avec ou sans préfixe)
    applicator_dirs = []
    for name in os.listdir(temp_dir_path):
        if "applicator" in name.lower():
            applicator_dirs.append(os.path.join(temp_dir_path, name))

    # Pour chaque dossier Applicator, chercher les sessions de backup
    for applicator_dir in applicator_dirs:
        if not os.path.isdir(applicator_dir):
            continue

        for session in os.listdir(applicator_dir):
            session_path = os.path.join(applicator_dir, session)
            backup_path = os.path.join(session_path, "backups")

            # Vérifier que c'est une session valide avec backups
            if os.path.isdir(backup_path):
                size, count = get_dir_size(backup_path)
                backups.append({
                    'session': session,
                    'path': session_path,
                    'backup_path': backup_path,
                    'size': size,
                    'file_count': count
                })

    # Trier du plus récent au plus ancien
    backups.sort(key=lambda x: x['session'], reverse=True)
    return backups


def clear_screen():
    """Efface l'écran."""
    os.system('cls' if os.name == 'nt' else 'clear')


def input_plugin_path(default_plugin_path: str = "") -> Optional[str]:
    """
    Demande le chemin du plugin (ou utilise le défaut si fourni).

    Args:
        default_plugin_path: Chemin du plugin pré-configuré (optionnel)

    Returns:
        Chemin du plugin normalisé ou None si annulé
    """
    # Si un plugin par défaut est fourni et valide, l'utiliser directement
    if default_plugin_path:
        is_valid, normalized, warning = validate_plugin_path(default_plugin_path)
        if is_valid:
            print(c.success(f"Plugin: {c.VALUE}{os.path.basename(normalized)}{c.RESET}"))
            print(f"{c.DIM}  Chemin: {normalized}{c.RESET}")
            print()
            return normalized
        else:
            print(c.warning(f"Plugin par défaut invalide: {warning}"))
            print()

    # Demander le chemin du plugin
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


def select_deletion_mode(temp_dir_path: str) -> Tuple[str, Optional[List[str]]]:
    """
    Affiche un menu pour choisir le mode de suppression.

    Returns:
        Tuple (mode, paths_to_delete) où mode peut être:
        - "all": Supprimer tout le dossier temporaire
        - "backups": Supprimer uniquement les backups
        - "cancel": Annuler
        paths_to_delete contient les chemins à supprimer (ou None si "all")
    """
    backups = find_backup_dirs(temp_dir_path)

    print()
    print(c.title("Que voulez-vous supprimer?"))
    print(c.separator())
    print()

    # Option 1: Supprimer uniquement les backups
    if backups:
        total_backup_size = sum(b['size'] for b in backups)
        total_backup_files = sum(b['file_count'] for b in backups)
        print(f"  {c.YELLOW}1{c.RESET}. {c.INFO}Supprimer UNIQUEMENT les backups{c.RESET}")
        print(f"     {c.DIM}{len(backups)} session(s) de backup • {total_backup_files} fichiers • {format_size(total_backup_size)}{c.RESET}")
    else:
        print(f"  {c.DIM}1. Supprimer UNIQUEMENT les backups (aucun backup trouvé){c.RESET}")

    # Option 2: Supprimer tout
    total_size, total_files = get_dir_size(temp_dir_path)
    print()
    print(f"  {c.YELLOW}2{c.RESET}. {c.ERROR}Supprimer TOUT le dossier temporaire{c.RESET}")
    print(f"     {c.DIM}Tout le contenu • {total_files} fichiers • {format_size(total_size)}{c.RESET}")

    # Option 0: Annuler
    print()
    print(f"  {c.YELLOW}0{c.RESET}. {c.DIM}Annuler{c.RESET}")
    print()

    while True:
        choice = input(f"{c.PROMPT}Votre choix (0-2): {c.RESET}").strip()

        if choice == '0':
            return "cancel", None
        elif choice == '1':
            if not backups:
                print(c.error("Aucun backup à supprimer"))
                continue
            # Retourner la liste des chemins de sessions à supprimer
            return "backups", [b['path'] for b in backups]
        elif choice == '2':
            return "all", None
        else:
            print(c.error("Choix invalide. Entrez 0, 1 ou 2"))
            print()


def confirm_deletion(mode: str, target_path: str, paths_list: Optional[List[str]] = None) -> bool:
    """
    Demande confirmation avant la suppression.

    Args:
        mode: "all" ou "backups"
        target_path: Chemin principal à afficher
        paths_list: Liste des chemins pour mode "backups"

    Returns:
        True si l'utilisateur confirme, False sinon
    """
    print()
    print(f"{c.ERROR}{'!' * 60}{c.RESET}")
    print(f"{c.ERROR}{c.BOLD}!!! ATTENTION - OPÉRATION IRRÉVERSIBLE !!!{c.RESET}")
    print(f"{c.ERROR}{'!' * 60}{c.RESET}")
    print()

    if mode == "all":
        print(f"Cette opération va {c.ERROR}SUPPRIMER DÉFINITIVEMENT{c.RESET}:")
        print(f"  {c.VALUE}{target_path}{c.RESET}")
        print()
        print(f"{c.WARNING}Vous perdrez:{c.RESET}")
        print("  - Toutes les extractions précédentes")
        print("  - Tous les fichiers de backup (.bak)")
        print("  - Toutes les sorties des outils")
        print()

        # Triple confirmation pour suppression totale
        print(f"{c.BOLD}Étape 1/3: Confirmation initiale{c.RESET}")
        confirm1 = input(c.prompt("Voulez-vous vraiment supprimer ce dossier? [o/N]: ")).strip().lower()
        if confirm1 not in ['o', 'oui', 'y', 'yes']:
            print(c.success("Suppression annulée."))
            return False

        print(f"\n{c.BOLD}Étape 2/3: Confirmation de sécurité{c.RESET}")
        confirm2 = input(c.prompt(f"Tapez '{c.ERROR}SUPPRIMER{c.RESET}{c.YELLOW}' pour confirmer: ")).strip()
        if confirm2 != 'SUPPRIMER':
            print(c.success("Suppression annulée (mot de confirmation incorrect)."))
            return False

        print(f"\n{c.BOLD}Étape 3/3: Dernière chance{c.RESET}")
        confirm3 = input(c.prompt("Dernière confirmation - Êtes-vous ABSOLUMENT sûr? [o/N]: ")).strip().lower()
        if confirm3 not in ['o', 'oui', 'y', 'yes']:
            print(c.success("Suppression annulée."))
            return False

    else:  # mode == "backups"
        print(f"Cette opération va {c.WARNING}SUPPRIMER{c.RESET} les backups suivants:")
        print()
        if paths_list:
            for path in paths_list:
                session_name = os.path.basename(path)
                print(f"  {c.DIM}•{c.RESET} {c.VALUE}{session_name}{c.RESET}")
        print()
        print(f"{c.INFO}Les autres fichiers du dossier temporaire seront conservés.{c.RESET}")
        print()

        # Confirmation simple pour backups uniquement
        confirm = input(c.prompt("Confirmer la suppression des backups? [o/N]: ")).strip().lower()
        if confirm not in ['o', 'oui', 'y', 'yes']:
            print(c.success("Suppression annulée."))
            return False

    return True


def delete_paths(paths: List[str], mode: str) -> Tuple[int, int]:
    """
    Supprime les chemins spécifiés.

    Args:
        paths: Liste des chemins à supprimer
        mode: "all" ou "backups"

    Returns:
        Tuple (succès, échecs)
    """
    success_count = 0
    failure_count = 0

    for path in paths:
        try:
            name = os.path.basename(path) if mode == "backups" else path
            print(f"  {c.DIM}Suppression:{c.RESET} {c.VALUE}{name}{c.RESET}...", end=" ")
            shutil.rmtree(path)
            print(f"{c.OK}[OK]{c.RESET}")
            success_count += 1
        except PermissionError as e:
            print(f"{c.ERROR}[ERREUR]{c.RESET}")
            print(f"    {c.DIM}Permission refusée: {e}{c.RESET}")
            failure_count += 1
        except Exception as e:
            print(f"{c.ERROR}[ERREUR]{c.RESET}")
            print(f"    {c.DIM}{e}{c.RESET}")
            failure_count += 1

    return success_count, failure_count


def main():
    """Point d'entrée principal."""
    # Parser les arguments
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

    gen = MenuGenerator("NETTOYAGE DU DOSSIER TEMPORAIRE", enable_colors=True)
    gen.clear_screen()

    print()
    print(c.box_header("NETTOYAGE DU DOSSIER TEMPORAIRE (v2.0)"))
    print()

    # Demander le chemin du plugin (ou utiliser celui fourni)
    plugin_path = input_plugin_path(default_plugin)

    if not plugin_path:
        print(c.error("Opération annulée."))
        input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
        sys.exit(1)

    # Afficher les informations sur le dossier temporaire
    temp_dir_path = show_temp_dir_info(plugin_path)

    if not temp_dir_path:
        input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
        sys.exit(0)

    # Demander le mode de suppression
    mode, paths_to_delete = select_deletion_mode(temp_dir_path)

    if mode == "cancel":
        print()
        print(c.success("Opération annulée."))
        input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
        sys.exit(0)

    # Demander confirmation
    target_display = temp_dir_path if mode == "all" else "backups"
    if not confirm_deletion(mode, target_display, paths_to_delete):
        input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
        sys.exit(0)

    # Supprimer
    print()
    print(c.separator("=", 60))
    print(c.title("NETTOYAGE EN COURS"))
    print(c.separator("=", 60))
    print()

    if mode == "all":
        # Supprimer tout le dossier temporaire
        success_count, failure_count = delete_paths([temp_dir_path], mode)
    else:
        # Supprimer uniquement les backups
        success_count, failure_count = delete_paths(paths_to_delete, mode)

    # Résumé
    print()
    print(c.separator("=", 60))
    print(c.title("RÉSUMÉ"))
    print(c.separator("=", 60))

    if failure_count == 0:
        print(c.success(f"{success_count} élément(s) supprimé(s) avec succès!"))
        if mode == "backups":
            print()
            print(c.info("Les autres fichiers du dossier temporaire ont été conservés."))
    else:
        print(f"{c.OK}Succès{c.RESET}: {c.VALUE}{success_count}{c.RESET}")
        print(f"{c.ERROR}Échecs{c.RESET}: {c.VALUE}{failure_count}{c.RESET}")
        print()
        print(c.warning("Certains fichiers n'ont pas pu être supprimés."))
        print("         Fermez tous les programmes qui utilisent ces fichiers.")

    input(f"\n{c.DIM}Appuyez sur ENTRÉE pour quitter...{c.RESET}")
    sys.exit(0 if failure_count == 0 else 1)


if __name__ == "__main__":
    main()
