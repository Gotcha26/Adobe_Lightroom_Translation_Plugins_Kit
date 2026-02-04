#!/usr/bin/env python3
"""
Nom du fichier : menu.py

Dépendances : Aucune

Description :
Interface menu interactif pour Extractor. Classe InteractiveMenu avec approche "Ready to go"
pour configurer et lancer l'extraction avec options de modification en ligne.

Usage CLI :
    Non pourvu

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
from typing import Tuple, List, Optional

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.paths import validate_plugin_path, get_i18n_dir
from core.colors import Colors
from core.i18n import _

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
        print(c.box_header(_("EXTRACTOR - Extraction des chaînes localisables")))
        print()

    def is_ready(self) -> bool:
        """Vérifie si la configuration est prête pour lancer l'extraction."""
        return bool(self.plugin_path and os.path.isdir(self.plugin_path))

    def print_config(self):
        """Affiche la configuration actuelle."""
        print(c.title(_("Configuration:")))
        print()

        # Plugin path avec indicateur de validité
        if self.plugin_path:
            if os.path.isdir(self.plugin_path):
                status = f"{c.OK}OK{c.RESET}"
            else:
                status = f"{c.ERROR}" + _("INTROUVABLE") + f"{c.RESET}"
            print(c.config_line("1. " + _("Plugin ciblé"), f"{self.plugin_path} {c.VALUE}[{c.RESET}{status}{c.VALUE}]{c.RESET}"))
        else:
            print(c.config_line("1. " + _("Plugin ciblé"), f"{c.ERROR}" + _("(non défini - REQUIS)") + f"{c.RESET}"))

        # Répertoire de sortie
        if self.output_dir:
            print(c.config_line("2. " + _("Sortie"), self.output_dir))
        else:
            default_output = f"<plugin>/{get_i18n_dir()}/Extractor/<timestamp>/"
            print(c.config_line("2. " + _("Sortie"), f"{default_output} {c.DIM}" + _("(auto)") + f"{c.RESET}"))

        # Autres options
        print(c.config_line("3. " + _("Préfixe LOC"), self.prefix))
        print(c.config_line("4. " + _("Langue extraite"), self.lang))

        exclude_display = ', '.join(self.exclude_files) if self.exclude_files else _("(aucun)")
        print(c.config_line("5. " + _("Exclusions"), exclude_display))

        print(c.config_line("6. " + _("Long. min chaînes"), str(self.min_length)))

        ignore_display = f"{c.OK}" + _("Oui") + f"{c.RESET}" if self.ignore_log else f"{c.WARNING}" + _("Non") + f"{c.RESET}"
        print(c.config_line("7. " + _("Ignorer logs"), ignore_display))

        print()

    def print_menu(self):
        """Affiche les options du menu."""
        print(c.separator("─"))

        if self.is_ready():
            print(c.menu_option(_("ENTRÉE"), f"{c.GREEN}" + _("Lancer l'extraction") + f"{c.RESET}"))
        else:
            print(f"  {c.DIM}" + _("ENTRÉE") + "  " + _("Lancer l'extraction (configurer le plugin d'abord)") + f"{c.RESET}")

        print(c.menu_option("1-7", _("Modifier une option")))
        print(c.menu_option("0", _("Quitter")))
        print()

    def input_plugin_path(self) -> bool:
        """Demande le chemin du plugin."""
        print()
        print(c.title("1. " + _("Chemin du plugin Lightroom")))
        print(c.separator())
        print(_("Exemples:"))
        print(f"  {c.VALUE}C:\\Users\\User\\Lightroom\\plugin.lrplugin{c.RESET}")
        print(f"  {c.VALUE}./piwigoPublish.lrplugin{c.RESET}")
        print()

        if self.plugin_path:
            print(_("Actuel:") + f" {c.VALUE}{self.plugin_path}{c.RESET}")
            path = input(c.prompt(_("Nouveau chemin (ENTRÉE pour garder, x pour annuler):") + " ")).strip()
            if path.lower() == 'x':
                print(f"{c.DIM}" + _("Annulation") + f"{c.RESET}")
                return True  # Retour au menu
            if not path:
                print(c.success(_("Chemin inchangé")))
                return True
        else:
            path = input(c.prompt(_("Chemin du plugin (x pour annuler):") + " ")).strip()
            if path.lower() == 'x':
                print(f"{c.DIM}" + _("Annulation") + f"{c.RESET}")
                return True  # Retour au menu
            if not path:
                print(c.error(_("Chemin requis!")))
                return False

        is_valid, normalized_path, warning = validate_plugin_path(path)

        if not is_valid:
            print(c.error(warning))
            return False

        if warning:
            print(c.warning(warning))
            print("            " + _("Les plugins Lightroom doivent se terminer par .lrplugin"))
            confirm = input(c.prompt(_("Continuer quand même? [o/N]:") + " ")).strip().lower()
            if confirm not in ['o', 'oui', 'y', 'yes']:
                print(c.error(_("Configuration annulée")))
                return False

        self.plugin_path = normalized_path
        print(c.success(_("Plugin: {path}").format(path=normalized_path)))
        return True

    def input_output_dir(self):
        """Demande le répertoire de sortie (override optionnel)."""
        print()
        print(c.title("2. " + _("Répertoire de sortie")))
        print(c.separator())
        print(_("Par défaut:") + f" {c.VALUE}<plugin>/{get_i18n_dir()}/Extractor/<timestamp>/{c.RESET}")
        print()
        print(_("Pour forcer un autre emplacement, entrez un chemin."))
        print(_("Sinon, appuyez sur ENTRÉE pour utiliser le défaut."))
        print()

        if self.output_dir:
            print(_("Override actuel:") + f" {c.VALUE}{self.output_dir}{c.RESET}")

        path = input(c.prompt(_("Répertoire (ENTRÉE pour défaut):") + " ")).strip()

        if path:
            normalized_path = os.path.normpath(path)
            os.makedirs(normalized_path, exist_ok=True)
            self.output_dir = normalized_path
            print(c.success(_("Override: {path}").format(path=normalized_path)))
        else:
            self.output_dir = ""
            print(c.success(_("Utilisera: <plugin>/{dir}/Extractor/<timestamp>/").format(dir=get_i18n_dir())))

    def input_prefix(self):
        """Demande le préfixe LOC."""
        print()
        print(c.title("3. " + _("Préfixe des clés LOC")))
        print(c.separator())
        print(_("Exemples:") + f" {c.VALUE}$$$/Piwigo{c.RESET}, {c.VALUE}$$$/MyApp{c.RESET}")
        print()

        prefix = input(c.prompt(_("Préfixe [{prefix}]:").format(prefix=self.prefix) + " ")).strip()

        if prefix:
            self.prefix = prefix
            print(c.success(_("Préfixe: {prefix}").format(prefix=self.prefix)))
        else:
            print(c.success(_("Préfixe inchangé: {prefix}").format(prefix=self.prefix)))

    def input_lang(self):
        """Demande le code langue."""
        print()
        print(c.title("4. " + _("Code langue")))
        print(c.separator())
        print(_("Exemples:") + f" {c.VALUE}en{c.RESET} " + _("(anglais)") + f", {c.VALUE}fr{c.RESET} " + _("(français)") + f", {c.VALUE}de{c.RESET} " + _("(allemand)"))
        print()

        lang = input(c.prompt(_("Langue [{lang}]:").format(lang=self.lang) + " ")).strip().lower()

        if lang and len(lang) == 2:
            self.lang = lang
            print(c.success(_("Langue: {lang}").format(lang=self.lang)))
        elif lang:
            print(c.warning(_("Code invalide (2 caractères requis), valeur inchangée")))
        else:
            print(c.success(_("Langue inchangée: {lang}").format(lang=self.lang)))

    def input_exclude_files(self):
        """Demande les fichiers à exclure."""
        print()
        print(c.title("5. " + _("Fichiers à exclure")))
        print(c.separator())
        print(_("Exemples:") + f" {c.VALUE}JSON.lua, test.lua{c.RESET}")
        print()

        if self.exclude_files:
            print(_("Actuels:") + f" {c.VALUE}{', '.join(self.exclude_files)}{c.RESET}")

        files = input(c.prompt(_("Fichiers à exclure (virgule pour séparer):") + " ")).strip()

        if files:
            self.exclude_files = [f.strip() for f in files.split(',') if f.strip()]
            print(c.success(_("Exclusions: {files}").format(files=', '.join(self.exclude_files))))
        else:
            self.exclude_files = []
            print(c.success(_("Aucun fichier exclu")))

    def input_min_length(self):
        """Demande la longueur minimale des chaînes."""
        print()
        print(c.title("6. " + _("Longueur minimale des chaînes")))
        print(c.separator())
        print(_("Les chaînes plus courtes seront ignorées."))
        print()

        length = input(c.prompt(_("Longueur minimale [{n}]:").format(n=self.min_length) + " ")).strip()

        if not length:
            print(c.success(_("Longueur inchangée: {n}").format(n=self.min_length)))
            return

        try:
            length_int = int(length)
            if length_int >= 1:
                self.min_length = length_int
                print(c.success(_("Longueur minimale: {n}").format(n=self.min_length)))
            else:
                print(c.error(_("Doit être >= 1")))
        except ValueError:
            print(c.error(_("Valeur invalide")))

    def input_ignore_log(self):
        """Demande si les logs doivent être ignorés."""
        print()
        print(c.title("7. " + _("Ignorer les lignes de log")))
        print(c.separator())
        print(_("Ignore les lignes contenant log(), warn(), etc."))
        print()

        current = "O" if self.ignore_log else "N"
        response = input(c.prompt(_("Ignorer les logs? [{current}]:").format(current=current) + " ")).strip().lower()

        if response in ['o', 'y', 'oui', 'yes']:
            self.ignore_log = True
            print(c.success(_("Logs ignorés")))
        elif response in ['n', 'non', 'no']:
            self.ignore_log = False
            print(c.success(_("Logs inclus")))
        else:
            status = _("Oui") if self.ignore_log else _("Non")
            print(c.success(_("Option inchangée: {status}").format(status=status)))

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

            choice = input(c.prompt(_("Votre choix:") + " ")).strip()

            if choice == '0':
                print()
                print(_("Au revoir!"))
                return False

            elif choice == '' and self.is_ready():
                # Lancer directement
                print()
                print(c.success(_("Lancement de l'extraction...")))
                return True

            elif choice == '1':
                self.input_plugin_path()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

            elif choice == '2':
                self.input_output_dir()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

            elif choice == '3':
                self.input_prefix()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

            elif choice == '4':
                self.input_lang()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

            elif choice == '5':
                self.input_exclude_files()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

            elif choice == '6':
                self.input_min_length()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

            elif choice == '7':
                self.input_ignore_log()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

            elif choice == '':
                # ENTRÉE mais pas prêt
                print()
                print(c.error(_("Configurez d'abord le chemin du plugin (option 1)")))
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

            else:
                print()
                print(c.error(_("Choix invalide: \"{choice}\"").format(choice=choice)))
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE...") + f"{c.RESET}")

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
