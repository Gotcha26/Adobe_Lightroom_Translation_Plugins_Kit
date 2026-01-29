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
    <plugin>/__i18n_kit__/<Outil>/<timestamp_YYYYMMDD_HHMMSS>/

Usage:
    python LocalizationToolkit.py

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-29
Version : 2.0 - Support structure __i18n_kit__
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
    get_i18n_kit_path, find_latest_tool_output, I18N_KIT_DIR, TIMESTAMP_LENGTH
)


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "plugin_path": r"D:\Gotcha\Documents\DIY\GitHub\LrC-PublishService\PiwigoPublish-lrc-plugin\piwigoPublish.lrplugin",
    "output_base_dir": "",  # Vide = à côté du script
    "prefix": "$$$/Piwigo",
    "lang": "en",
    "last_extraction_dir": "",
    "last_used": ""
}

TOOL_DIRS = {
    "extractor": "1_Extractor",
    "applicator": "2_Applicator",
    "translation_manager": "3_TranslationManager",
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
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Fusionner avec defaults pour nouvelles clés
                    return {**DEFAULT_CONFIG, **loaded}
            except Exception as e:
                print(f"⚠️  Erreur lecture config: {e}")
        return DEFAULT_CONFIG.copy()
    
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
        i18n_kit_path = get_i18n_kit_path(plugin_path) if plugin_path else '(non defini)'

        print("\nConfiguration actuelle:")
        print(f"   Plugin path        : {plugin_path or '(non defini)'}")
        print(f"   __i18n_kit__ path  : {i18n_kit_path}")
        print(f"   Prefixe LOC        : {self.config.get('prefix', '$$$/Piwigo')}")
        print(f"   Langue par defaut  : {self.config.get('lang', 'en')}")
        print()

        # Afficher les exécutions récentes si le plugin est configuré
        if plugin_path and os.path.isdir(plugin_path):
            self._display_recent_executions(plugin_path)

    def _display_recent_executions(self, plugin_path: str):
        """Affiche les dernières exécutions de chaque outil."""
        print("   Executions recentes dans __i18n_kit__/:")

        tools = ["Extractor", "Applicator", "TranslationManager"]

        for tool in tools:
            latest = find_latest_tool_output(plugin_path, tool)
            if latest:
                timestamp = os.path.basename(latest)
                formatted = self._format_timestamp(timestamp)
                print(f"     {tool:20} : {formatted}")
            else:
                print(f"     {tool:20} : (aucune)")

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
            return self._run_script(script)
        else:
            plugin_path = self.config.get("plugin_path")
            extraction_dir = self.config.get("last_extraction_dir")
            
            if not extraction_dir:
                print("❌ Aucune extraction précédente. Lancez d'abord l'Extractor.")
                return False
            
            args = [
                "--plugin-path", plugin_path,
                "--extraction-dir", extraction_dir,
                "--dry-run"
            ]
            
            return self._run_script(script, args)
    
    def run_translation_manager(self, interactive: bool = True) -> bool:
        """Lance le gestionnaire de traductions."""
        script = self._get_tool_path("translation_manager", "TranslationManager_main.py")
        return self._run_script(script)
    
    def run_restore_backup(self) -> bool:
        """Lance la restauration des backups."""
        script = self._get_tool_path("tools", "Restore_backup.py")
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
        print("\n" + "=" * 70)
        print("  LIGHTROOM PLUGIN LOCALIZATION TOOLKIT v2.0".center(70))
        print("=" * 70)

        # Afficher le plugin configuré
        plugin = self.config.get("plugin_path", "")
        if plugin and os.path.isdir(plugin):
            plugin_name = os.path.basename(plugin)
            print(f"  Plugin: {plugin_name} [OK]".center(70))
        else:
            print("  !!! Plugin non configure ou introuvable".center(70))

        print("=" * 70 + "\n")
    
    def print_menu(self):
        """Affiche le menu principal."""
        print("OUTILS DE LOCALISATION")
        print("-" * 40)
        print("  1. Extractor      - Extraire les chaines")
        print("  2. Applicator     - Appliquer les localisations")
        print("  3. Translation    - Gerer les traductions")
        print("  4. Restore        - Restaurer les backups")
        print()
        print("CONFIGURATION")
        print("-" * 40)
        print("  5. Configurer le plugin")
        print("  6. Afficher la configuration")
        print()
        print("  0. Quitter")
        print()
    
    def input_plugin_path(self):
        """Configure le chemin du plugin."""
        print("\nConfiguration du chemin du plugin")
        print("-" * 60)

        current = self.config.get("plugin_path", "")
        if current:
            print(f"Actuel: {current}")
            print()

        print("Exemples:")
        print("  D:\\Lightroom\\plugin.lrplugin")
        print("  ./piwigoPublish.lrplugin")
        print()

        path = input("Nouveau chemin (ENTREE pour garder): ").strip()

        if path:
            normalized = os.path.normpath(path)
            if os.path.isdir(normalized):
                self.config.set("plugin_path", normalized)
                print(f"[OK] Plugin configure: {normalized}")

                # Afficher le chemin __i18n_kit__
                i18n_path = get_i18n_kit_path(normalized)
                print(f"     Sorties dans: {i18n_path}")
            else:
                print(f"[ERREUR] Repertoire introuvable: {normalized}")
        else:
            print("[OK] Chemin inchange")
    
    def configure_paths(self):
        """Menu de configuration des chemins."""
        self.clear_screen()
        print("\n" + "=" * 60)
        print("  CONFIGURATION".center(60))
        print("=" * 60 + "\n")

        print("1. Chemin du plugin")
        print("2. Prefixe LOC")
        print("3. Langue par defaut")
        print("0. Retour")
        print()

        choice = input("Votre choix: ").strip()

        if choice == '1':
            self.input_plugin_path()
        elif choice == '2':
            current = self.config.get("prefix", "$$$/Piwigo")
            prefix = input(f"Prefixe LOC [{current}]: ").strip()
            if prefix:
                self.config.set("prefix", prefix)
                print(f"[OK] Prefixe: {prefix}")
        elif choice == '3':
            current = self.config.get("lang", "en")
            lang = input(f"Langue [{current}]: ").strip().lower()
            if lang and len(lang) == 2:
                self.config.set("lang", lang)
                print(f"[OK] Langue: {lang}")

        input("\nAppuyez sur ENTREE pour continuer...")
    
    def run(self):
        """Boucle principale du menu."""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()

            choice = input("Votre choix (0-6): ").strip()

            if choice == '0':
                print("\nAu revoir!")
                break
            elif choice == '1':
                # Vérifier plugin
                plugin = self.config.get("plugin_path")
                if not plugin or not os.path.isdir(plugin):
                    print("\n!!! Plugin non configure!")
                    self.input_plugin_path()
                else:
                    self.launcher.run_extractor()
                input("\nAppuyez sur ENTREE pour continuer...")
            elif choice == '2':
                plugin = self.config.get("plugin_path")
                if not plugin or not os.path.isdir(plugin):
                    print("\n!!! Plugin non configure!")
                    self.input_plugin_path()
                else:
                    self.launcher.run_applicator()
                input("\nAppuyez sur ENTREE pour continuer...")
            elif choice == '3':
                self.launcher.run_translation_manager()
                input("\nAppuyez sur ENTREE pour continuer...")
            elif choice == '4':
                self.launcher.run_restore_backup()
                input("\nAppuyez sur ENTREE pour continuer...")
            elif choice == '5':
                self.configure_paths()
            elif choice == '6':
                self.config.display()
                input("Appuyez sur ENTREE pour continuer...")
            else:
                print("[ERREUR] Choix invalide")
                input("Appuyez sur ENTREE pour continuer...")


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
            print("  python LocalizationToolkit.py --config  # Afficher config")
            success = False
        
        sys.exit(0 if success else 1)
    
    # Mode menu interactif
    menu = MainMenu()
    menu.run()


if __name__ == "__main__":
    main()