#!/usr/bin/env python3
"""
LocalizationToolkit.py

Script principal pour gérer tous les outils de localisation du plugin Lightroom.
Centralise la configuration (chemins) et permet de lancer les différents outils
depuis une interface unifiée.

Structure attendue:
    LocalizationToolkit.py      (ce fichier)
    config.json                 (configuration persistante)
    1_Extractor/               (scripts d'extraction)
    2_Applicator/              (scripts d'application)
    3_TranslationManager/      (scripts de gestion traductions)
    9_Tools/                   (utilitaires)

Usage:
    python LocalizationToolkit.py

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-28
Version : 1.0
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List


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
        print("\n📋 Configuration actuelle:")
        print(f"   Plugin path        : {self.config.get('plugin_path', '(non défini)')}")
        print(f"   Output base dir    : {self.config.get('output_base_dir') or '(à côté du script)'}")
        print(f"   Préfixe LOC        : {self.config.get('prefix', '$$$/Piwigo')}")
        print(f"   Langue par défaut  : {self.config.get('lang', 'en')}")
        print(f"   Dernière extraction: {self.config.get('last_extraction_dir') or '(aucune)'}")
        print()


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
        """Trouve le dossier d'extraction le plus récent."""
        output_dir = self.config.get("output_base_dir")
        if not output_dir:
            # Chercher dans le dossier Extractor
            extractor_dir = os.path.join(self.base_dir, TOOL_DIRS["extractor"])
            if os.path.isdir(extractor_dir):
                output_dir = extractor_dir
            else:
                output_dir = self.base_dir
        
        latest_dir = None
        latest_time = None
        
        try:
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                
                # Format YYYYMMDD_hhmmss
                if os.path.isdir(item_path) and len(item) == 15 and item[8] == '_':
                    try:
                        if os.path.exists(os.path.join(item_path, "replacements.json")):
                            item_time = datetime.strptime(item, '%Y%m%d_%H%M%S')
                            if latest_time is None or item_time > latest_time:
                                latest_time = item_time
                                latest_dir = item_path
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return latest_dir


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
        print("  🔧 LIGHTROOM PLUGIN LOCALIZATION TOOLKIT".center(70))
        print("=" * 70)
        
        # Afficher le plugin configuré
        plugin = self.config.get("plugin_path", "")
        if plugin and os.path.isdir(plugin):
            plugin_name = os.path.basename(plugin)
            print(f"  Plugin: {plugin_name} ✓".center(70))
        else:
            print("  ⚠️  Plugin non configuré ou introuvable".center(70))
        
        print("=" * 70 + "\n")
    
    def print_menu(self):
        """Affiche le menu principal."""
        print("OUTILS DE LOCALISATION")
        print("-" * 40)
        print("  1. 📤 Extractor      - Extraire les chaînes")
        print("  2. 📥 Applicator     - Appliquer les localisations")
        print("  3. 🌐 Translation    - Gérer les traductions")
        print("  4. 🔄 Restore        - Restaurer les backups")
        print()
        print("CONFIGURATION")
        print("-" * 40)
        print("  5. ⚙️  Configurer les chemins")
        print("  6. 📋 Afficher la configuration")
        print("  7. 🔍 Détecter dernière extraction")
        print()
        print("  0. 🚪 Quitter")
        print()
    
    def input_plugin_path(self):
        """Configure le chemin du plugin."""
        print("\n📂 Configuration du chemin du plugin")
        print("-" * 60)
        
        current = self.config.get("plugin_path", "")
        if current:
            print(f"Actuel: {current}")
            print()
        
        print("Exemples:")
        print("  D:\\Lightroom\\plugin.lrplugin")
        print("  ./piwigoPublish.lrplugin")
        print()
        
        path = input("Nouveau chemin (ENTRÉE pour garder): ").strip()
        
        if path:
            normalized = os.path.normpath(path)
            if os.path.isdir(normalized):
                self.config.set("plugin_path", normalized)
                print(f"✓ Plugin configuré: {normalized}")
            else:
                print(f"❌ Répertoire introuvable: {normalized}")
        else:
            print("✓ Chemin inchangé")
    
    def input_output_dir(self):
        """Configure le répertoire de sortie."""
        print("\n📂 Configuration du répertoire de sortie")
        print("-" * 60)
        
        current = self.config.get("output_base_dir", "")
        print(f"Actuel: {current or '(à côté des scripts)'}")
        print()
        
        path = input("Nouveau chemin (ENTRÉE pour défaut): ").strip()
        
        if path:
            normalized = os.path.normpath(path)
            os.makedirs(normalized, exist_ok=True)
            self.config.set("output_base_dir", normalized)
            print(f"✓ Sortie configurée: {normalized}")
        else:
            self.config.set("output_base_dir", "")
            print("✓ Utilisera le répertoire par défaut")
    
    def configure_paths(self):
        """Menu de configuration des chemins."""
        self.clear_screen()
        print("\n" + "=" * 60)
        print("  CONFIGURATION DES CHEMINS".center(60))
        print("=" * 60 + "\n")
        
        print("1. Chemin du plugin")
        print("2. Répertoire de sortie")
        print("3. Préfixe LOC")
        print("4. Langue par défaut")
        print("0. Retour")
        print()
        
        choice = input("Votre choix: ").strip()
        
        if choice == '1':
            self.input_plugin_path()
        elif choice == '2':
            self.input_output_dir()
        elif choice == '3':
            current = self.config.get("prefix", "$$$/Piwigo")
            prefix = input(f"Préfixe LOC [{current}]: ").strip()
            if prefix:
                self.config.set("prefix", prefix)
                print(f"✓ Préfixe: {prefix}")
        elif choice == '4':
            current = self.config.get("lang", "en")
            lang = input(f"Langue [{current}]: ").strip().lower()
            if lang and len(lang) == 2:
                self.config.set("lang", lang)
                print(f"✓ Langue: {lang}")
        
        input("\nAppuyez sur ENTRÉE pour continuer...")
    
    def detect_extraction(self):
        """Détecte et configure la dernière extraction."""
        print("\n🔍 Recherche de la dernière extraction...")
        
        latest = self.launcher.find_latest_extraction()
        
        if latest:
            print(f"✓ Trouvé: {latest}")
            confirm = input("Utiliser ce dossier? [O/n]: ").strip().lower()
            if confirm in ['o', 'y', '', 'oui', 'yes']:
                self.config.set("last_extraction_dir", latest)
                print("✓ Configuré comme dernière extraction")
        else:
            print("❌ Aucune extraction trouvée")
        
        input("\nAppuyez sur ENTRÉE pour continuer...")
    
    def run(self):
        """Boucle principale du menu."""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_menu()
            
            choice = input("Votre choix (0-7): ").strip()
            
            if choice == '0':
                print("\n👋 Au revoir!")
                break
            elif choice == '1':
                # Vérifier plugin
                plugin = self.config.get("plugin_path")
                if not plugin or not os.path.isdir(plugin):
                    print("\n⚠️  Plugin non configuré!")
                    self.input_plugin_path()
                else:
                    self.launcher.run_extractor()
                input("\nAppuyez sur ENTRÉE pour continuer...")
            elif choice == '2':
                plugin = self.config.get("plugin_path")
                if not plugin or not os.path.isdir(plugin):
                    print("\n⚠️  Plugin non configuré!")
                    self.input_plugin_path()
                else:
                    self.launcher.run_applicator()
                input("\nAppuyez sur ENTRÉE pour continuer...")
            elif choice == '3':
                self.launcher.run_translation_manager()
                input("\nAppuyez sur ENTRÉE pour continuer...")
            elif choice == '4':
                self.launcher.run_restore_backup()
                input("\nAppuyez sur ENTRÉE pour continuer...")
            elif choice == '5':
                self.configure_paths()
            elif choice == '6':
                self.config.display()
                input("Appuyez sur ENTRÉE pour continuer...")
            elif choice == '7':
                self.detect_extraction()
            else:
                print("❌ Choix invalide")
                input("Appuyez sur ENTRÉE pour continuer...")


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