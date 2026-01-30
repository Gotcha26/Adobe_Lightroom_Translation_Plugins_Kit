#!/usr/bin/env python3
"""
LocalizationToolkit.py

Script principal pour gérer tous les outils de localisation du plugin Lightroom.
Centralise la configuration (chemins) et permet de lancer les différents outils
depuis une interface unifiée.

Structure attendue:
    LocalizationToolkit.py      (ce fichier)
    config.json                 (configuration persistante)
    common/                    (module commun paths.py)
    1_Extractor/               (scripts d'extraction)
    2_Applicator/              (scripts d'application)
    3_TranslationManager/      (scripts de gestion traductions)
    9_Tools/                   (utilitaires)

Les outils generent leurs sorties dans:
    <plugin>/<temp_dir>/<Outil>/<timestamp_YYYYMMDD_HHMMSS>/
    (temp_dir configurable, defaut: __i18n_tmp__)

Usage:
    python LocalizationToolkit.py

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-30
Version : 2.1 - Dossier temporaire configurable (__i18n_tmp__ par defaut)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List

# Ajouter le répertoire courant au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common.paths import (
    get_i18n_kit_path, find_latest_tool_output, get_i18n_dir, set_i18n_dir,
    validate_plugin_path, DEFAULT_I18N_DIR, TIMESTAMP_LENGTH
)
from common.colors import Colors

# Instance couleurs
c = Colors()


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "plugin_path": r"D:\Gotcha\Documents\DIY\GitHub\LrC-PublishService\PiwigoPublish-lrc-plugin\piwigoPublish.lrplugin",
    "output_base_dir": "",  # Vide = à côté du script
    "prefix": "$$$/Piwigo",
    "lang": "en",
    "temp_dir": DEFAULT_I18N_DIR,  # Nom du dossier temporaire (__i18n_tmp__ par défaut)
    "last_extraction_dir": "",
    "last_used": ""
}

TOOL_DIRS = {
    "extractor": "1_Extractor",
    "applicator": "2_Applicator",
    "translation_manager": "3_Translation_manager",
    "tools": "9_Tools"
}


# =============================================================================
# GESTIONNAIRE DE CONFIGURATION
# =============================================================================

class ConfigManager:
    """Gère la configuration persistante."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_path = os.path.join(base_dir, CONFIG_FILE)
        self.config = self._load()

    def _load(self) -> Dict:
        """Charge la configuration depuis le fichier JSON."""
        config = DEFAULT_CONFIG.copy()
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Fusionner avec defaults pour nouvelles clés
                    config = {**DEFAULT_CONFIG, **loaded}
            except Exception as e:
                print(f"⚠️  Erreur lecture config: {e}")

        # Appliquer le nom du dossier temporaire
        temp_dir = config.get("temp_dir", DEFAULT_I18N_DIR)
        set_i18n_dir(temp_dir)

        return config

    def save(self):
        """Sauvegarde la configuration."""
        self.config["last_used"] = datetime.now().isoformat()
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Erreur sauvegarde config: {e}")

    def get(self, key: str, default=None):
        """Récupère une valeur de configuration."""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """Définit une valeur de configuration."""
        self.config[key] = value
        self.save()

    def display(self):
        """Affiche la configuration actuelle."""
        plugin_path = self.config.get('plugin_path', '')
        temp_dir = self.config.get('temp_dir', DEFAULT_I18N_DIR)
        i18n_path = get_i18n_kit_path(plugin_path) if plugin_path else '(non defini)'

        print()
        print(c.title("Configuration actuelle:"))
        print()
        print(c.config_line("Plugin path", plugin_path or f"{c.ERROR}(non défini){c.RESET}"))
        print(c.config_line("Dossier temporaire", temp_dir))
        print(c.config_line("Chemin complet", i18n_path))
        print(c.config_line("Préfixe LOC", self.config.get('prefix', '$$$/Piwigo')))
        print(c.config_line("Langue par défaut", self.config.get('lang', 'en')))
        print()

        # Afficher les exécutions récentes si le plugin est configuré
        if plugin_path and os.path.isdir(plugin_path):
            self._display_recent_executions(plugin_path)

    def _display_recent_executions(self, plugin_path: str):
        """Affiche les dernières exécutions de chaque outil."""
        print(f"   {c.DIM}Exécutions récentes dans {get_i18n_dir()}/:{c.RESET}")

        tools = ["Extractor", "Applicator", "TranslationManager"]

        for tool in tools:
            latest = find_latest_tool_output(plugin_path, tool)
            if latest:
                timestamp = os.path.basename(latest)
                formatted = self._format_timestamp(timestamp)
                print(f"     {c.KEY}{tool:20}{c.RESET} : {c.VALUE}{formatted}{c.RESET}")
            else:
                print(f"     {c.KEY}{tool:20}{c.RESET} : {c.DIM}(aucune){c.RESET}")

        print()

    def _format_timestamp(self, timestamp: str) -> str:
        """Formate un timestamp YYYYMMDD_HHMMSS en format lisible."""
        try:
            date_part = timestamp[:8]
            time_part = timestamp[9:15]
            return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
        except:
            return timestamp


# =============================================================================
# LANCEUR D'OUTILS
# =============================================================================

class ToolLauncher:
    """Lance les différents scripts d'outils."""

    def __init__(self, base_dir: str, config: ConfigManager):
        self.base_dir = base_dir
        self.config = config

    def _get_tool_path(self, category: str, script_name: str) -> Optional[str]:
        """Retourne le chemin complet d'un script."""
        tool_dir = TOOL_DIRS.get(category)
        if not tool_dir:
            return None

        path = os.path.join(self.base_dir, tool_dir, script_name)
        if os.path.exists(path):
            return path

        # Essayer sans le sous-dossier (structure plate)
        path_flat = os.path.join(self.base_dir, script_name)
        if os.path.exists(path_flat):
            return path_flat

        return None

    def _run_script(self, script_path: str, args: List[str] = None,
                    cwd: str = None) -> bool:
        """Exécute un script Python."""
        if not script_path or not os.path.exists(script_path):
            print(f"❌ Script introuvable: {script_path}")
            return False

        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)

        working_dir = cwd or os.path.dirname(script_path)

        try:
            print(f"\n🚀 Lancement: {os.path.basename(script_path)}")
            print(f"   Répertoire: {working_dir}")
            print("-" * 60)

            result = subprocess.run(
                cmd,
                cwd=working_dir,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )

            return result.returncode == 0
        except Exception as e:
            print(f"❌ Erreur exécution: {e}")
            return False

    def run_extractor(self, interactive: bool = True) -> bool:
        """Lance l'extracteur."""
        script = self._get_tool_path("extractor", "Extractor_main.py")

        if interactive:
            # Passer le plugin_path en tant que valeur par defaut
            plugin_path = self.config.get("plugin_path", "")
            if plugin_path and os.path.isdir(plugin_path):
                return self._run_script(script, ["--default-plugin", plugin_path])
            return self._run_script(script)
        else:
            # Mode CLI avec config
            plugin_path = self.config.get("plugin_path")
            prefix = self.config.get("prefix", "$$$/Piwigo")
            lang = self.config.get("lang", "en")
            output_dir = self.config.get("output_base_dir") or os.path.dirname(script)

            args = [
                "--plugin-path", plugin_path,
                "--prefix", prefix,
                "--lang", lang
            ]
            if output_dir:
                args.extend(["--output-dir", output_dir])

            return self._run_script(script, args)

    def run_applicator(self, interactive: bool = True) -> bool:
        """Lance l'applicateur."""
        script = self._get_tool_path("applicator", "Applicator_main.py")

        if interactive:
            # Passer le plugin_path en tant que valeur par defaut
            plugin_path = self.config.get("plugin_path", "")
            if plugin_path and os.path.isdir(plugin_path):
                return self._run_script(script, ["--default-plugin", plugin_path])
            return self._run_script(script)
        else:
            plugin_path = self.config.get("plugin_path")
            extraction_dir = self.config.get("last_extraction_dir")

            if not extraction_dir:
                print("[ERREUR] Aucune extraction precedente. Lancez d'abord l'Extractor.")
                return False

            args = [
                "--plugin-path", plugin_path,
                "--extraction-dir", extraction_dir,
                "--dry-run"
            ]

            return self._run_script(script, args)

    def run_translation_manager(self, interactive: bool = True) -> bool:
        """Lance le gestionnaire de traductions."""
        script = self._get_tool_path("translation_manager", "TranslationManager.py")

        if interactive:
            # Passer le plugin_path en tant que valeur par défaut
            plugin_path = self.config.get("plugin_path", "")
            if plugin_path and os.path.isdir(plugin_path):
                return self._run_script(script, ["--default-plugin", plugin_path])
            return self._run_script(script)
        else:
            # Mode CLI avec config
            plugin_path = self.config.get("plugin_path")
            if not plugin_path:
                print("[ERREUR] Plugin non configuré.")
                return False

            args = ["--plugin-path", plugin_path]
            return self._run_script(script, args)

    def run_restore_backup(self) -> bool:
        """Lance la restauration des backups."""
        script = self._get_tool_path("tools", "Restore_backup.py")
        return self._run_script(script)

    def run_delete_temp_dir(self) -> bool:
        """Lance la suppression du dossier temporaire."""
        script = self._get_tool_path("tools", "Delete_temp_dir.py")
        return self._run_script(script)

    def find_latest_extraction(self) -> Optional[str]:
        """Trouve le dossier d'extraction le plus récent dans __i18n_kit__."""
        plugin_path = self.config.get("plugin_path")
        if not plugin_path or not os.path.isdir(plugin_path):
            return None

        # Utiliser la fonction commune pour trouver la dernière extraction
        return find_latest_tool_output(plugin_path, "Extractor")


# =============================================================================
# MENU PRINCIPAL
# =============================================================================

class MainMenu:
    """Menu principal interactif."""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = ConfigManager(self.base_dir)
        self.launcher = ToolLauncher(self.base_dir, self.config)

    def clear_screen(self):
        """Efface l'écran."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        """Affiche l'en-tête."""
        print()
        print(c.box_header("LIGHTROOM PLUGIN LOCALIZATION TOOLKIT v2.1"))

        # Afficher le plugin configuré
        plugin = self.config.get("plugin_path", "")
        if plugin and os.path.isdir(plugin):
            plugin_name = os.path.basename(plugin)
            print(f"  Plugin: {c.VALUE}{plugin_name}{c.RESET} [{c.OK}OK{c.RESET}]")
        else:
            print(f"  {c.WARNING}Plugin non configuré ou introuvable{c.RESET}")

        print()

    def print_menu(self):
        """Affiche le menu principal."""
        print(c.title("OUTILS DE LOCALISATION"))
        print(c.separator())
        print(c.menu_option("1", "Extractor      - Extraire les chaînes"))
        print(c.menu_option("2", "Applicator     - Appliquer les localisations"))
        print(c.menu_option("3", "Translation    - Gérer les traductions"))
        print(c.menu_option("4", "Restore        - Restaurer les backups"))
        print(c.menu_option("5", f"{c.WARNING}Supprimer{c.RESET}      - Supprimer le dossier temporaire"))
        print()
        print(c.title("CONFIGURATION"))
        print(c.separator())
        print(c.menu_option("6", "Configurer le plugin"))
        print(c.menu_option("7", "Afficher la configuration"))
        print()
        print(c.menu_option("0", "Quitter"))
        print()

    def input_plugin_path(self):
        """Configure le chemin du plugin."""
        print()
        print(c.title("Configuration du chemin du plugin"))
        print(c.separator())

        current = self.config.get("plugin_path", "")
        if current:
            print(f"Actuel: {c.VALUE}{current}{c.RESET}")
            print()

        print("Exemples:")
        print(f"  {c.VALUE}D:\\Lightroom\\plugin.lrplugin{c.RESET}")
        print(f"  {c.VALUE}./piwigoPublish.lrplugin{c.RESET}")
        print()

        path = input(c.prompt("Nouveau chemin (ENTRÉE pour garder): ")).strip()

        if path:
            is_valid, normalized, warning = validate_plugin_path(path)

            if not is_valid:
                print(c.error(warning))
                return

            # Avertissement si pas .lrplugin
            if warning:
                print(c.warning(warning))
                print("            Les plugins Lightroom doivent se terminer par .lrplugin")
                confirm = input(c.prompt("Continuer quand même? [o/N]: ")).strip().lower()
                if confirm not in ['o', 'oui', 'y', 'yes']:
                    print(c.error("Configuration annulée"))
                    return

            self.config.set("plugin_path", normalized)
            print(c.success(f"Plugin configuré: {normalized}"))

            # Afficher le chemin du dossier temporaire
            i18n_path = get_i18n_kit_path(normalized)
            print(f"     Sorties dans: {c.VALUE}{i18n_path}{c.RESET}")
        else:
            print(c.success("Chemin inchangé"))

    def input_temp_dir(self):
        """Configure le nom du dossier temporaire."""
        print()
        print(c.title("Configuration du dossier temporaire"))
        print(c.separator())

        current = self.config.get("temp_dir", DEFAULT_I18N_DIR)
        print(f"Actuel: {c.VALUE}{current}{c.RESET}")
        print()
        print("Ce dossier est créé dans le plugin pour stocker les")
        print("fichiers générés par les outils (extractions, backups, etc.)")
        print()
        print(f"Exemples: {c.VALUE}__i18n_tmp__{c.RESET}, {c.VALUE}__i18n_kit__{c.RESET}, {c.VALUE}.i18n_work{c.RESET}")
        print()

        name = input(c.prompt("Nouveau nom (ENTRÉE pour garder): ")).strip()

        if name:
            # Valider le nom (pas de caractères invalides)
            invalid_chars = '<>:"/\\|?*'
            if any(char in name for char in invalid_chars):
                print(c.error(f"Caractères invalides dans le nom: {invalid_chars}"))
            else:
                self.config.set("temp_dir", name)
                set_i18n_dir(name)
                print(c.success(f"Dossier temporaire: {name}"))

                plugin_path = self.config.get("plugin_path", "")
                if plugin_path:
                    print(f"     Nouveau chemin: {c.VALUE}{get_i18n_kit_path(plugin_path)}{c.RESET}")
        else:
            print(c.success("Nom inchangé"))

    def configure_paths(self):
        """Menu de configuration des chemins."""
        self.clear_screen()
        print()
        print(c.box_header("CONFIGURATION"))
        print()

        print(c.menu_option("1", "Chemin du plugin"))
        print(c.menu_option("2", "Prefixe LOC"))
        print(c.menu_option("3", "Langue par defaut"))
        print(c.menu_option("4", "Dossier temporaire"))
        print(c.menu_option("0", "Retour"))
        print()

        choice = input(c.prompt("Votre choix: ")).strip()

        if choice == '1':
            self.input_plugin_path()
        elif choice == '2':
            current = self.config.get("prefix", "$$$/Piwigo")
            prefix = input(c.prompt(f"Préfixe LOC [{current}]: ")).strip()
            if prefix:
                self.config.set("prefix", prefix)
                print(c.success(f"Préfixe: {prefix}"))
        elif choice == '3':
            current = self.config.get("lang", "en")
            lang = input(c.prompt(f"Langue [{current}]: ")).strip().lower()
            if lang and len(lang) == 2:
                self.config.set("lang", lang)
                print(c.success(f"Langue: {lang}"))
        elif choice == '4':
            self.input_temp_dir()

        input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")

    def run(self):
        """Boucle principale du menu."""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()

            choice = input(c.prompt("Votre choix (0-7): ")).strip()

            if choice == '0':
                print("\nAu revoir!")
                break
            elif choice == '1':
                # Vérifier plugin
                plugin = self.config.get("plugin_path")
                if not plugin or not os.path.isdir(plugin):
                    print(c.warning("Plugin non configuré!"))
                    self.input_plugin_path()
                else:
                    self.launcher.run_extractor()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")
            elif choice == '2':
                plugin = self.config.get("plugin_path")
                if not plugin or not os.path.isdir(plugin):
                    print(c.warning("Plugin non configuré!"))
                    self.input_plugin_path()
                else:
                    self.launcher.run_applicator()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")
            elif choice == '3':
                self.launcher.run_translation_manager()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")
            elif choice == '4':
                self.launcher.run_restore_backup()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")
            elif choice == '5':
                self.launcher.run_delete_temp_dir()
                input(f"\n{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")
            elif choice == '6':
                self.configure_paths()
            elif choice == '7':
                self.config.display()
                input(f"{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")
            else:
                print(c.error("Choix invalide"))
                input(f"{c.DIM}Appuyez sur ENTRÉE pour continuer...{c.RESET}")


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    """Point d'entrée principal."""

    # Mode CLI?
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        base_dir = os.path.dirname(os.path.abspath(__file__))
        config = ConfigManager(base_dir)
        launcher = ToolLauncher(base_dir, config)

        if cmd in ['extract', 'extractor', '1']:
            success = launcher.run_extractor(interactive=len(sys.argv) == 2)
        elif cmd in ['apply', 'applicator', '2']:
            success = launcher.run_applicator(interactive=len(sys.argv) == 2)
        elif cmd in ['translate', 'translation', '3']:
            success = launcher.run_translation_manager()
        elif cmd in ['restore', '4']:
            success = launcher.run_restore_backup()
        elif cmd in ['delete', 'clean', '5']:
            success = launcher.run_delete_temp_dir()
        elif cmd == '--config':
            config.display()
            success = True
        else:
            print(f"Commande inconnue: {cmd}")
            print("\nUsage:")
            print("  python LocalizationToolkit.py           # Menu interactif")
            print("  python LocalizationToolkit.py extract   # Lancer Extractor")
            print("  python LocalizationToolkit.py apply     # Lancer Applicator")
            print("  python LocalizationToolkit.py translate # Lancer TranslationManager")
            print("  python LocalizationToolkit.py restore   # Lancer Restore")
            print("  python LocalizationToolkit.py delete    # Supprimer dossier temporaire")
            print("  python LocalizationToolkit.py --config  # Afficher config")
            success = False

        sys.exit(0 if success else 1)

    # Mode menu interactif
    menu = MainMenu()
    menu.run()


if __name__ == "__main__":
    main()
