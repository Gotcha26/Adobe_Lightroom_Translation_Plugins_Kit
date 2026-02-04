#!/usr/bin/env python3
"""
Nom du fichier : LocalizationToolKit.py

Dépendances : core.paths, core.colors, core.i18n, subprocess

Description :
Script principal pour gérer tous les outils de localisation du plugin Lightroom.
Centralise la configuration (chemins), la persistance des paramètres et lance les
différents outils (Extractor, Applicator, Translator, Restore, Delete) depuis
une interface unifiée. Gère également la configuration du plugin et du dossier
temporaire (__i18n_tmp__ par défaut, configurable).

Structure attendue:
    LocalizationToolKit.py      (ce fichier)
    config.json                 (configuration persistante)
    core/                       (modules communs)
    tools/
        ├── extractor/
        ├── applicator/
        ├── translator/
        └── toolbox/

Les outils génèrent leurs sorties dans:
    <plugin>/<temp_dir>/<Outil>/<timestamp_YYYYMMDD_HHMMSS>/

Usage CLI :
    python LocalizationToolkit.py               # Menu interactif
    python LocalizationToolkit.py extract       # Lancer Extractor
    python LocalizationToolkit.py apply         # Lancer Applicator
    python LocalizationToolkit.py translate     # Lancer Translator
    python LocalizationToolkit.py restore       # Lancer Restore
    python LocalizationToolkit.py delete        # Nettoyer dossier temporaire
    python LocalizationToolkit.py --config      # Afficher configuration

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

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
from core.paths import (
    get_i18n_kit_path, find_latest_tool_output, get_i18n_dir, set_i18n_dir,
    validate_plugin_path, DEFAULT_I18N_DIR, TIMESTAMP_LENGTH
)
from core.colors import Colors
from core.i18n import _

# Instance couleurs
c = Colors()


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_FILE       = "config.json"
CONFIG_LOCAL_FILE = "config.local.json"   # Surcharge locale, ignorée par git

DEFAULT_CONFIG = {
    "plugin_path": r"D:\Gotcha\Documents\DIY\GitHub\LrC-PublishService\PiwigoPublish-lrc-plugin\piwigoPublish.lrplugin",
    "output_base_dir": "",  # Vide = à côté du script
    "prefix": "$$$/Piwigo",
    "lang": "en",
    "temp_dir": DEFAULT_I18N_DIR,  # Nom du dossier temporaire (__i18n_tmp__ par défaut)
    "last_extraction_dir": "",
    "last_used": "",
    "enable_flip_anim": True,  # 🎬 Lancer Flip-anim.py au démarrage (true = activé, false = désactivé)
    "auto_add_gitignore": True  # Ajouter automatiquement le dossier temporaire au .gitignore du plugin
}

TOOL_DIRS = {
    "extractor": "tools/extractor",
    "applicator": "tools/applicator",
    "translator": "tools/translator",
    "tools": "tools/toolbox"
}


# =============================================================================
# GESTIONNAIRE DE CONFIGURATION
# =============================================================================

class ConfigManager:
    """Gère la configuration persistante."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_path       = os.path.join(base_dir, CONFIG_FILE)
        self.config_local_path = os.path.join(base_dir, CONFIG_LOCAL_FILE)
        self.config = self._load()

    # ------------------------------------------------------------------
    # Ordre de priorité :  DEFAULT_CONFIG  <  config.json  <  config.local.json
    # ------------------------------------------------------------------
    def _load(self) -> Dict:
        """Charge la configuration depuis le fichier JSON.

        config.local.json (si présent) écrase les valeurs de config.json.
        Ce fichier est ignoré par git : utilisez-le pour des surcharges locales.
        """
        config = DEFAULT_CONFIG.copy()

        # 1) Charger config.json (base partagée)
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = {**config, **json.load(f)}
            except Exception as e:
                print(_("Erreur lecture config: {error}").format(error=e))

        # 2) Surcharger avec config.local.json (local, non versionnée)
        if os.path.exists(self.config_local_path):
            try:
                with open(self.config_local_path, 'r', encoding='utf-8') as f:
                    config = {**config, **json.load(f)}
            except Exception as e:
                print(_("Erreur lecture config locale: {error}").format(error=e))

        # Appliquer le nom du dossier temporaire
        set_i18n_dir(config.get("temp_dir", DEFAULT_I18N_DIR))

        return config

    def save(self):
        """Sauvegarde la configuration."""
        self.config["last_used"] = datetime.now().isoformat()
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(_("Erreur sauvegarde config: {error}").format(error=e))

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
        i18n_path = get_i18n_kit_path(plugin_path) if plugin_path else _('(non défini)')

        print()
        print(c.title(_("Configuration actuelle:")))
        print()
        print(c.config_line(_("Plugin path"), str(plugin_path or f"{c.ERROR}" + _("(non défini)") + f"{c.RESET}")))
        print(c.config_line(_("Dossier temporaire"), str(temp_dir)))
        print(c.config_line(_("Chemin complet"), str(i18n_path)))
        print(c.config_line(_("Préfixe LOC"), str(self.config.get('prefix', '$$$/Piwigo'))))
        print(c.config_line(_("Langue par défaut"), str(self.config.get('lang', 'en'))))
        print()

        # Afficher les exécutions récentes si le plugin est configuré
        if plugin_path and os.path.isdir(plugin_path):
            self._display_recent_executions(plugin_path)

    def _display_recent_executions(self, plugin_path: str):
        """Affiche les dernières exécutions de chaque outil."""
        print(f"   {c.DIM}" + _("Exécutions récentes dans {dir}/:").format(dir=get_i18n_dir()) + f"{c.RESET}")

        tools = ["Extractor", "Applicator", "Translator"]

        for tool in tools:
            latest = find_latest_tool_output(plugin_path, tool)
            if latest:
                timestamp = os.path.basename(latest)
                formatted = self._format_timestamp(timestamp)
                print(f"     {c.KEY}{tool:20}{c.RESET} : {c.VALUE}{formatted}{c.RESET}")
            else:
                print(f"     {c.KEY}{tool:20}{c.RESET} : {c.DIM}" + _("(aucune)") + f"{c.RESET}")

        print()

    def _format_timestamp(self, timestamp: str) -> str:
        """Formate un timestamp YYYYMMDD_HHMMSS en format lisible."""
        try:
            date_part = timestamp[:8]
            time_part = timestamp[9:15]
            return f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
        except:
            return timestamp

    def add_temp_dir_to_gitignore(self, plugin_path: str) -> bool:
        """Ajoute le dossier temporaire au .gitignore du plugin si nécessaire.

        Args:
            plugin_path: Chemin vers le plugin

        Returns:
            True si ajouté ou déjà présent, False si erreur
        """
        if not self.config.get("auto_add_gitignore", True):
            return True  # Option désactivée, on considère que c'est OK

        if not plugin_path or not os.path.isdir(plugin_path):
            return False

        # Chercher le dossier .git (peut être dans le plugin ou son parent)
        git_dir = os.path.join(plugin_path, ".git")
        git_root = plugin_path

        if not os.path.exists(git_dir):
            # Essayer dans le dossier parent
            parent_dir = os.path.dirname(plugin_path)
            git_dir = os.path.join(parent_dir, ".git")
            if os.path.exists(git_dir):
                git_root = parent_dir
            else:
                return True  # Pas de dépôt git, rien à faire

        gitignore_path = os.path.join(git_root, ".gitignore")
        temp_dir = self.config.get("temp_dir", DEFAULT_I18N_DIR)

        # Ligne à ajouter - chemin relatif depuis la racine git
        if git_root == plugin_path:
            # .git est dans le plugin lui-même
            ignore_line = f"{temp_dir}/"
        else:
            # .git est dans le parent, inclure le nom du plugin
            plugin_name = os.path.basename(plugin_path)
            ignore_line = f"{plugin_name}/{temp_dir}/"

        try:
            # Lire le .gitignore existant
            existing_lines = []
            if os.path.exists(gitignore_path):
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    existing_lines = [line.rstrip('\n\r') for line in f.readlines()]

            # Vérifier si déjà présent (avec ou sans / final)
            if ignore_line in existing_lines or temp_dir in existing_lines:
                return True  # Déjà présent

            # Ajouter la ligne
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                # Ajouter une ligne vide si le fichier n'est pas vide et ne se termine pas par une ligne vide
                if existing_lines and existing_lines[-1].strip():
                    f.write('\n')
                f.write(f"# {_('Dossier temporaire pour les outils de localisation')}\n")
                f.write(f"{ignore_line}\n")

            print(f"     {c.OK}[OK]{c.RESET} " + _("Ajouté '{line}' au .gitignore").format(line=ignore_line))
            return True

        except Exception as e:
            print(f"     {c.WARNING}[!]{c.RESET} " + _("Impossible d'ajouter au .gitignore: {error}").format(error=e))
            return False

    def prompt_add_to_gitignore(self, plugin_path: str) -> bool:
        """Demande à l'utilisateur s'il veut ajouter le dossier temporaire au .gitignore.

        Args:
            plugin_path: Chemin vers le plugin

        Returns:
            True si l'utilisateur a accepté et l'ajout a réussi, False sinon
        """
        if not self.config.get("auto_add_gitignore", True):
            return False  # Option désactivée

        if not plugin_path or not os.path.isdir(plugin_path):
            return False

        # Chercher le dossier .git
        git_dir = os.path.join(plugin_path, ".git")
        git_root = plugin_path

        if not os.path.exists(git_dir):
            parent_dir = os.path.dirname(plugin_path)
            git_dir = os.path.join(parent_dir, ".git")
            if os.path.exists(git_dir):
                git_root = parent_dir
            else:
                return False  # Pas de dépôt git

        gitignore_path = os.path.join(git_root, ".gitignore")
        temp_dir = self.config.get("temp_dir", DEFAULT_I18N_DIR)

        # Calculer la ligne à ajouter
        if git_root == plugin_path:
            ignore_line = f"{temp_dir}/"
        else:
            plugin_name = os.path.basename(plugin_path)
            ignore_line = f"{plugin_name}/{temp_dir}/"

        # Vérifier si déjà présent
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    existing_lines = [line.rstrip('\n\r') for line in f.readlines()]

                if ignore_line in existing_lines or temp_dir in existing_lines:
                    return False  # Déjà présent, pas besoin de demander
            except Exception:
                return False

        # Demander à l'utilisateur
        print()
        print(f"{c.WARNING}" + _("Le dossier temporaire '{dir}' n'est pas dans le .gitignore").format(dir=temp_dir) + f"{c.RESET}")
        print(_("Voulez-vous l'ajouter automatiquement ?"))
        print(f"  " + _("Ligne à ajouter:") + f" {c.VALUE}{ignore_line}{c.RESET}")
        print()
        response = input(f"{c.PROMPT}" + _("Ajouter au .gitignore? [O/n]:") + f" {c.RESET}").strip().lower()

        if response in ['', 'o', 'oui', 'y', 'yes']:
            return self.add_temp_dir_to_gitignore(plugin_path)

        return False

    def check_gitignore_status(self, plugin_path: str) -> str:
        """Vérifie le statut du dossier temporaire dans le .gitignore.

        Args:
            plugin_path: Chemin vers le plugin

        Returns:
            Chaîne de statut formatée pour l'affichage
        """
        if not plugin_path or not os.path.isdir(plugin_path):
            return ""

        # Chercher le dossier .git (peut être dans le plugin ou son parent)
        git_dir = os.path.join(plugin_path, ".git")
        git_root = plugin_path

        if not os.path.exists(git_dir):
            # Essayer dans le dossier parent
            parent_dir = os.path.dirname(plugin_path)
            git_dir = os.path.join(parent_dir, ".git")
            if os.path.exists(git_dir):
                git_root = parent_dir
            else:
                return f"  {c.DIM}.gitignore: N/A " + _("(pas de dépôt git)") + f"{c.RESET}"

        gitignore_path = os.path.join(git_root, ".gitignore")
        temp_dir = self.config.get("temp_dir", DEFAULT_I18N_DIR)

        # Ligne à chercher - chemin relatif depuis la racine git
        if git_root == plugin_path:
            ignore_line = f"{temp_dir}/"
        else:
            plugin_name = os.path.basename(plugin_path)
            ignore_line = f"{plugin_name}/{temp_dir}/"

        # Vérifier si le .gitignore existe
        if not os.path.exists(gitignore_path):
            return f"  {c.WARNING}.gitignore: " + _("Absent") + f"{c.RESET}"

        # Vérifier si le dossier temporaire est dans le .gitignore
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                existing_lines = [line.rstrip('\n\r') for line in f.readlines()]

            # Chercher plusieurs variantes possibles
            found = any(
                line in existing_lines
                for line in [ignore_line, ignore_line.rstrip('/'), temp_dir, f"{temp_dir}/"]
            )

            if found:
                return f"{c.OK}.gitignore: OK{c.RESET}"
            else:
                auto_enabled = self.config.get("auto_add_gitignore", True)
                if auto_enabled:
                    return f"{c.ERROR}" + _("Exception .gitignore - sera ajouté") + f"{c.RESET}"
                else:
                    return f"{c.WARNING}" + _("Exception .gitignore - manquant") + f"{c.RESET}"
        except Exception:
            return f"  {c.ERROR}.gitignore: " + _("Erreur lecture") + f"{c.RESET}"


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

    def _run_script(self, script_path: Optional[str], args: Optional[List[str]] = None,
                    cwd: Optional[str] = None) -> bool:
        """Exécute un script Python."""
        if not script_path or not os.path.exists(script_path):
            print(_("Script introuvable: {path}").format(path=script_path))
            return False

        # Scripts dans tools/ doivent être lancés avec -m pour préserver
        # le contexte de package nécessaire aux imports relatifs (from .xxx)
        tools_dir = os.path.join(self.base_dir, "tools")
        abs_script = os.path.abspath(script_path)
        if abs_script.startswith(os.path.abspath(tools_dir) + os.sep):
            rel = os.path.relpath(abs_script, self.base_dir)
            module_path = rel.replace(os.sep, ".").replace(".py", "")
            cmd = [sys.executable, "-m", module_path]
            working_dir = cwd or self.base_dir
        else:
            cmd = [sys.executable, script_path]
            working_dir = cwd or os.path.dirname(script_path)

        if args:
            cmd.extend(args)

        try:
            print(f"\n" + _("Lancement:") + f" {os.path.basename(script_path)}")
            print(_("Répertoire:") + f" {working_dir}")
            print("-" * 60)

            result = subprocess.run(
                cmd,
                cwd=working_dir,
                env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
            )

            return result.returncode == 0
        except Exception as e:
            print(_("[ERREUR] Erreur exécution: {error}").format(error=e))
            return False

    def run_extractor(self, interactive: bool = True) -> bool:
        """Lance l'extracteur."""
        script = self._get_tool_path("extractor", "main.py")

        if not script:
            print(_("Erreur: Script Extractor introuvable"))
            return False

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
        script = self._get_tool_path("applicator", "main.py")

        if not script:
            print(_("Erreur: Script Applicator introuvable"))
            return False

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
                print(_("[ERREUR] Aucune extraction précédente. Lancez d'abord l'Extractor."))
                return False

            args = [
                "--plugin-path", plugin_path,
                "--extraction-dir", extraction_dir,
                "--dry-run"
            ]

            return self._run_script(script, args)

    def run_translation_manager(self, interactive: bool = True) -> bool:
        """Lance le gestionnaire de traductions."""
        script = self._get_tool_path("translator", "main.py")

        if not script:
            print(_("Erreur: Script Translator introuvable"))
            return False

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
                print(_("[ERREUR] Plugin non configuré."))
                return False

            args = ["--plugin-path", plugin_path]
            return self._run_script(script, args)


    def run_restore_backup(self) -> bool:
        """Lance la restauration des backups."""
        script = self._get_tool_path("tools", "restore_backup.py")

        if not script:
            print(_("Erreur: Script Restore introuvable"))
            return False

        # Passer le plugin_path en tant que valeur par défaut
        plugin_path = self.config.get("plugin_path", "")
        if plugin_path and os.path.isdir(plugin_path):
            return self._run_script(script, ["--default-plugin", plugin_path])
        return self._run_script(script)

    def run_delete_temp_dir(self) -> bool:
        """Lance la suppression du dossier temporaire."""
        script = self._get_tool_path("tools", "delete_temp_dir.py")

        if not script:
            print(_("Erreur: Script Delete introuvable"))
            return False

        # Passer le plugin_path en tant que valeur par défaut
        plugin_path = self.config.get("plugin_path", "")
        if plugin_path and os.path.isdir(plugin_path):
            return self._run_script(script, ["--default-plugin", plugin_path])
        return self._run_script(script)

    def find_latest_extraction(self) -> Optional[str]:
        """Trouve le dossier d'extraction le plus récent dans __i18n_tmp__."""
        plugin_path = self.config.get("plugin_path")
        if not plugin_path or not os.path.isdir(plugin_path):
            return None

        # Utiliser la fonction commune pour trouver la dernière extraction
        return find_latest_tool_output(plugin_path, "Extractor")

    def run_flip_anim(self) -> bool:
        """Lance l'animation Flip-anim.py.

        🎬 Cette animation s'exécute au démarrage du menu interactif.
        """
        script = os.path.join(self.base_dir, "assets", "flip_anim.py")
        return self._run_script(script)


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
        print(c.box_header("LIGHTROOM PLUGIN LOCALIZATION TOOLKIT"))

        # Afficher le plugin configuré
        plugin = self.config.get("plugin_path", "")
        if plugin and os.path.isdir(plugin):
            plugin_name = os.path.basename(plugin)

            # Afficher le statut .gitignore sur la même ligne
            gitignore_status = self.config.check_gitignore_status(plugin)
            if gitignore_status:
                # Le statut commence par des espaces, on les supprime et on ajoute le séparateur
                compact_status = gitignore_status.strip()
                print(f"  Plugin: {c.VALUE}{plugin_name}{c.RESET} [{c.OK}OK{c.RESET}] | {compact_status}")
            else:
                print(f"  Plugin: {c.VALUE}{plugin_name}{c.RESET} [{c.OK}OK{c.RESET}]")
        else:
            print(f"  {c.WARNING}" + _("Plugin non configuré ou introuvable") + f"{c.RESET}")

        print()

    def print_menu(self):
        """Affiche le menu principal."""
        print(c.title(_("OUTILS DE LOCALISATION")))
        print(c.separator())
        print(c.menu_option("1", _("Extractor      - Extraire les chaînes")))
        print(c.menu_option("2", _("Applicator     - Appliquer les localisations")))
        print(c.menu_option("3", _("Translation    - Gérer les traductions")))
        print(c.menu_option("4", _("Restore        - Restaurer les backups")))
        print(c.menu_option("5", f"{c.WARNING}" + _("Supprimer") + f"{c.RESET}      - " + _("Nettoyer le dossier temporaire")))
        print()
        print(c.title(_("CONFIGURATION")))
        print(c.separator())
        print(c.menu_option("6", _("Configuration du plugin")))
        print()
        print(c.menu_option("0", _("Quitter")))
        print()

    def input_plugin_path(self):
        """Configure le chemin du plugin."""
        print()
        print(c.title(_("Configuration du chemin du plugin")))
        print(c.separator())

        current = self.config.get("plugin_path", "")
        if current:
            print(_("Actuel:") + f" {c.VALUE}{current}{c.RESET}")
            print()

        print(_("Exemples:"))
        print(f"  {c.VALUE}D:\\Lightroom\\plugin.lrplugin{c.RESET}")
        print(f"  {c.VALUE}./piwigoPublish.lrplugin{c.RESET}")
        print()

        path = input(c.prompt(_("Nouveau chemin (ENTRÉE pour garder):") + " ")).strip()

        if path:
            is_valid, normalized, warning = validate_plugin_path(path)

            if not is_valid:
                print(c.error(warning))
                return

            # Avertissement si pas .lrplugin
            if warning:
                print(c.warning(warning))
                print("            " + _("Les plugins Lightroom doivent se terminer par .lrplugin"))
                confirm = input(c.prompt(_("Continuer quand même? [o/N]:") + " ")).strip().lower()
                if confirm not in ['o', 'oui', 'y', 'yes']:
                    print(c.error(_("Configuration annulée")))
                    return

            self.config.set("plugin_path", normalized)
            print(c.success(_("Plugin configuré: {path}").format(path=normalized)))

            # Afficher le chemin du dossier temporaire
            i18n_path = get_i18n_kit_path(normalized)
            print(f"     " + _("Sorties dans:") + f" {c.VALUE}{i18n_path}{c.RESET}")
        else:
            print(c.success(_("Chemin inchangé")))

    def input_temp_dir(self):
        """Configure le nom du dossier temporaire."""
        print()
        print(c.title(_("Configuration du dossier temporaire")))
        print(c.separator())

        current = self.config.get("temp_dir", DEFAULT_I18N_DIR)
        print(_("Actuel:") + f" {c.VALUE}{current}{c.RESET}")
        print()
        print(_("Ce dossier est créé dans le plugin pour stocker les"))
        print(_("fichiers générés par les outils (extractions, backups, etc.)"))
        print()
        print(_("Exemples:") + f" {c.VALUE}__i18n_tmp__{c.RESET}, {c.VALUE}__i18n_kit__{c.RESET}, {c.VALUE}.i18n_work{c.RESET}")
        print()

        name = input(c.prompt(_("Nouveau nom (ENTRÉE pour garder):") + " ")).strip()

        if name:
            # Valider le nom (pas de caractères invalides)
            invalid_chars = '<>:"/\\|?*'
            if any(char in name for char in invalid_chars):
                print(c.error(_("Caractères invalides dans le nom: {chars}").format(chars=invalid_chars)))
            else:
                self.config.set("temp_dir", name)
                set_i18n_dir(name)
                print(c.success(_("Dossier temporaire: {name}").format(name=name)))

                plugin_path = self.config.get("plugin_path", "")
                if plugin_path:
                    print(f"     " + _("Nouveau chemin:") + f" {c.VALUE}{get_i18n_kit_path(plugin_path)}{c.RESET}")
        else:
            print(c.success(_("Nom inchangé")))

    def configure_paths(self):
        """Menu de configuration avec affichage et édition des paramètres."""
        self.clear_screen()
        print()
        print(c.box_header("CONFIGURATION"))
        print()

        # Afficher la configuration actuelle
        plugin_path = self.config.get('plugin_path', '')
        temp_dir = self.config.get('temp_dir', DEFAULT_I18N_DIR)
        i18n_path = get_i18n_kit_path(plugin_path) if plugin_path else '(non défini)'
        prefix = self.config.get('prefix', '$$$/Piwigo')
        lang = self.config.get('lang', 'en')
        auto_gitignore = self.config.get("auto_add_gitignore", True)
        enable_flip = self.config.get("enable_flip_anim", True)

        print(c.title(_("Paramètres actuels:")))
        print()
        print(c.config_line("1. " + _("Plugin path"), str(plugin_path or f"{c.ERROR}" + _("(non défini)") + f"{c.RESET}")))
        print(c.config_line("2. " + _("Dossier temporaire"), str(temp_dir)))
        print(c.config_line("   " + _("Chemin complet"), str(i18n_path)))

        # Auto-ajout .gitignore
        gitignore_status = f"{c.OK}" + _("activé") + f"{c.RESET}" if auto_gitignore else f"{c.DIM}" + _("désactivé") + f"{c.RESET}"
        print(c.config_line("3. " + _("Auto-ajout .gitignore"), str(gitignore_status)))

        # Animation
        flip_status = f"{c.OK}" + _("activée") + f"{c.RESET}" if enable_flip else f"{c.DIM}" + _("désactivée") + f"{c.RESET}"
        print(c.config_line("4. " + _("Animation au démarrage"), str(flip_status)))

        print(c.config_line("5. " + _("Préfixe LOC"), str(prefix)))
        print(c.config_line("6. " + _("Langue par défaut"), str(lang)))
        print()

        # Afficher les exécutions récentes si le plugin est configuré
        if plugin_path and os.path.isdir(plugin_path):
            print(f"   {c.DIM}" + _("Exécutions récentes dans {dir}/:").format(dir=get_i18n_dir()) + f"{c.RESET}")
            tools = ["Extractor", "Applicator", "Translator"]
            for tool in tools:
                latest = find_latest_tool_output(plugin_path, tool)
                if latest:
                    timestamp = os.path.basename(latest)
                    formatted = self.config._format_timestamp(timestamp)
                    print(f"     {c.KEY}{tool:20}{c.RESET} : {c.VALUE}{formatted}{c.RESET}")
                else:
                    print(f"     {c.KEY}{tool:20}{c.RESET} : {c.DIM}(aucune){c.RESET}")
            print()

        print(c.separator())
        print(f"{c.DIM}" + _("Entrez le numéro d'un paramètre pour le modifier, ou 0 pour revenir") + f"{c.RESET}")
        print()

        choice = input(c.prompt(_("Votre choix (0-6):") + " ")).strip()

        if choice == '0':
            # Retour au menu principal sans validation
            return
        elif choice == '1':
            self.input_plugin_path()
        elif choice == '2':
            self.input_temp_dir()
        elif choice == '3':
            # Toggle auto-ajout .gitignore
            current = self.config.get("auto_add_gitignore", True)
            new_value = not current
            self.config.set("auto_add_gitignore", new_value)
            status = _("activé") if new_value else _("désactivé")
            print(c.success(_("Auto-ajout au .gitignore: {status}").format(status=status)))
            print()
            temp_dir_name = self.config.get('temp_dir', DEFAULT_I18N_DIR)
            if new_value:
                print(_("Le dossier '{dir}' sera automatiquement ajouté au .gitignore du plugin").format(dir=temp_dir_name))
            else:
                print(_("Le dossier '{dir}' ne sera pas ajouté automatiquement au .gitignore").format(dir=temp_dir_name))
        elif choice == '4':
            # Toggle animation Flip-anim
            current = self.config.get("enable_flip_anim", True)
            new_value = not current
            self.config.set("enable_flip_anim", new_value)
            status = _("activée") if new_value else _("désactivée")
            print(c.success(_("Animation au démarrage: {status}").format(status=status)))
        elif choice == '5':
            # Modifier le préfixe
            print()
            print(c.title(_("Préfixe de localisation")))
            print(c.separator())
            print(_("Actuel:") + f" {c.VALUE}{prefix}{c.RESET}")
            print()
            new_prefix = input(c.prompt(_("Nouveau préfixe (ENTRÉE pour garder):") + " ")).strip()
            if new_prefix:
                self.config.set("prefix", new_prefix)
                print(c.success(_("Préfixe: {prefix}").format(prefix=new_prefix)))
            else:
                print(c.success(_("Préfixe inchangé")))
        elif choice == '6':
            # Modifier la langue
            print()
            print(c.title(_("Langue par défaut")))
            print(c.separator())
            print(_("Actuelle:") + f" {c.VALUE}{lang}{c.RESET}")
            print()
            print(_("Exemples:") + f" {c.VALUE}en{c.RESET}, {c.VALUE}fr{c.RESET}, {c.VALUE}es{c.RESET}, {c.VALUE}de{c.RESET}")
            print()
            new_lang = input(c.prompt(_("Nouvelle langue (ENTRÉE pour garder):") + " ")).strip()
            if new_lang:
                self.config.set("lang", new_lang)
                print(c.success(_("Langue: {lang}").format(lang=new_lang)))
            else:
                print(c.success(_("Langue inchangée")))

        input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE pour continuer...") + f"{c.RESET}")

    def run(self):
        """Boucle principale du menu."""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()

            choice = input(c.prompt(_("Votre choix (0-6):") + " ")).strip()

            if choice == '0':
                print("\n" + _("Au revoir!"))
                break
            elif choice == '1':
                # Vérifier plugin
                plugin = self.config.get("plugin_path")
                if not plugin or not os.path.isdir(plugin):
                    print(c.warning(_("Plugin non configuré!")))
                    self.input_plugin_path()
                else:
                    # Demander d'ajouter au .gitignore si nécessaire
                    self.config.prompt_add_to_gitignore(plugin)
                    self.launcher.run_extractor()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE pour continuer...") + f"{c.RESET}")
            elif choice == '2':
                plugin = self.config.get("plugin_path")
                if not plugin or not os.path.isdir(plugin):
                    print(c.warning(_("Plugin non configuré!")))
                    self.input_plugin_path()
                else:
                    # Demander d'ajouter au .gitignore si nécessaire
                    self.config.prompt_add_to_gitignore(plugin)
                    self.launcher.run_applicator()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE pour continuer...") + f"{c.RESET}")
            elif choice == '3':
                plugin = self.config.get("plugin_path")
                # Demander d'ajouter au .gitignore si nécessaire
                if plugin and os.path.isdir(plugin):
                    self.config.prompt_add_to_gitignore(plugin)
                self.launcher.run_translation_manager()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE pour continuer...") + f"{c.RESET}")
            elif choice == '4':
                self.launcher.run_restore_backup()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE pour continuer...") + f"{c.RESET}")
            elif choice == '5':
                self.launcher.run_delete_temp_dir()
                input(f"\n{c.DIM}" + _("Appuyez sur ENTRÉE pour continuer...") + f"{c.RESET}")
            elif choice == '6':
                self.configure_paths()
            else:
                print(c.error(_("Choix invalide")))
                input(f"{c.DIM}" + _("Appuyez sur ENTRÉE pour continuer...") + f"{c.RESET}")


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
            print(_("Commande inconnue: {cmd}").format(cmd=cmd))
            print("\n" + _("Usage:"))
            print("  python LocalizationToolkit.py           # " + _("Menu interactif"))
            print("  python LocalizationToolkit.py extract   # " + _("Lancer Extractor"))
            print("  python LocalizationToolkit.py apply     # " + _("Lancer Applicator"))
            print("  python LocalizationToolkit.py translate # " + _("Lancer Translator"))
            print("  python LocalizationToolkit.py restore   # " + _("Lancer Restore"))
            print("  python LocalizationToolkit.py delete    # " + _("Supprimer dossier temporaire"))
            print("  python LocalizationToolkit.py --config  # " + _("Afficher config"))
            success = False

        sys.exit(0 if success else 1)

    # Mode menu interactif
    menu = MainMenu()

    # 🎬 Lancer l'animation au démarrage (si activée dans config.json)
    if menu.config.get("enable_flip_anim", True):
        menu.launcher.run_flip_anim()

    menu.run()


if __name__ == "__main__":
    main()
