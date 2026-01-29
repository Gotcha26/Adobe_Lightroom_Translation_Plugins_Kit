#!/usr/bin/env python3
"""
Extractor_menu.py

Interface menu interactive pour Extractor.
Permet de configurer tous les paramètres via un menu, compatible Windows/Linux.
"""

import os
import sys
from typing import Tuple, List, Optional


class InteractiveMenu:
    """Menu interactif pour configurer l'extraction."""
    
    def __init__(self):
        self.plugin_path = ""
        self.output_dir = ""
        self.prefix = "$$$/Piwigo"
        self.lang = "en"
        self.exclude_files: List[str] = []
        self.min_length = 3
        self.ignore_log = True
    
    def clear_screen(self):
        """Efface l'écran (compatible Windows et Linux)."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Affiche l'en-tête du menu."""
        print("\n" + "=" * 80)
        print("  EXTRACTOR - Configuration Interactive".center(80))
        print("=" * 80 + "\n")
    
    def print_current_config(self):
        """Affiche la configuration actuelle."""
        print("Configuration actuelle:")
        print(f"  1. Chemin du plugin      : {self.plugin_path if self.plugin_path else '(non défini)'}")
        default_output = "<plugin>/__i18n_kit__/Extractor/<timestamp>/" if self.plugin_path else "(automatique)"
        print(f"  2. Répertoire de sortie  : {self.output_dir if self.output_dir else default_output}")
        print(f"  3. Préfixe LOC           : {self.prefix}")
        print(f"  4. Code langue           : {self.lang}")
        print(f"  5. Fichiers à exclure    : {', '.join(self.exclude_files) if self.exclude_files else '(aucun)'}")
        print(f"  6. Longueur min chaînes  : {self.min_length}")
        print(f"  7. Ignorer logs          : {'✓ Oui' if self.ignore_log else '✗ Non'}")
        print()
    
    def input_plugin_path(self) -> bool:
        """Demande le chemin du plugin."""
        print("1️⃣  Chemin du plugin Lightroom")
        print("-" * 80)
        print("Exemples Windows:")
        print("  C:\\Users\\User\\Documents\\Lightroom\\piwigoPublish.lrplugin")
        print("  .\\piwigoPublish.lrplugin")
        print("\nExemples Linux/Mac:")
        print("  /home/user/piwigoPublish.lrplugin")
        print("  ./piwigoPublish.lrplugin")
        print()
        
        path = input("Chemin du plugin (obligatoire): ").strip()
        
        if not path:
            print("❌ Chemin obligatoire!")
            return False
        
        # Normaliser le chemin pour Windows et Linux
        normalized_path = os.path.normpath(path)
        
        if not os.path.isdir(normalized_path):
            print(f"❌ Répertoire introuvable: {normalized_path}")
            return False
        
        self.plugin_path = normalized_path
        print(f"✓ Plugin trouvé: {normalized_path}\n")
        return True
    
    def input_output_dir(self):
        """Demande le répertoire de sortie (override optionnel)."""
        print("2️⃣  Répertoire de sortie (override)")
        print("-" * 80)
        print("Par DEFAUT: Les fichiers seront créés dans:")
        print("  <plugin>/__i18n_kit__/Extractor/<timestamp>/")
        print("")
        print("Pour OVERRIDE (usage avancé), spécifiez un chemin:")
        print("  C:\\Users\\User\\Desktop\\Extraction")
        print("  /home/user/extraction")
        print("\n(Appuyer sur ENTRÉE pour utiliser le dossier __i18n_kit__ du plugin)\n")

        path = input("Override répertoire de sortie (optionnel): ").strip()

        if path:
            normalized_path = os.path.normpath(path)
            os.makedirs(normalized_path, exist_ok=True)
            self.output_dir = normalized_path
            print(f"✓ Override: {normalized_path}\n")
        else:
            self.output_dir = ""
            print("✓ Utilisera: <plugin>/__i18n_kit__/Extractor/<timestamp>/\n")
    
    def input_prefix(self):
        """Demande le préfixe LOC."""
        print("3️⃣  Préfixe des clés LOC")
        print("-" * 80)
        print("Exemples:")
        print("  $$$/Piwigo (défaut)")
        print("  $$$/MyApp")
        print("  $$$/Plugin/MyPlugin")
        print()
        
        prefix = input(f"Préfixe LOC [{self.prefix}]: ").strip()
        
        if prefix:
            self.prefix = prefix
            print(f"✓ Préfixe: {self.prefix}\n")
        else:
            print(f"✓ Préfixe (défaut): {self.prefix}\n")
    
    def input_lang(self):
        """Demande le code langue."""
        print("4️⃣  Code langue")
        print("-" * 80)
        print("Exemples:")
        print("  en (anglais) - défaut")
        print("  fr (français)")
        print("  de (allemand)")
        print("  es (espagnol)")
        print()
        
        lang = input(f"Code langue [{self.lang}]: ").strip().lower()
        
        if lang and len(lang) == 2:
            self.lang = lang
            print(f"✓ Langue: {self.lang}\n")
        elif lang:
            print("⚠️  Code langue invalide (2 caractères), valeur par défaut utilisée\n")
        else:
            print(f"✓ Langue (défaut): {self.lang}\n")
    
    def input_exclude_files(self):
        """Demande les fichiers à exclure."""
        print("5️⃣  Fichiers à exclure de l'analyse")
        print("-" * 80)
        print("Exemples:")
        print("  JSON.lua")
        print("  test.lua, debug.lua")
        print("  (Appuyer sur ENTRÉE pour ignorer cette option)")
        print()
        
        files = input("Fichiers à exclure (séparés par virgule): ").strip()
        
        if files:
            self.exclude_files = [f.strip() for f in files.split(',')]
            print(f"✓ Fichiers à exclure: {', '.join(self.exclude_files)}\n")
        else:
            self.exclude_files = []
            print("✓ Aucun fichier exclu\n")
    
    def input_min_length(self):
        """Demande la longueur minimale des chaînes."""
        print("6️⃣  Longueur minimale des chaînes")
        print("-" * 80)
        print("Les chaînes plus courtes seront ignorées.")
        print("Valeurs typiques: 2-4")
        print()
        
        while True:
            length = input(f"Longueur minimale [{self.min_length}]: ").strip()
            
            if not length:
                print(f"✓ Longueur minimale (défaut): {self.min_length}\n")
                break
            
            try:
                length_int = int(length)
                if length_int >= 1:
                    self.min_length = length_int
                    print(f"✓ Longueur minimale: {self.min_length}\n")
                    break
                else:
                    print("❌ Doit être >= 1\n")
            except ValueError:
                print("❌ Valeur invalide, entrez un nombre\n")
    
    def input_ignore_log(self):
        """Demande si les logs doivent être ignorées."""
        print("7️⃣  Ignorer les lignes de log")
        print("-" * 80)
        print("Par défaut, les lignes contenant log(), warn(), etc. sont ignorées.")
        print()
        
        while True:
            response = input("Ignorer les logs? [O/n]: ").strip().lower()
            
            if response in ['o', 'y', '', 'oui', 'yes']:
                self.ignore_log = True
                print("✓ Les logs seront ignorés\n")
                break
            elif response in ['n', 'non', 'no']:
                self.ignore_log = False
                print("✓ Les logs NE seront PAS ignorés\n")
                break
            else:
                print("❌ Entrez 'o' (oui) ou 'n' (non)\n")
    
    def run(self) -> bool:
        """Lance le menu interactif."""
        self.clear_screen()
        self.print_header()
        
        print("Configurer les paramètres d'extraction.\n")
        
        while True:
            # Boucle sur les éléments obligatoires
            while not self.input_plugin_path():
                pass
            
            # Options optionnelles
            self.input_output_dir()
            
            self.input_prefix()
            self.input_lang()
            self.input_exclude_files()
            self.input_min_length()
            self.input_ignore_log()
            
            # Afficher le résumé
            self.clear_screen()
            self.print_header()
            print("Résumé de la configuration:\n")
            self.print_current_config()
            
            # Confirmation
            print("Options:")
            print("  1. Démarrer l'extraction")
            print("  2. Modifier les paramètres")
            print("  3. Quitter")
            print()
            
            choice = input("Votre choix (1-3): ").strip()
            
            if choice == '1':
                return True
            elif choice == '2':
                self.clear_screen()
                self.print_header()
                print("Modification de la configuration\n")
                print("Sélectionnez le paramètre à modifier:\n")
                self.print_current_config()
                
                while True:
                    param = input("Paramètre à modifier (1-7) ou 0 pour revenir: ").strip()
                    
                    if param == '0':
                        break
                    elif param == '1':
                        while not self.input_plugin_path():
                            pass
                    elif param == '2':
                        self.input_output_dir()
                    elif param == '3':
                        self.input_prefix()
                    elif param == '4':
                        self.input_lang()
                    elif param == '5':
                        self.input_exclude_files()
                    elif param == '6':
                        self.input_min_length()
                    elif param == '7':
                        self.input_ignore_log()
                    else:
                        print("❌ Choix invalide\n")
                        continue
                    
                    self.clear_screen()
                    self.print_header()
                    print("Modification de la configuration\n")
                    print("Sélectionnez le paramètre à modifier:\n")
                    self.print_current_config()
            elif choice == '3':
                print("\n👋 Au revoir!")
                return False
            else:
                print("❌ Choix invalide (1-3)\n")
    
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


def show_interactive_menu() -> Optional[Tuple[str, str, str, str, List[str], int, bool]]:
    """
    Affiche le menu interactif et retourne les paramètres.
    
    Returns:
        Tuple avec (plugin_path, output_dir, prefix, lang, exclude_files, min_length, ignore_log)
        ou None si l'utilisateur a annulé
    """
    menu = InteractiveMenu()
    
    if menu.run():
        return menu.to_args()
    
    return None
