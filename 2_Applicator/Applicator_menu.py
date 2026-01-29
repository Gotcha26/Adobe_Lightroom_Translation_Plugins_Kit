#!/usr/bin/env python3
"""
Applicator_menu.py

Interface menu interactive pour Applicator.
Permet de configurer tous les paramètres via un menu, compatible Windows/Linux.
Détecte automatiquement les fichiers Extractor générés.
"""

import os
import sys
from datetime import datetime
from typing import Tuple, List, Optional

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import find_latest_tool_output


class ApplicatorMenu:
    """Menu interactif pour configurer l'application des localisations."""
    
    def __init__(self):
        self.plugin_path = ""
        self.extraction_dir = ""  # Dossier contenant les fichiers Extractor
        self.dry_run = False
    
    def clear_screen(self):
        """Efface l'écran (compatible Windows et Linux)."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Affiche l'en-tête du menu."""
        print("\n" + "=" * 80)
        print("  APPLICATOR - Configuration Interactive".center(80))
        print("=" * 80 + "\n")
    
    def print_current_config(self):
        """Affiche la configuration actuelle."""
        print("Configuration actuelle:")
        print(f"  1. Chemin du plugin           : {self.plugin_path if self.plugin_path else '(non défini)'}")
        extraction_display = self.extraction_dir if self.extraction_dir else "(auto-detection __i18n_kit__/Extractor/)"
        print(f"  2. Dossier Extractor          : {extraction_display}")
        print(f"  3. Mode dry-run               : {'Oui (simulation)' if self.dry_run else 'Non (modifications reelles)'}")
        if self.plugin_path:
            print(f"  -> Sortie Applicator          : <plugin>/__i18n_kit__/Applicator/<timestamp>/")
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
        
        # Normaliser le chemin
        normalized_path = os.path.normpath(path)
        
        if not os.path.isdir(normalized_path):
            print(f"❌ Répertoire introuvable: {normalized_path}")
            return False
        
        self.plugin_path = normalized_path
        print(f"✓ Plugin trouvé: {normalized_path}\n")
        return True
    
    def find_latest_extraction(self) -> Optional[str]:
        """Cherche le dossier d'extraction le plus récent dans __i18n_kit__."""
        if not self.plugin_path:
            return None

        # Utiliser la fonction commune pour trouver la dernière extraction
        return find_latest_tool_output(self.plugin_path, "Extractor")
    
    def input_extraction_dir(self) -> bool:
        """Demande le répertoire contenant les fichiers Extractor."""
        print("2  Dossier contenant les fichiers Extractor")
        print("-" * 80)

        # Chercher automatiquement dans __i18n_kit__/Extractor/
        auto_dir = self.find_latest_extraction()

        if auto_dir:
            print(f"Dossier detecte automatiquement:")
            print(f"  {auto_dir}\n")
            print("Options:")
            print("  1. Utiliser ce dossier (recommande)")
            print("  2. Specifier un autre dossier")
            print("  3. Annuler")
            print()

            choice = input("Votre choix (1-3): ").strip()

            if choice == '1' or choice == '':
                self.extraction_dir = auto_dir
                print(f"[OK] Dossier Extractor: {auto_dir}\n")
                return True
            elif choice == '3':
                return False
            elif choice != '2':
                print("[ERREUR] Choix invalide\n")
                return self.input_extraction_dir()
        else:
            print("Aucune extraction detectee dans __i18n_kit__/Extractor/")
            print("Vous devez specifier un chemin manuellement.\n")

        # Entrée manuelle
        print("Exemples:")
        print("  <plugin>/__i18n_kit__/Extractor/20260127_091234")
        print("  C:\\Extractions\\20260127_091234")
        print()

        path = input("Chemin du dossier Extractor: ").strip()

        if not path:
            print("[ERREUR] Chemin obligatoire!")
            return False

        # Normaliser le chemin
        normalized_path = os.path.normpath(path)

        if not os.path.isdir(normalized_path):
            print(f"[ERREUR] Repertoire introuvable: {normalized_path}")
            return False

        # Vérifier que les fichiers Extractor existent
        required_files = ["spacing_metadata.json", "replacements.json"]
        missing = [f for f in required_files if not os.path.exists(os.path.join(normalized_path, f))]

        if missing:
            print(f"[ERREUR] Fichiers manquants: {', '.join(missing)}")
            print("         Assurez-vous que c'est un dossier Extractor valide\n")
            return False

        self.extraction_dir = normalized_path
        print(f"[OK] Dossier Extractor: {normalized_path}\n")
        return True
    
    def input_dry_run(self):
        """Demande si mode dry-run ou modifications réelles."""
        print("3️⃣  Mode de fonctionnement")
        print("-" * 80)
        print("Dry-run (simulation)  : Affiche ce qui sera fait SANS modifier les fichiers")
        print("Modification réelle    : Applique les changements au plugin")
        print()
        
        while True:
            response = input("Mode dry-run? [O/n]: ").strip().lower()
            
            if response in ['o', 'y', '', 'oui', 'yes']:
                self.dry_run = True
                print("✓ Mode simulation (DRY-RUN) - Aucun fichier ne sera modifié\n")
                break
            elif response in ['n', 'non', 'no']:
                self.dry_run = False
                # Confirmation
                confirm = input("⚠️  Êtes-vous sûr de vouloir MODIFIER les fichiers du plugin? [o/N]: ").strip().lower()
                if confirm in ['o', 'oui', 'yes']:
                    print("✓ Mode modification réelle - Les fichiers seront modifiés\n")
                    break
                else:
                    print("Annulé\n")
                    return self.input_dry_run()
            else:
                print("❌ Entrez 'o' (oui) ou 'n' (non)\n")
    
    def run(self) -> bool:
        """Lance le menu interactif."""
        self.clear_screen()
        self.print_header()
        
        print("Configurer les paramètres d'application des localisations.\n")
        
        while True:
            # Boucle sur les éléments obligatoires
            while not self.input_plugin_path():
                pass
            
            while not self.input_extraction_dir():
                pass
            
            self.input_dry_run()
            
            # Afficher le résumé
            self.clear_screen()
            self.print_header()
            print("Résumé de la configuration:\n")
            self.print_current_config()
            
            # Confirmation
            print("Options:")
            print("  1. Démarrer l'application")
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
                    param = input("Paramètre à modifier (1-3) ou 0 pour revenir: ").strip()
                    
                    if param == '0':
                        break
                    elif param == '1':
                        while not self.input_plugin_path():
                            pass
                    elif param == '2':
                        while not self.input_extraction_dir():
                            pass
                    elif param == '3':
                        self.input_dry_run()
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
    
    def to_args(self) -> Tuple[str, str, bool]:
        """Retourne les arguments sous forme de tuple."""
        return (
            self.plugin_path,
            self.extraction_dir,
            self.dry_run
        )


def show_interactive_menu() -> Optional[Tuple[str, str, bool]]:
    """
    Affiche le menu interactif et retourne les paramètres.
    
    Returns:
        Tuple avec (plugin_path, extraction_dir, dry_run)
        ou None si l'utilisateur a annulé
    """
    menu = ApplicatorMenu()
    
    if menu.run():
        return menu.to_args()
    
    return None
