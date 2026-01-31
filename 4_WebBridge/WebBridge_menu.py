#!/usr/bin/env python3
"""
WebBridge_menu.py

Interface menu interactive pour WebBridge.
Approche "Ready to go" : affiche la configuration complète d'entrée
et permet de lancer directement ou d'éditer des options spécifiques.
"""

import os
import sys
from typing import Tuple, List, Optional, Dict

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import validate_plugin_path, get_i18n_dir, find_latest_tool_output, get_tool_output_path
from common.colors import Colors
from common.menu_helpers import select_tool_output_dir

# Instance couleurs
c = Colors()


class InteractiveMenu:
    """Menu interactif pour configurer le WebBridge."""

    def __init__(self, default_plugin_path: str = ""):
        """
        Initialise le menu avec des valeurs par défaut.

        Args:
            default_plugin_path: Chemin du plugin pré-configuré (depuis LocalisationToolKit)
        """
        self.plugin_path = default_plugin_path
        self.mode = "export"  # export, import, validate
        self.json_file = ""
        self.extraction_dir = ""
        self.output_file = ""
        self.languages: List[str] = []
        self.validate_before_import = True

        # Valider le chemin par défaut s'il est fourni
        if default_plugin_path:
            is_valid, normalized, _ = validate_plugin_path(default_plugin_path)
            if is_valid:
                self.plugin_path = normalized
                # Auto-détecter le dossier d'extraction
                self.extraction_dir = find_latest_tool_output(self.plugin_path, "Extractor") or ""

    def clear_screen(self):
        """Efface l'écran (compatible Windows et Linux)."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Affiche l'en-tête du menu."""
        print()
        print(c.box_header("WEBBRIDGE - Export/Import de traductions JSON i18n"))
        print()

    def is_ready(self) -> bool:
        """Vérifie si la configuration est prête pour lancer l'opération."""
        if self.mode == "export":
            return bool(self.plugin_path and os.path.isdir(self.plugin_path) and
                       self.extraction_dir and os.path.isdir(self.extraction_dir))
        elif self.mode == "import":
            return bool(self.json_file and os.path.exists(self.json_file) and
                       self.plugin_path and os.path.isdir(self.plugin_path))
        elif self.mode == "validate":
            return bool(self.json_file and os.path.exists(self.json_file))
        return False

    def print_config(self):
        """Affiche la configuration actuelle."""
        print(c.title("Configuration:"))
        print()

        # Mode
        mode_display = {
            "export": "Export vers JSON i18n",
            "import": "Import depuis JSON i18n",
            "validate": "Validation JSON i18n"
        }
        print(c.config_line("M. Mode", mode_display.get(self.mode, self.mode)))
        print()

        if self.mode == "export":
            self._print_export_config()
        elif self.mode == "import":
            self._print_import_config()
        elif self.mode == "validate":
            self._print_validate_config()

        print()

    def _print_export_config(self):
        """Affiche la configuration pour le mode export."""
        # Plugin path
        if self.plugin_path:
            if os.path.isdir(self.plugin_path):
                status = f"{c.OK}OK{c.RESET}"
            else:
                status = f"{c.ERROR}INTROUVABLE{c.RESET}"
            print(c.config_line("1. Plugin", f"{self.plugin_path} [{status}]"))
        else:
            print(c.config_line("1. Plugin", f"{c.ERROR}(non défini - REQUIS){c.RESET}"))

        # Extraction dir
        if self.extraction_dir:
            if os.path.isdir(self.extraction_dir):
                status = f"{c.OK}OK{c.RESET}"
            else:
                status = f"{c.ERROR}INTROUVABLE{c.RESET}"
            print(c.config_line("2. Dossier Extractor", f"{self.extraction_dir} [{status}]"))
        else:
            if self.plugin_path and os.path.isdir(self.plugin_path):
                auto_detect = find_latest_tool_output(self.plugin_path, "Extractor")
                if auto_detect:
                    print(c.config_line("2. Dossier Extractor", f"{c.DIM}(auto-détection: {auto_detect}){c.RESET}"))
                else:
                    print(c.config_line("2. Dossier Extractor", f"{c.ERROR}(non trouvé - REQUIS){c.RESET}"))
            else:
                print(c.config_line("2. Dossier Extractor", f"{c.ERROR}(non défini - REQUIS){c.RESET}"))

        # Fichier de sortie
        if self.output_file:
            print(c.config_line("3. Fichier JSON", self.output_file))
        else:
            if self.plugin_path and os.path.isdir(self.plugin_path):
                webbridge_output = get_tool_output_path(self.plugin_path, "WebBridge", create=False)
                default_output = os.path.join(webbridge_output, "translations.json")
                print(c.config_line("3. Fichier JSON", f"{c.DIM}(auto: {default_output}){c.RESET}"))
            else:
                print(c.config_line("3. Fichier JSON", f"{c.DIM}(auto){c.RESET}"))

    def _print_import_config(self):
        """Affiche la configuration pour le mode import."""
        # Fichier JSON
        if self.json_file:
            if os.path.exists(self.json_file):
                status = f"{c.OK}OK{c.RESET}"
            else:
                status = f"{c.ERROR}INTROUVABLE{c.RESET}"
            print(c.config_line("1. Fichier JSON", f"{self.json_file} [{status}]"))
        else:
            print(c.config_line("1. Fichier JSON", f"{c.ERROR}(non défini - REQUIS){c.RESET}"))

        # Plugin path
        if self.plugin_path:
            if os.path.isdir(self.plugin_path):
                status = f"{c.OK}OK{c.RESET}"
            else:
                status = f"{c.ERROR}INTROUVABLE{c.RESET}"
            print(c.config_line("2. Plugin", f"{self.plugin_path} [{status}]"))
        else:
            print(c.config_line("2. Plugin", f"{c.ERROR}(non défini - REQUIS){c.RESET}"))

        # Langues
        if self.languages:
            print(c.config_line("3. Langues", ', '.join(self.languages)))
        else:
            print(c.config_line("3. Langues", f"{c.DIM}(toutes){c.RESET}"))

        # Validation
        validate_display = f"{c.OK}Oui{c.RESET}" if self.validate_before_import else f"{c.WARNING}Non{c.RESET}"
        print(c.config_line("4. Validation", validate_display))

    def _print_validate_config(self):
        """Affiche la configuration pour le mode validate."""
        # Fichier JSON
        if self.json_file:
            if os.path.exists(self.json_file):
                status = f"{c.OK}OK{c.RESET}"
            else:
                status = f"{c.ERROR}INTROUVABLE{c.RESET}"
            print(c.config_line("1. Fichier JSON", f"{self.json_file} [{status}]"))
        else:
            print(c.config_line("1. Fichier JSON", f"{c.ERROR}(non défini - REQUIS){c.RESET}"))

    def print_menu(self):
        """Affiche les options du menu."""
        print(c.separator("─"))

        if self.is_ready():
            print(f"  {c.OK}[G]{c.RESET}. {c.BOLD}GO! Lancer l'opération{c.RESET}")
        else:
            print(f"  {c.DIM}[G]. GO! Lancer l'opération (configuration incomplète){c.RESET}")

        print()

        if self.mode == "export":
            self._print_export_menu()
        elif self.mode == "import":
            self._print_import_menu()
        elif self.mode == "validate":
            self._print_validate_menu()

        print()
        print(c.menu_option("M", "Changer de mode (export/import/validate)"))
        print(c.menu_option("0", "Annuler et quitter"))
        print()

    def _print_export_menu(self):
        """Affiche le menu pour le mode export."""
        print(c.menu_option("1", "Chemin du plugin"))
        print(c.menu_option("2", "Dossier Extractor"))
        print(c.menu_option("3", "Fichier JSON de sortie"))

    def _print_import_menu(self):
        """Affiche le menu pour le mode import."""
        print(c.menu_option("1", "Fichier JSON"))
        print(c.menu_option("2", "Chemin du plugin"))
        print(c.menu_option("3", "Langues à importer"))
        print(c.menu_option("4", "Validation avant import"))

    def _print_validate_menu(self):
        """Affiche le menu pour le mode validate."""
        print(c.menu_option("1", "Fichier JSON"))

    def input_plugin_path(self):
        """Demande le chemin du plugin."""
        print()
        print(c.title("Chemin du plugin"))
        print(c.separator())

        current = self.plugin_path
        if current:
            print(f"Actuel: {c.VALUE}{current}{c.RESET}")
            print()

        print("Exemples:")
        print(f"  {c.VALUE}D:\\Lightroom\\plugin.lrplugin{c.RESET}")
        print(f"  {c.VALUE}./piwigoPublish.lrplugin{c.RESET}")
        print()

        path = input(c.prompt("Chemin (ENTRÉE pour garder): ")).strip()

        if path:
            is_valid, normalized, warning = validate_plugin_path(path)

            if not is_valid:
                print(c.error(warning))
                return

            if warning:
                print(c.warning(warning))

            self.plugin_path = normalized
            print(c.success(f"Plugin: {normalized}"))

            # Auto-détecter le dossier d'extraction
            if self.mode == "export":
                auto_detect = find_latest_tool_output(self.plugin_path, "Extractor")
                if auto_detect:
                    self.extraction_dir = auto_detect
                    print(c.info(f"Auto-détection Extractor: {auto_detect}"))
        else:
            print(c.success("Chemin inchangé"))

    def input_extraction_dir(self):
        """Demande le dossier d'extraction avec choix multiple si plusieurs disponibles."""
        selected_dir = select_tool_output_dir(self.plugin_path, "Extractor", self.extraction_dir)
        if selected_dir:
            self.extraction_dir = selected_dir

    def input_json_file(self):
        """Demande le fichier JSON."""
        print()
        print(c.title("Fichier JSON"))
        print(c.separator())

        current = self.json_file
        if current:
            print(f"Actuel: {c.VALUE}{current}{c.RESET}")
            print()

        path = input(c.prompt("Chemin (ENTRÉE pour garder): ")).strip()

        if path:
            # Normaliser le chemin
            normalized = os.path.abspath(path)
            if self.mode == "import" or self.mode == "validate":
                # Pour import/validate, le fichier doit exister
                if os.path.exists(normalized):
                    self.json_file = normalized
                    print(c.success(f"Fichier: {normalized}"))
                else:
                    print(c.error("Fichier introuvable"))
            else:
                # Pour export, le fichier peut ne pas exister encore
                self.json_file = normalized
                print(c.success(f"Fichier: {normalized}"))
        else:
            print(c.success("Chemin inchangé"))

    def input_output_file(self):
        """Demande le fichier de sortie (export)."""
        print()
        print(c.title("Fichier JSON de sortie"))
        print(c.separator())

        current = self.output_file
        if current:
            print(f"Actuel: {c.VALUE}{current}{c.RESET}")
        else:
            if self.plugin_path and os.path.isdir(self.plugin_path):
                webbridge_output = get_tool_output_path(self.plugin_path, "WebBridge", create=False)
                default = os.path.join(webbridge_output, "translations.json")
                print(f"Par défaut: {c.VALUE}{default}{c.RESET}")
        print()

        path = input(c.prompt("Chemin (ENTRÉE pour garder/défaut): ")).strip()

        if path:
            normalized = os.path.abspath(path)
            self.output_file = normalized
            print(c.success(f"Fichier: {normalized}"))
        else:
            print(c.success("Chemin inchangé (défaut auto)"))

    def input_languages(self):
        """Demande les langues à importer."""
        print()
        print(c.title("Langues à importer"))
        print(c.separator())

        current = self.languages
        if current:
            print(f"Actuel: {c.VALUE}{', '.join(current)}{c.RESET}")
        else:
            print(f"Actuel: {c.VALUE}(toutes){c.RESET}")
        print()

        print("Exemples:")
        print(f"  {c.VALUE}en{c.RESET} - Anglais seulement")
        print(f"  {c.VALUE}en,fr{c.RESET} - Anglais et français")
        print(f"  {c.VALUE}en,fr,de,es{c.RESET} - Plusieurs langues")
        print()

        langs = input(c.prompt("Langues (séparées par virgules, ENTRÉE pour toutes): ")).strip()

        if langs:
            # Parser les langues
            lang_list = [lang.strip().lower() for lang in langs.split(',') if lang.strip()]
            if lang_list:
                self.languages = lang_list
                print(c.success(f"Langues: {', '.join(lang_list)}"))
        else:
            self.languages = []
            print(c.success("Toutes les langues"))

    def toggle_validation(self):
        """Inverse la validation avant import."""
        self.validate_before_import = not self.validate_before_import
        if self.validate_before_import:
            print(c.success("Validation activée"))
        else:
            print(c.warning("Validation désactivée"))

    def change_mode(self):
        """Change de mode (export/import/validate)."""
        print()
        print(c.title("Changer de mode"))
        print(c.separator())
        print(c.menu_option("1", "Export vers JSON i18n"))
        print(c.menu_option("2", "Import depuis JSON i18n"))
        print(c.menu_option("3", "Validation JSON i18n"))
        print()

        choice = input(c.prompt("Votre choix: ")).strip()

        if choice == '1':
            self.mode = "export"
            print(c.success("Mode: Export"))
        elif choice == '2':
            self.mode = "import"
            print(c.success("Mode: Import"))
        elif choice == '3':
            self.mode = "validate"
            print(c.success("Mode: Validation"))
        else:
            print(c.error("Choix invalide"))

    def run(self) -> Optional[Tuple[str, Dict]]:
        """
        Boucle principale du menu.

        Returns:
            Tuple (mode, params) ou None si annulé
        """
        while True:
            self.clear_screen()
            self.print_header()
            self.print_config()
            self.print_menu()

            choice = input(c.prompt("Votre choix: ")).strip().upper()

            if choice == '0':
                return None
            elif choice == 'G':
                if not self.is_ready():
                    print(c.error("Configuration incomplète!"))
                    input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")
                    continue

                # Préparer les paramètres selon le mode
                if self.mode == "export":
                    params = {
                        'plugin_path': self.plugin_path,
                        'extraction_dir': self.extraction_dir or None,
                        'output_file': self.output_file or None,
                        'plugin_name': os.path.basename(self.plugin_path)
                    }
                elif self.mode == "import":
                    params = {
                        'json_file': self.json_file,
                        'plugin_path': self.plugin_path,
                        'languages': self.languages or None,
                        'validate': self.validate_before_import
                    }
                elif self.mode == "validate":
                    params = {
                        'json_file': self.json_file
                    }
                else:
                    print(c.error(f"Mode inconnu: {self.mode}"))
                    continue

                return (self.mode, params)

            elif choice == 'M':
                self.change_mode()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")

            elif choice == '1':
                if self.mode == "export":
                    self.input_plugin_path()
                elif self.mode == "import":
                    self.input_json_file()
                elif self.mode == "validate":
                    self.input_json_file()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")

            elif choice == '2':
                if self.mode == "export":
                    self.input_extraction_dir()
                elif self.mode == "import":
                    self.input_plugin_path()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")

            elif choice == '3':
                if self.mode == "export":
                    self.input_output_file()
                elif self.mode == "import":
                    self.input_languages()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")

            elif choice == '4':
                if self.mode == "import":
                    self.toggle_validation()
                    input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")
                else:
                    print(c.error("Choix invalide"))
                    input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")

            else:
                print(c.error("Choix invalide"))
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")


def show_interactive_menu(default_plugin_path: str = "") -> Optional[Tuple[str, Dict]]:
    """
    Affiche le menu interactif.

    Args:
        default_plugin_path: Chemin du plugin pré-configuré

    Returns:
        Tuple (mode, params) ou None si annulé
    """
    menu = InteractiveMenu(default_plugin_path)
    return menu.run()
