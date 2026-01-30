#!/usr/bin/env python3
"""
Applicator_menu.py

Interface menu interactive pour Applicator.
Approche "Ready to go" : affiche la configuration complète d'entrée
et permet de lancer directement ou d'éditer des options spécifiques.
"""

import os
import sys
from typing import Tuple, Optional

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import find_latest_tool_output, validate_plugin_path, get_i18n_dir
from common.colors import Colors

# Instance couleurs
c = Colors()


class ApplicatorMenu:
    """Menu interactif pour configurer l'application des localisations."""

    def __init__(self, default_plugin_path: str = ""):
        """
        Initialise le menu avec des valeurs par défaut.

        Args:
            default_plugin_path: Chemin du plugin pré-configuré (depuis LocalisationToolKit)
        """
        self.plugin_path = ""
        self.extraction_dir = ""
        self.dry_run = False  # Par défaut: modifications réelles
        self.create_backup = True  # Par défaut: sauvegardes activées

        # Valider et appliquer le chemin par défaut
        if default_plugin_path:
            is_valid, normalized, _ = validate_plugin_path(default_plugin_path)
            if is_valid:
                self.plugin_path = normalized
                # Auto-détecter l'extraction
                self._auto_detect_extraction()

    def _auto_detect_extraction(self):
        """Auto-détecte le dossier d'extraction le plus récent."""
        if self.plugin_path:
            latest = find_latest_tool_output(self.plugin_path, "Extractor")
            if latest:
                self.extraction_dir = latest

    def clear_screen(self):
        """Efface l'écran (compatible Windows et Linux)."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Affiche l'en-tête du menu."""
        print()
        print(c.box_header("APPLICATOR - Application des localisations"))
        print()

    def is_ready(self) -> bool:
        """Vérifie si la configuration est prête pour lancer l'application."""
        return (
            bool(self.plugin_path and os.path.isdir(self.plugin_path)) and
            bool(self.extraction_dir and os.path.isdir(self.extraction_dir))
        )

    def print_config(self):
        """Affiche la configuration actuelle."""
        print(c.title("Configuration:"))
        print()

        # Plugin path
        if self.plugin_path:
            if os.path.isdir(self.plugin_path):
                status = f"{c.OK}OK{c.RESET}"
            else:
                status = f"{c.ERROR}INTROUVABLE{c.RESET}"
            print(c.config_line("1. Plugin", f"{self.plugin_path} [{status}]"))
        else:
            print(c.config_line("1. Plugin", f"{c.ERROR}(non défini - REQUIS){c.RESET}"))

        # Dossier extraction
        if self.extraction_dir:
            if os.path.isdir(self.extraction_dir):
                # Vérifier que replacements.json existe
                replacements_file = os.path.join(self.extraction_dir, "replacements.json")
                if os.path.exists(replacements_file):
                    status = f"{c.OK}OK{c.RESET}"
                else:
                    status = f"{c.WARNING}replacements.json manquant{c.RESET}"
                print(c.config_line("2. Extraction", f"{self.extraction_dir} [{status}]"))
            else:
                print(c.config_line("2. Extraction", f"{self.extraction_dir} [{c.ERROR}INTROUVABLE{c.RESET}]"))
        else:
            print(c.config_line("2. Extraction", f"{c.ERROR}(non défini - REQUIS){c.RESET}"))

        # Mode dry-run
        if self.dry_run:
            dry_display = f"{c.WARNING}Oui (SIMULATION){c.RESET}"
        else:
            dry_display = f"{c.OK}Non (modifications réelles){c.RESET}"
        print(c.config_line("3. Mode simulation", dry_display))

        # Sauvegardes
        if self.create_backup:
            backup_display = f"{c.OK}Oui (recommandé){c.RESET}"
        else:
            backup_display = f"{c.WARNING}Non{c.RESET}"
        print(c.config_line("4. Sauvegardes .bak", backup_display))

        # Sortie Applicator
        if self.plugin_path:
            output_path = f"<plugin>/{get_i18n_dir()}/Applicator/<timestamp>/"
            print(c.config_line("   Sortie", f"{c.DIM}{output_path}{c.RESET}"))

        print()

    def print_menu(self):
        """Affiche les options du menu."""
        print(c.separator("─"))

        if self.is_ready():
            if self.dry_run:
                print(c.menu_option("ENTRÉE", f"{c.YELLOW}Lancer la SIMULATION{c.RESET}"))
            else:
                print(c.menu_option("ENTRÉE", f"{c.GREEN}Lancer l'application{c.RESET}"))
        else:
            print(f"  {c.DIM}ENTRÉE  Lancer (configurer plugin et extraction d'abord){c.RESET}")

        print(c.menu_option("1-4", "Modifier une option"))
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

        old_path = self.plugin_path
        self.plugin_path = normalized_path
        print(c.success(f"Plugin: {normalized_path}"))

        # Auto-détecter extraction si plugin change
        if old_path != normalized_path:
            self._auto_detect_extraction()
            if self.extraction_dir:
                print(c.info(f"Extraction auto-détectée: {os.path.basename(self.extraction_dir)}"))

        return True

    def input_extraction_dir(self) -> bool:
        """Demande le répertoire d'extraction."""
        print()
        print(c.title("2. Dossier d'extraction Extractor"))
        print(c.separator())

        # Chercher automatiquement
        auto_dir = None
        if self.plugin_path:
            auto_dir = find_latest_tool_output(self.plugin_path, "Extractor")

        if auto_dir:
            print(f"Détection automatique:")
            print(f"  {c.VALUE}{auto_dir}{c.RESET}")
            print()
            print(c.menu_option("1", "Utiliser ce dossier (recommandé)"))
            print(c.menu_option("2", "Spécifier un autre dossier"))
            print(c.menu_option("0", "Annuler"))
            print()

            choice = input(c.prompt("Choix [1]: ")).strip()

            if choice in ['1', '']:
                self.extraction_dir = auto_dir
                print(c.success(f"Extraction: {auto_dir}"))
                return True
            elif choice == '0':
                return True  # Ne pas changer
            elif choice != '2':
                print(c.error("Choix invalide"))
                return self.input_extraction_dir()
        else:
            print(f"{c.WARNING}Aucune extraction détectée dans {get_i18n_dir()}/Extractor/{c.RESET}")
            print("Spécifiez le chemin manuellement.")
            print()

        # Entrée manuelle
        print("Exemples:")
        print(f"  {c.VALUE}<plugin>/{get_i18n_dir()}/Extractor/20260130_091234{c.RESET}")
        print()

        if self.extraction_dir:
            print(f"Actuel: {c.VALUE}{self.extraction_dir}{c.RESET}")

        path = input(c.prompt("Dossier d'extraction: ")).strip()

        if not path:
            if self.extraction_dir:
                print(c.success("Dossier inchangé"))
                return True
            print(c.error("Dossier requis!"))
            return False

        normalized = os.path.normpath(path)

        if not os.path.isdir(normalized):
            print(c.error(f"Répertoire introuvable: {normalized}"))
            return False

        # Vérifier les fichiers requis
        required = ["replacements.json"]
        missing = [f for f in required if not os.path.exists(os.path.join(normalized, f))]

        if missing:
            print(c.warning(f"Fichiers manquants: {', '.join(missing)}"))
            print("         Ce n'est peut-être pas un dossier Extractor valide.")
            confirm = input(c.prompt("Continuer quand même? [o/N]: ")).strip().lower()
            if confirm not in ['o', 'oui', 'y', 'yes']:
                return False

        self.extraction_dir = normalized
        print(c.success(f"Extraction: {normalized}"))
        return True

    def input_dry_run(self):
        """Demande le mode dry-run."""
        print()
        print(c.title("3. Mode simulation (dry-run)"))
        print(c.separator())
        print(f"  {c.VALUE}Oui{c.RESET} = Affiche les changements SANS modifier les fichiers")
        print(f"  {c.VALUE}Non{c.RESET} = Applique les modifications (crée des backups)")
        print()

        current = "O" if self.dry_run else "N"
        response = input(c.prompt(f"Mode simulation? [{current}]: ")).strip().lower()

        if response in ['o', 'y', 'oui', 'yes']:
            self.dry_run = True
            print(c.success("Mode SIMULATION activé"))
        elif response in ['n', 'non', 'no']:
            self.dry_run = False
            print(c.success("Mode MODIFICATION activé"))
        else:
            print(c.success(f"Option inchangée: {'Simulation' if self.dry_run else 'Modification'}"))

    def input_backup(self):
        """Demande si créer des sauvegardes."""
        print()
        print(c.title("4. Sauvegardes .bak"))
        print(c.separator())
        print("Crée des copies de sauvegarde avant modification.")
        print(f"{c.WARNING}Fortement recommandé pour pouvoir revenir en arrière.{c.RESET}")
        print()

        if self.dry_run:
            print(f"{c.DIM}(Non utilisé en mode simulation){c.RESET}")
            input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")
            return

        current = "O" if self.create_backup else "N"
        response = input(c.prompt(f"Créer des sauvegardes? [{current}]: ")).strip().lower()

        if response in ['o', 'y', 'oui', 'yes', '']:
            self.create_backup = True
            print(c.success("Sauvegardes activées"))
        elif response in ['n', 'non', 'no']:
            # Double confirmation
            print(c.warning("Êtes-vous sûr de NE PAS vouloir de sauvegardes?"))
            confirm = input(c.prompt("Confirmer [o/N]: ")).strip().lower()
            if confirm in ['o', 'oui', 'y', 'yes']:
                self.create_backup = False
                print(c.success("Sauvegardes désactivées"))
            else:
                self.create_backup = True
                print(c.success("Sauvegardes activées"))
        else:
            print(c.success(f"Option inchangée: {'Oui' if self.create_backup else 'Non'}"))

    def run(self) -> bool:
        """
        Lance le menu interactif avec l'approche "Ready to go".

        Returns:
            True si l'application doit être lancée, False si annulé
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
                if self.dry_run:
                    print(c.success("Lancement de la SIMULATION..."))
                else:
                    print(c.success("Lancement de l'application..."))
                return True

            elif choice == '1':
                self.input_plugin_path()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '2':
                self.input_extraction_dir()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '3':
                self.input_dry_run()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            elif choice == '4':
                self.input_backup()

            elif choice == '':
                # ENTRÉE mais pas prêt
                print()
                if not self.plugin_path or not os.path.isdir(self.plugin_path):
                    print(c.error("Configurez d'abord le chemin du plugin (option 1)"))
                else:
                    print(c.error("Configurez d'abord le dossier d'extraction (option 2)"))
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

            else:
                print()
                print(c.error("Choix invalide"))
                input(f"\n{c.DIM}Appuyez sur ENTRÉE...{c.RESET}")

    def to_args(self) -> Tuple[str, str, bool, bool]:
        """Retourne les arguments sous forme de tuple."""
        return (
            self.plugin_path,
            self.extraction_dir,
            self.dry_run,
            self.create_backup
        )


def show_interactive_menu(default_plugin_path: str = "") -> Optional[Tuple[str, str, bool, bool]]:
    """
    Affiche le menu interactif et retourne les paramètres.

    Args:
        default_plugin_path: Chemin du plugin pré-configuré (optionnel)

    Returns:
        Tuple avec (plugin_path, extraction_dir, dry_run, create_backup)
        ou None si l'utilisateur a annulé
    """
    menu = ApplicatorMenu(default_plugin_path)

    if menu.run():
        return menu.to_args()

    return None
