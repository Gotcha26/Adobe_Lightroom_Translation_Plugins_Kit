#!/usr/bin/env python3
"""
Extractor_menu.py

Interface menu interactive pour Extractor.
Approche "Ready to go" : affiche la configuration complète d'entrée
et permet de lancer directement ou d'éditer des options spécifiques.
"""

import os
import sys
from typing import Tuple, List, Optional

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import validate_plugin_path, get_i18n_dir
from common.colors import Colors

# Instance couleurs
c = Colors()


class InteractiveMenu:
    """Menu interactif pour configurer l'extraction."""

    def __init__(self, default_plugin_path: str = ""):
        """
        Initialise le menu avec des valeurs par défaut.

        Args:
            default_plugin_path: Chemin du plugin pré-configuré (depuis LocalisationToolKit)
        """
        self.plugin_path = default_plugin_path
        self.output_dir = ""
        self.prefix = "$$$/Piwigo"
        self.lang = "en"
        self.exclude_files: List[str] = []
        self.min_length = 3
        self.ignore_log = True

        # Valider le chemin par défaut s'il est fourni
        if default_plugin_path:
            is_valid, normalized, _ = validate_plugin_path(default_plugin_path)
            if is_valid:
                self.plugin_path = normalized

    def clear_screen(self):
        """Efface l'écran (compatible Windows et Linux)."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Affiche l'en-tête du menu."""
        print()
        print(c.box_header("EXTRACTOR - Extraction des chaînes localisables"))
        print()

    def is_ready(self) -> bool:
        """Vérifie si la configuration est prête pour lancer l'extraction."""
        return bool(self.plugin_path and os.path.isdir(self.plugin_path))

    def print_config(self):
        """Affiche la configuration actuelle."""
        print(c.title("Configuration:"))
        print()

        # Plugin path avec indicateur de validité
        if self.plugin_path:
            if os.path.isdir(self.plugin_path):
                status = f"{c.OK}OK{c.RESET}"
            else:
                status = f"{c.ERROR}INTROUVABLE{c.RESET}"
            print(c.config_line("1. Plugin", f"{self.plugin_path} [{status}]"))
        else:
            print(c.config_line("1. Plugin", f"{c.ERROR}(non défini - REQUIS){c.RESET}"))

        # Répertoire de sortie
        if self.output_dir:
            print(c.config_line("2. Sortie", self.output_dir))
        else:
            default_output = f"<plugin>/{get_i18n_dir()}/Extractor/<timestamp>/"
            print(c.config_line("2. Sortie", f"{default_output} {c.DIM}(auto){c.RESET}"))

        # Autres options
        print(c.config_line("3. Préfixe LOC", self.prefix))
        print(c.config_line("4. Langue", self.lang))

        exclude_display = ', '.join(self.exclude_files) if self.exclude_files else "(aucun)"
        print(c.config_line("5. Exclusions", exclude_display))

        print(c.config_line("6. Long. min chaînes", str(self.min_length)))

        ignore_display = f"{c.OK}Oui{c.RESET}" if self.ignore_log else f"{c.WARNING}Non{c.RESET}"
        print(c.config_line("7. Ignorer logs", ignore_display))

        print()

    def print_menu(self):
        """Affiche les options du menu."""
        print(c.separator("─"))

        if self.is_ready():
            print(c.menu_option("ENTRÉE", f"{c.GREEN}Lancer l'extraction{c.RESET}"))
        else:
            print(f"  {c.DIM}ENTRÉE  Lancer l'extraction (configurer le plugin d'abord){c.RESET}")

        print(c.menu_option("1-7", "Modifier une option"))
        print(c.menu_option("0", "Quitter"))
        print()

    def input_plugin_path(self) -> bool:
        """Demande le chemin du plugin."""
        print()
        print(c.title("1. Chemin du plugin Lightroom"))
        print(c.separator())
        print("Exemples:")
        print(f"  {c.VALUE}C:\\Users\\User\\Lightroom\\plugin.lrplugin{c.RESET}")
        print(f"  {c.VALUE}./piwigoPublish.lrplugin{c.RESET}")
        print()

        if self.plugin_path:
            print(f"Actuel: {c.VALUE}{self.plugin_path}{c.RESET}")
            path = input(c.prompt("Nouveau chemin (ENTRÉE pour garder): ")).strip()
            if not path:
                print(c.success("Chemin inchangé"))
                return True
        else:
            path = input(c.prompt("Chemin du plugin: ")).strip()
            if not path:
                print(c.error("Chemin requis!"))
                return False

        is_valid, normalized_path, warning = validate_plugin_path(path)

        if not is_valid:
            print(c.error(warning))
            return False

        if warning:
            print(c.warning(warning))
            print("            Les plugins Lightroom doivent se terminer par .lrplugin")
            confirm = input(c.prompt("Continuer quand même? [o/N]: ")).strip().lower()
            if confirm not in ['o', 'oui', 'y', 'yes']:
                print(c.error("Configuration annulée"))
                return False

        self.plugin_path = normalized_path
        print(c.success(f"Plugin: {normalized_path}"))
        return True

    def input_output_dir(self):
        """Demande le répertoire de sortie (override optionnel)."""
        print()
        print(c.title("2. Répertoire de sortie"))
        print(c.separator())
        print(f"Par défaut: {c.VALUE}<plugin>/{get_i18n_dir()}/Extractor/<timestamp>/{c.RESET}")
        print()
        print("Pour forcer un autre emplacement, entrez un chemin.")
        print(f"Sinon, appuyez sur {c.YELLOW}ENTRÉE{c.RESET} pour utiliser le défaut.")
        print()

        if self.output_dir:
            print(f"Override actuel: {c.VALUE}{self.output_dir}{c.RESET}")

        path = input(c.prompt("Répertoire (ENTRÉE pour défaut): ")).strip()

        if path:
            normalized_path = os.path.normpath(path)
            os.makedirs(normalized_path, exist_ok=True)
            self.output_dir = normalized_path
            print(c.success(f"Override: {normalized_path}"))
        else:
            self.output_dir = ""
            print(c.success(f"Utilisera: <plugin>/{get_i18n_dir()}/Extractor/<timestamp>/"))

    def input_prefix(self):
        """Demande le préfixe LOC."""
        print()
        print(c.title("3. Préfixe des clés LOC"))
        print(c.separator())
        print(f"Exemples: {c.VALUE}$$$/Piwigo{c.RESET}, {c.VALUE}$$$/MyApp{c.RESET}")
        print()

        prefix = input(c.prompt(f"Préfixe [{self.prefix}]: ")).strip()

        if prefix:
            self.prefix = prefix
            print(c.success(f"Préfixe: {self.prefix}"))
        else:
            print(c.success(f"Préfixe inchangé: {self.prefix}"))

    def input_lang(self):
        """Demande le code langue."""
        print()
        print(c.title("4. Code langue"))
        print(c.separator())
        print(f"Exemples: {c.VALUE}en{c.RESET} (anglais), {c.VALUE}fr{c.RESET} (français), {c.VALUE}de{c.RESET} (allemand)")
        print()

        lang = input(c.prompt(f"Langue [{self.lang}]: ")).strip().lower()

        if lang and len(lang) == 2:
            self.lang = lang
            print(c.success(f"Langue: {self.lang}"))
        elif lang:
            print(c.warning("Code invalide (2 caractères requis), valeur inchangée"))
        else:
            print(c.success(f"Langue inchangée: {self.lang}"))

    def input_exclude_files(self):
        """Demande les fichiers à exclure."""
        print()
        print(c.title("5. Fichiers à exclure"))
        print(c.separator())
        print(f"Exemples: {c.VALUE}JSON.lua, test.lua{c.RESET}")
        print()

        if self.exclude_files:
            print(f"Actuels: {c.VALUE}{', '.join(self.exclude_files)}{c.RESET}")

        files = input(c.prompt("Fichiers à exclure (virgule pour séparer): ")).strip()

        if files:
            self.exclude_files = [f.strip() for f in files.split(',') if f.strip()]
            print(c.success(f"Exclusions: {', '.join(self.exclude_files)}"))
        else:
            self.exclude_files = []
            print(c.success("Aucun fichier exclu"))

    def input_min_length(self):
        """Demande la longueur minimale des chaînes."""
        print()
        print(c.title("6. Longueur minimale des chaînes"))
        print(c.separator())
        print("Les chaînes plus courtes seront ignorées.")
        print()

        length = input(c.prompt(f"Longueur minimale [{self.min_length}]: ")).strip()

        if not length:
            print(c.success(f"Longueur inchangée: {self.min_length}"))
            return

        try:
            length_int = int(length)
            if length_int >= 1:
                self.min_length = length_int
                print(c.success(f"Longueur minimale: {self.min_length}"))
            else:
                print(c.error("Doit être >= 1"))
        except ValueError:
            print(c.error("Valeur invalide"))

    def input_ignore_log(self):
        """Demande si les logs doivent être ignorés."""
        print()
        print(c.title("7. Ignorer les lignes de log"))
        print(c.separator())
        print("Ignore les lignes contenant log(), warn(), etc.")
        print()

        current = "O" if self.ignore_log else "N"
        response = input(c.prompt(f"Ignorer les logs? [{current}]: ")).strip().lower()

        if response in ['o', 'y', 'oui', 'yes']:
            self.ignore_log = True
            print(c.success("Logs ignorés"))
        elif response in ['n', 'non', 'no']:
            self.ignore_log = False
            print(c.success("Logs inclus"))
        else:
            print(c.success(f"Option inchangée: {'Oui' if self.ignore_log else 'Non'}"))

    def run(self) -> bool:
        """
        Lance le menu interactif avec l'approche "Ready to go".

        Returns:
            True si l'extraction doit être lancée, False si annulé
        """
        while True:
            self.clear_screen()
            self.print_header()
            self.print_config()
            self.print_menu()

            choice = input(c.prompt("Votre choix: ")).strip()

            if choice == '0':
                print()
                print("Au revoir!")
                return False

            elif choice == '' and self.is_ready():
                # Lancer directement
                print()
                print(c.success("Lancement de l'extraction..."))
                return True

            elif choice == '1':
                self.input_plugin_path()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '2':
                self.input_output_dir()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '3':
                self.input_prefix()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '4':
                self.input_lang()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '5':
                self.input_exclude_files()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '6':
                self.input_min_length()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '7':
                self.input_ignore_log()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '':
                # ENTRÉE mais pas prêt
                print()
                print(c.error("Configurez d'abord le chemin du plugin (option 1)"))
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            else:
                print()
                print(c.error("Choix invalide"))
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

    def to_args(self) -> Tuple[str, str, str, str, List[str], int, bool]:
        """Retourne les arguments sous forme de tuple."""
        return (
            self.plugin_path,
            self.output_dir,
            self.prefix,
            self.lang,
            self.exclude_files,
            self.min_length,
            self.ignore_log
        )


def show_interactive_menu(default_plugin_path: str = "") -> Optional[Tuple[str, str, str, str, List[str], int, bool]]:
    """
    Affiche le menu interactif et retourne les paramètres.

    Args:
        default_plugin_path: Chemin du plugin pré-configuré (optionnel)

    Returns:
        Tuple avec (plugin_path, output_dir, prefix, lang, exclude_files, min_length, ignore_log)
        ou None si l'utilisateur a annulé
    """
    menu = InteractiveMenu(default_plugin_path)

    if menu.run():
        return menu.to_args()

    return None
