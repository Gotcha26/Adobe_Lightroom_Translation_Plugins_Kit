#!/usr/bin/env python3
"""
Nom du fichier : Delete_temp_dir.py

Dépendances : common.paths, common.colors

Description :
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

Usage CLI :
    python Delete_temp_dir.py                           # Menu interactif
    python Delete_temp_dir.py --default-plugin <path>   # Avec plugin pré-configuré

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import shutil
from typing import Optional, Tuple, List

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.paths import get_i18n_kit_path, get_i18n_dir, validate_plugin_path
from core.colors import Colors
from core.i18n import _

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
    size: float = float(size_bytes)
    for unit in ['octets', 'Ko', 'Mo', 'Go']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} To"


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
            print(c.success(_("Plugin: {var0}{var1}{var2}").format(var0=c.VALUE, var1=os.path.basename(normalized), var2=c.RESET)))
            print(_("{var0}  Chemin: {normalized}{var2}").format(var0=c.DIM, normalized=normalized, var2=c.RESET))
            print()
            return normalized
        else:
            print(c.warning(_("Plugin par défaut invalide: {warning}").format(warning=warning)))
            print()

    # Demander le chemin du plugin
    print(c.title(_("Chemin du plugin Lightroom")))
    print(c.separator())
    print(_("Exemples:"))
    print("  {var0}D:\\Lightroom\\plugin.lrplugin{var1}".format(var0=c.VALUE, var1=c.RESET))
    print("  {var0}./piwigoPublish.lrplugin{var1}".format(var0=c.VALUE, var1=c.RESET))
    print()

    path = input(c.prompt(_("Chemin du plugin: "))).strip()

    if not path:
        return None

    is_valid, normalized, warning = validate_plugin_path(path)

    if not is_valid:
        print(c.error(warning))
        return None

    # Avertissement si pas .lrplugin
    if warning:
        print(c.warning(warning))
        print(_("            Êtes-vous sûr que c'est un plugin Lightroom?"))
        confirm = input(c.prompt(_("Continuer quand même? [o/N]: "))).strip().lower()
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
    print(c.config_line(_("Dossier temporaire"), temp_dir_name))
    print(c.config_line(_("Chemin complet"), temp_dir_path))
    print()

    if not os.path.isdir(temp_dir_path):
        print(c.info(_("Le dossier temporaire n'existe pas.")))
        print(_("       Rien à supprimer."))
        return None

    # Calculer les statistiques
    total_size, total_files = get_dir_size(temp_dir_path)
    subdirs = list_subdirs(temp_dir_path)

    print(c.box_header(_("CONTENU DU DOSSIER TEMPORAIRE")))
    print()

    if subdirs:
        for subdir in subdirs:
            print(_("  {var0}{var1:25}{var2} : {var3}{var4:4}{var5} fichiers, {var6}{var7}{var8}").format(var0=c.KEY, var1=subdir['name'], var2=c.RESET, var3=c.VALUE, var4=subdir['file_count'], var5=c.RESET, var6=c.VALUE, var7=format_size(subdir['size']), var8=c.RESET))
        print()

    print(c.separator())
    print(_("{var0}TOTAL: {total_files} fichiers, {var2}{var3}").format(var0=c.BOLD, total_files=total_files, var2=format_size(total_size), var3=c.RESET))
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
    print(c.title(_("Que voulez-vous supprimer?")))
    print(c.separator())
    print()

    # Option 1: Supprimer uniquement les backups
    if backups:
        total_backup_size = sum(b['size'] for b in backups)
        total_backup_files = sum(b['file_count'] for b in backups)
        print(_("  {var0}1{var1}. {var2}Supprimer UNIQUEMENT les backups{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.INFO, var3=c.RESET))
        print(_("     {var0}{var1} session(s) de backup • {total_backup_files} fichiers • {var3}{var4}").format(var0=c.DIM, var1=len(backups), total_backup_files=total_backup_files, var3=format_size(total_backup_size), var4=c.RESET))
    else:
        print(_("  {var0}1. Supprimer UNIQUEMENT les backups (aucun backup trouvé){var1}").format(var0=c.DIM, var1=c.RESET))

    # Option 2: Supprimer tout
    total_size, total_files = get_dir_size(temp_dir_path)
    print()
    print(_("  {var0}2{var1}. {var2}Supprimer TOUT le dossier temporaire{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.ERROR, var3=c.RESET))
    print(_("     {var0}Tout le contenu • {total_files} fichiers • {var2}{var3}").format(var0=c.DIM, total_files=total_files, var2=format_size(total_size), var3=c.RESET))

    # Option 0: Annuler
    print()
    print(_("  {var0}0{var1}. {var2}Annuler{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.DIM, var3=c.RESET))
    print()

    while True:
        choice = input(c.prompt(_("Votre choix:") + " (0-2): ")).strip()

        if choice == '0':
            return "cancel", None
        elif choice == '1':
            if not backups:
                print(c.error(_("Aucun backup à supprimer")))
                continue
            # Retourner la liste des chemins de sessions à supprimer
            return "backups", [b['path'] for b in backups]
        elif choice == '2':
            return "all", None
        else:
            print(c.error(_("Choix invalide. Entrez 0, 1 ou 2")))
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
    print(_("{var0}{var1}!!! ATTENTION - OPÉRATION IRRÉVERSIBLE !!!{var2}").format(var0=c.ERROR, var1=c.BOLD, var2=c.RESET))
    print(f"{c.ERROR}{'!' * 60}{c.RESET}")
    print()

    if mode == "all":
        print(_("Cette opération va {var0}SUPPRIMER DÉFINITIVEMENT{var1}:").format(var0=c.ERROR, var1=c.RESET))
        print(f"  {c.VALUE}{target_path}{c.RESET}")
        print()
        print(_("{var0}Vous perdrez:{var1}").format(var0=c.WARNING, var1=c.RESET))
        print(_("  - Toutes les extractions précédentes"))
        print(_("  - Tous les fichiers de backup (.bak)"))
        print(_("  - Toutes les sorties des outils"))
        print()

        # Triple confirmation pour suppression totale
        print(_("{var0}Étape 1/3: Confirmation initiale{var1}").format(var0=c.BOLD, var1=c.RESET))
        confirm1 = input(c.prompt(_("Voulez-vous vraiment supprimer ce dossier? [o/N]: "))).strip().lower()
        if confirm1 not in ['o', 'oui', 'y', 'yes']:
            print(c.success(_("Suppression annulée.")))
            return False

        print(_("\n{var0}Étape 2/3: Confirmation de sécurité{var1}").format(var0=c.BOLD, var1=c.RESET))
        confirm2 = input(c.prompt(_("Tapez '{var0}SUPPRIMER{var1}{var2}' pour confirmer: ").format(var0=c.ERROR, var1=c.RESET, var2=c.YELLOW))).strip()
        if confirm2 != 'SUPPRIMER':
            print(c.success(_("Suppression annulée (mot de confirmation incorrect).")))
            return False

        print(_("\n{var0}Étape 3/3: Dernière chance{var1}").format(var0=c.BOLD, var1=c.RESET))
        confirm3 = input(c.prompt(_("Dernière confirmation - Êtes-vous ABSOLUMENT sûr? [o/N]: "))).strip().lower()
        if confirm3 not in ['o', 'oui', 'y', 'yes']:
            print(c.success(_("Suppression annulée.")))
            return False

    else:  # mode == "backups"
        print(_("Cette opération va {var0}SUPPRIMER{var1} les backups suivants:").format(var0=c.WARNING, var1=c.RESET))
        print()
        if paths_list:
            for path in paths_list:
                session_name = os.path.basename(path)
                print(f"  {c.DIM}•{c.RESET} {c.VALUE}{session_name}{c.RESET}")
        print()
        print(_("{var0}Les autres fichiers du dossier temporaire seront conservés.{var1}").format(var0=c.INFO, var1=c.RESET))
        print()

        # Confirmation simple pour backups uniquement
        confirm = input(c.prompt(_("Confirmer la suppression des backups? [o/N]: "))).strip().lower()
        if confirm not in ['o', 'oui', 'y', 'yes']:
            print(c.success(_("Suppression annulée.")))
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
            print(_("  {var0}Suppression:{var1} {var2}{name}{var4}...").format(var0=c.DIM, var1=c.RESET, var2=c.VALUE, name=name, var4=c.RESET), end=" ")
            shutil.rmtree(path)
            print(_("{var0}[OK]{var1}").format(var0=c.OK, var1=c.RESET))
            success_count += 1
        except PermissionError as e:
            print(_("{var0}[ERREUR]{var1}").format(var0=c.ERROR, var1=c.RESET))
            print(_("    {var0}Permission refusée: {e}{var2}").format(var0=c.DIM, e=e, var2=c.RESET))
            failure_count += 1
        except Exception as e:
            print(_("{var0}[ERREUR]{var1}").format(var0=c.ERROR, var1=c.RESET))
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

    # Vérifier si --default-plugin est fourni (depuis LocalizationToolKit.py)
    if '--default-plugin' in args:
        idx = args.index('--default-plugin')
        if idx + 1 < len(args):
            default_plugin = args[idx + 1]

    os.system('cls' if os.name == 'nt' else 'clear')

    print()
    print(c.box_header(_("NETTOYAGE DU DOSSIER TEMPORAIRE (v2.0)")))
    print()

    # Demander le chemin du plugin (ou utiliser celui fourni)
    plugin_path = input_plugin_path(default_plugin)

    if not plugin_path:
        print(c.error(_("Opération annulée.")))
        input(_("\n{var0}Appuyez sur ENTRÉE pour quitter...{var1}").format(var0=c.DIM, var1=c.RESET))
        sys.exit(1)

    # Afficher les informations sur le dossier temporaire
    temp_dir_path = show_temp_dir_info(plugin_path)

    if not temp_dir_path:
        input(_("\n{var0}Appuyez sur ENTRÉE pour quitter...{var1}").format(var0=c.DIM, var1=c.RESET))
        sys.exit(0)

    # Demander le mode de suppression
    mode, paths_to_delete = select_deletion_mode(temp_dir_path)

    if mode == "cancel":
        print()
        print(c.success(_("Opération annulée.")))
        input(_("\n{var0}Appuyez sur ENTRÉE pour quitter...{var1}").format(var0=c.DIM, var1=c.RESET))
        sys.exit(0)

    # Demander confirmation
    target_display = temp_dir_path if mode == "all" else "backups"
    if not confirm_deletion(mode, target_display, paths_to_delete):
        input(_("\n{var0}Appuyez sur ENTRÉE pour quitter...{var1}").format(var0=c.DIM, var1=c.RESET))
        sys.exit(0)

    # Supprimer
    print()
    print(c.separator("=", 60))
    print(c.title(_("NETTOYAGE EN COURS")))
    print(c.separator("=", 60))
    print()

    if mode == "all":
        # Supprimer tout le dossier temporaire
        success_count, failure_count = delete_paths([temp_dir_path], mode)
    else:
        # Supprimer uniquement les backups
        if paths_to_delete:
            success_count, failure_count = delete_paths(paths_to_delete, mode)
        else:
            success_count, failure_count = 0, 0

    # Résumé
    print()
    print(c.separator("=", 60))
    print(c.title(_("RÉSUMÉ")))
    print(c.separator("=", 60))

    if failure_count == 0:
        print(c.success(_("{success_count} élément(s) supprimé(s) avec succès!").format(success_count=success_count)))
        if mode == "backups":
            print()
            print(c.info(_("Les autres fichiers du dossier temporaire ont été conservés.")))
    else:
        print(_("{var0}Succès{var1}: {var2}{success_count}{var4}").format(var0=c.OK, var1=c.RESET, var2=c.VALUE, success_count=success_count, var4=c.RESET))
        print(_("{var0}Échecs{var1}: {var2}{failure_count}{var4}").format(var0=c.ERROR, var1=c.RESET, var2=c.VALUE, failure_count=failure_count, var4=c.RESET))
        print()
        print(c.warning(_("Certains fichiers n'ont pas pu être supprimés.")))
        print(_("         Fermez tous les programmes qui utilisent ces fichiers."))

    sys.exit(0 if failure_count == 0 else 1)


if __name__ == "__main__":
    main()
