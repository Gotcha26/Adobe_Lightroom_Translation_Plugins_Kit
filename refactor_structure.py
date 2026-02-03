#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refactor_structure.py - Script de réorganisation automatique du projet

Ce script automatise la réorganisation complète de la structure du projet
LocalisationToolKit selon le plan défini dans .claude/REFACTORING_PLAN.md.

ATTENTION: Ce script modifie la structure des fichiers de manière irréversible.
           Assurez-vous d'avoir un backup git avant de l'exécuter.

Usage:
    python refactor_structure.py --dry-run    # Simulation (recommandé d'abord)
    python refactor_structure.py              # Exécution réelle

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-02-03
Version: 1.0
"""

import os
import sys
import shutil
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime


# =============================================================================
# CONFIGURATION
# =============================================================================

# Racine du projet (où se trouve ce script)
PROJECT_ROOT = Path(__file__).parent.resolve()

# Correspondances des dossiers (ancien -> nouveau)
FOLDER_MAPPINGS = {
    "0_doc": "doc",
    "1_Extractor": "tools/extractor",
    "2_Applicator": "tools/applicator",
    "3_Translator": "tools/translator",
    "9_Tools": "tools/toolbox",
    "common": "core",
    "scripts": "i18n",
}

# Correspondances des fichiers (ancien nom -> nouveau nom)
# Relatif au dossier source
FILE_MAPPINGS = {
    # Extractor
    "1_Extractor/Extractor_main.py": "tools/extractor/main.py",
    "1_Extractor/Extractor_menu.py": "tools/extractor/menu.py",
    "1_Extractor/Extractor_engine.py": "tools/extractor/engine.py",
    "1_Extractor/Extractor_config.py": "tools/extractor/config.py",
    "1_Extractor/Extractor_models.py": "tools/extractor/models.py",
    "1_Extractor/Extractor_output.py": "tools/extractor/output.py",
    "1_Extractor/Extractor_report.py": "tools/extractor/report.py",
    "1_Extractor/Extractor_utils.py": "tools/extractor/utils.py",
    # Applicator
    "2_Applicator/Applicator_main.py": "tools/applicator/main.py",
    "2_Applicator/Applicator_menu.py": "tools/applicator/menu.py",
    # Translator
    "3_Translator/Translator_main.py": "tools/translator/main.py",
    "3_Translator/TM_common.py": "tools/translator/common.py",
    "3_Translator/TM_sync.py": "tools/translator/sync.py",
    "3_Translator/TM_autosync.py": "tools/translator/autosync.py",
    "3_Translator/TM_compare.py": "tools/translator/compare.py",
    "3_Translator/TM_compare_langs.py": "tools/translator/compare_langs.py",
    "3_Translator/TM_extract.py": "tools/translator/extract.py",
    "3_Translator/TM_inject.py": "tools/translator/inject.py",
    "3_Translator/TM_install.py": "tools/translator/install.py",
    "3_Translator/TM_addlang.py": "tools/translator/addlang.py",
    # Toolbox
    "9_Tools/Restore_backup.py": "tools/toolbox/restore_backup.py",
    "9_Tools/Delete_temp_dir.py": "tools/toolbox/delete_temp_dir.py",
    # Core (common)
    "common/__init__.py": "core/__init__.py",
    "common/colors.py": "core/colors.py",
    "common/i18n.py": "core/i18n.py",
    "common/menu_helpers.py": "core/menu_helpers.py",
    "common/output_formatters.py": "core/output_formatters.py",
    "common/paths.py": "core/paths.py",
    # Assets
    "common/Flip-anim.py": "assets/flip_anim.py",
    # i18n scripts
    "scripts/extract_strings.py": "i18n/extract_strings.py",
    "scripts/compile_po.py": "i18n/compile_po.py",
    "scripts/init_language.py": "i18n/init_language.py",
    "scripts/update_po.py": "i18n/update_po.py",
}

# Dossiers de documentation à renommer (__doc -> __doc__)
DOC_FOLDER_RENAMES = {
    "__doc": "__doc__",
}

# Remplacements d'imports dans les fichiers Python
IMPORT_REPLACEMENTS = [
    # common -> core
    (r'from common\.', 'from core.'),
    (r'from common import', 'from core import'),
    (r'import common\.', 'import core.'),
    # Extractor imports (dans tools/extractor/)
    (r'from Extractor_config import', 'from .config import'),
    (r'from Extractor_engine import', 'from .engine import'),
    (r'from Extractor_main import', 'from .main import'),
    (r'from Extractor_menu import', 'from .menu import'),
    (r'from Extractor_models import', 'from .models import'),
    (r'from Extractor_output import', 'from .output import'),
    (r'from Extractor_report import', 'from .report import'),
    (r'from Extractor_utils import', 'from .utils import'),
    (r'import Extractor_', 'from . import '),
    # Applicator imports (dans tools/applicator/)
    (r'from Applicator_main import', 'from .main import'),
    (r'from Applicator_menu import', 'from .menu import'),
    (r'import Applicator_', 'from . import '),
    # Translator imports (dans tools/translator/)
    (r'from TM_common import', 'from .common import'),
    (r'from TM_sync import', 'from .sync import'),
    (r'from TM_autosync import', 'from .autosync import'),
    (r'from TM_compare import', 'from .compare import'),
    (r'from TM_compare_langs import', 'from .compare_langs import'),
    (r'from TM_extract import', 'from .extract import'),
    (r'from TM_inject import', 'from .inject import'),
    (r'from TM_install import', 'from .install import'),
    (r'from TM_addlang import', 'from .addlang import'),
    (r'from Translator_main import', 'from .main import'),
    (r'import TM_', 'from . import '),
]

# Remplacements de chemins dans LocalisationToolKit.py
PATH_REPLACEMENTS = [
    # TOOL_DIRS
    (r'"1_Extractor"', '"tools/extractor"'),
    (r'"2_Applicator"', '"tools/applicator"'),
    (r'"3_Translator"', '"tools/translator"'),
    (r'"9_Tools"', '"tools/toolbox"'),
    # Chemins de scripts
    (r'1_Extractor/Extractor_main\.py', 'tools/extractor/main.py'),
    (r'2_Applicator/Applicator_main\.py', 'tools/applicator/main.py'),
    (r'3_Translator/Translator_main\.py', 'tools/translator/main.py'),
    (r'9_Tools/Restore_backup\.py', 'tools/toolbox/restore_backup.py'),
    (r'9_Tools/Delete_temp_dir\.py', 'tools/toolbox/delete_temp_dir.py'),
    (r'common/Flip-anim\.py', 'assets/flip_anim.py'),
    # Noms d'outils dans les dictionnaires
    (r'"extractor":\s*"1_Extractor"', '"extractor": "tools/extractor"'),
    (r'"applicator":\s*"2_Applicator"', '"applicator": "tools/applicator"'),
    (r'"translator":\s*"3_Translator"', '"translator": "tools/translator"'),
    (r'"tools":\s*"9_Tools"', '"toolbox": "tools/toolbox"'),
]

# Contenu des fichiers __init__.py à créer
INIT_FILES = {
    "tools/__init__.py": '''"""
Tools - Outils de localisation pour plugins Lightroom.

Ce package contient les 4 outils principaux:
- extractor: Extraction des chaînes localisables
- applicator: Application des localisations
- translator: Gestion des traductions
- toolbox: Utilitaires de maintenance
"""
''',
    "tools/extractor/__init__.py": '''"""
Extractor - Extraction des chaînes localisables des plugins Lightroom.

Ce module analyse les fichiers Lua d'un plugin et extrait toutes les
chaînes de texte pouvant être localisées.
"""
from .main import run_extraction
from .menu import show_interactive_menu
''',
    "tools/applicator/__init__.py": '''"""
Applicator - Application des localisations aux plugins Lightroom.

Ce module remplace les chaînes extraites par les appels LOC appropriés.
"""
from .main import process_plugin_directory
from .menu import show_interactive_menu
''',
    "tools/translator/__init__.py": '''"""
Translator - Gestion des traductions pour les plugins Lightroom.

Ce module permet de synchroniser, comparer et gérer les fichiers
de traduction TranslatedStrings_xx.txt.
"""
''',
    "tools/toolbox/__init__.py": '''"""
Toolbox - Utilitaires pour la maintenance des plugins.

Outils de restauration des backups et nettoyage des dossiers temporaires.
"""
''',
    "assets/__init__.py": '''"""
Assets - Ressources visuelles et animations.
"""
''',
    "i18n/__init__.py": '''"""
i18n - Scripts de gestion des traductions du toolkit.

Ces scripts permettent d'extraire, compiler et mettre à jour
les fichiers de traduction .po/.mo du LocalisationToolKit.
"""
''',
}


# =============================================================================
# CLASSES
# =============================================================================

class RefactoringEngine:
    """Moteur de refactoring automatique."""

    def __init__(self, project_root: Path, dry_run: bool = True):
        self.root = project_root
        self.dry_run = dry_run
        self.actions_log: List[str] = []
        self.errors: List[str] = []

    def log(self, message: str, level: str = "INFO"):
        """Enregistre un message dans le log."""
        prefix = {"INFO": "  ", "ACTION": "→ ", "ERROR": "✗ ", "SUCCESS": "✓ "}
        formatted = f"{prefix.get(level, '  ')}{message}"
        self.actions_log.append(formatted)
        print(formatted)

    def log_action(self, action: str):
        """Log une action."""
        if self.dry_run:
            self.log(f"[DRY-RUN] {action}", "ACTION")
        else:
            self.log(action, "ACTION")

    def log_error(self, error: str):
        """Log une erreur."""
        self.errors.append(error)
        self.log(error, "ERROR")

    def log_success(self, message: str):
        """Log un succès."""
        self.log(message, "SUCCESS")

    # -------------------------------------------------------------------------
    # Phase 1: Création des dossiers
    # -------------------------------------------------------------------------
    def create_directories(self):
        """Crée tous les nouveaux dossiers."""
        self.log("\n" + "=" * 60)
        self.log("PHASE 1: Création des dossiers")
        self.log("=" * 60)

        directories = [
            "doc",
            "tools",
            "tools/extractor",
            "tools/extractor/__doc__",
            "tools/extractor/__doc__/en",
            "tools/extractor/__doc__/fr",
            "tools/applicator",
            "tools/applicator/__doc__",
            "tools/applicator/__doc__/en",
            "tools/applicator/__doc__/fr",
            "tools/translator",
            "tools/translator/__doc__",
            "tools/translator/__doc__/en",
            "tools/translator/__doc__/fr",
            "tools/toolbox",
            "tools/toolbox/__doc__",
            "tools/toolbox/__doc__/en",
            "tools/toolbox/__doc__/fr",
            "core",
            "assets",
            "i18n",
        ]

        for dir_path in directories:
            full_path = self.root / dir_path
            if not full_path.exists():
                self.log_action(f"Créer dossier: {dir_path}")
                if not self.dry_run:
                    full_path.mkdir(parents=True, exist_ok=True)
            else:
                self.log(f"Dossier existe déjà: {dir_path}")

    # -------------------------------------------------------------------------
    # Phase 2: Copie des fichiers
    # -------------------------------------------------------------------------
    def copy_files(self):
        """Copie tous les fichiers vers leur nouvelle destination."""
        self.log("\n" + "=" * 60)
        self.log("PHASE 2: Copie des fichiers")
        self.log("=" * 60)

        for old_path, new_path in FILE_MAPPINGS.items():
            src = self.root / old_path
            dst = self.root / new_path

            if src.exists():
                self.log_action(f"Copier: {old_path} → {new_path}")
                if not self.dry_run:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
            else:
                self.log_error(f"Fichier source introuvable: {old_path}")

    # -------------------------------------------------------------------------
    # Phase 3: Copie des dossiers de documentation
    # -------------------------------------------------------------------------
    def copy_documentation(self):
        """Copie les dossiers de documentation."""
        self.log("\n" + "=" * 60)
        self.log("PHASE 3: Copie de la documentation")
        self.log("=" * 60)

        doc_mappings = [
            ("0_doc/.claude", "doc/.claude"),
            ("0_doc/en", "doc/en"),
            ("0_doc/fr", "doc/fr"),
            ("1_Extractor/__doc/en", "tools/extractor/__doc__/en"),
            ("1_Extractor/__doc/fr", "tools/extractor/__doc__/fr"),
            ("2_Applicator/__doc/en", "tools/applicator/__doc__/en"),
            ("2_Applicator/__doc/fr", "tools/applicator/__doc__/fr"),
            ("3_Translator/__doc/en", "tools/translator/__doc__/en"),
            ("3_Translator/__doc/fr", "tools/translator/__doc__/fr"),
            ("9_Tools/__doc", "tools/toolbox/__doc__"),
        ]

        for old_path, new_path in doc_mappings:
            src = self.root / old_path
            dst = self.root / new_path

            if src.exists() and src.is_dir():
                self.log_action(f"Copier dossier: {old_path} → {new_path}")
                if not self.dry_run:
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
            elif src.exists():
                self.log(f"N'est pas un dossier: {old_path}")
            else:
                self.log(f"Dossier source introuvable: {old_path}")

    # -------------------------------------------------------------------------
    # Phase 4: Création des fichiers __init__.py
    # -------------------------------------------------------------------------
    def create_init_files(self):
        """Crée les fichiers __init__.py."""
        self.log("\n" + "=" * 60)
        self.log("PHASE 4: Création des fichiers __init__.py")
        self.log("=" * 60)

        for file_path, content in INIT_FILES.items():
            full_path = self.root / file_path
            self.log_action(f"Créer: {file_path}")
            if not self.dry_run:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    # -------------------------------------------------------------------------
    # Phase 5: Mise à jour des imports dans les fichiers
    # -------------------------------------------------------------------------
    def update_imports(self):
        """Met à jour les imports dans tous les fichiers Python."""
        self.log("\n" + "=" * 60)
        self.log("PHASE 5: Mise à jour des imports")
        self.log("=" * 60)

        # Fichiers à mettre à jour (dans la nouvelle structure)
        files_to_update = [
            "tools/extractor/main.py",
            "tools/extractor/menu.py",
            "tools/extractor/engine.py",
            "tools/extractor/output.py",
            "tools/extractor/report.py",
            "tools/extractor/utils.py",
            "tools/applicator/main.py",
            "tools/applicator/menu.py",
            "tools/translator/main.py",
            "tools/translator/common.py",
            "tools/translator/sync.py",
            "tools/translator/autosync.py",
            "tools/translator/compare.py",
            "tools/translator/compare_langs.py",
            "tools/translator/extract.py",
            "tools/translator/inject.py",
            "tools/translator/install.py",
            "tools/translator/addlang.py",
            "tools/toolbox/restore_backup.py",
            "tools/toolbox/delete_temp_dir.py",
            "core/i18n.py",
            "core/menu_helpers.py",
            "core/output_formatters.py",
            "core/paths.py",
            "i18n/extract_strings.py",
            "i18n/compile_po.py",
            "i18n/init_language.py",
            "i18n/update_po.py",
        ]

        for file_path in files_to_update:
            full_path = self.root / file_path
            if full_path.exists():
                self._update_file_imports(full_path, file_path)
            else:
                self.log(f"Fichier non trouvé (sera créé plus tard): {file_path}")

    def _update_file_imports(self, file_path: Path, rel_path: str):
        """Met à jour les imports dans un fichier."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            changes_made = []

            for pattern, replacement in IMPORT_REPLACEMENTS:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    changes_made.append(f"{pattern} → {replacement}")
                    content = new_content

            if changes_made:
                self.log_action(f"Mise à jour imports: {rel_path}")
                for change in changes_made[:3]:  # Limiter l'affichage
                    self.log(f"    {change}")
                if len(changes_made) > 3:
                    self.log(f"    ... et {len(changes_made) - 3} autres")

                if not self.dry_run:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
            else:
                self.log(f"Pas de changement: {rel_path}")

        except Exception as e:
            self.log_error(f"Erreur lecture {rel_path}: {e}")

    # -------------------------------------------------------------------------
    # Phase 6: Mise à jour de LocalisationToolKit.py
    # -------------------------------------------------------------------------
    def update_main_script(self):
        """Met à jour le fichier principal LocalisationToolKit.py."""
        self.log("\n" + "=" * 60)
        self.log("PHASE 6: Mise à jour de LocalisationToolKit.py")
        self.log("=" * 60)

        main_file = self.root / "LocalisationToolKit.py"
        if not main_file.exists():
            self.log_error("LocalisationToolKit.py introuvable!")
            return

        try:
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            changes_made = []

            # Appliquer les remplacements d'imports
            for pattern, replacement in IMPORT_REPLACEMENTS:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    changes_made.append(f"Import: {pattern}")
                    content = new_content

            # Appliquer les remplacements de chemins
            for pattern, replacement in PATH_REPLACEMENTS:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    changes_made.append(f"Chemin: {pattern}")
                    content = new_content

            if changes_made:
                self.log_action("Mise à jour LocalisationToolKit.py")
                for change in changes_made[:5]:
                    self.log(f"    {change}")
                if len(changes_made) > 5:
                    self.log(f"    ... et {len(changes_made) - 5} autres")

                if not self.dry_run:
                    with open(main_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            else:
                self.log("Pas de changement dans LocalisationToolKit.py")

        except Exception as e:
            self.log_error(f"Erreur mise à jour LocalisationToolKit.py: {e}")

    # -------------------------------------------------------------------------
    # Phase 7: Suppression des anciens dossiers
    # -------------------------------------------------------------------------
    def cleanup_old_folders(self):
        """Supprime les anciens dossiers après migration."""
        self.log("\n" + "=" * 60)
        self.log("PHASE 7: Nettoyage des anciens dossiers")
        self.log("=" * 60)

        old_folders = [
            "0_doc",
            "1_Extractor",
            "2_Applicator",
            "3_Translator",
            "9_Tools",
            "common",
            "scripts",
        ]

        for folder in old_folders:
            folder_path = self.root / folder
            if folder_path.exists():
                self.log_action(f"Supprimer: {folder}/")
                if not self.dry_run:
                    shutil.rmtree(folder_path)
            else:
                self.log(f"Déjà supprimé: {folder}/")

    # -------------------------------------------------------------------------
    # Exécution complète
    # -------------------------------------------------------------------------
    def run(self):
        """Exécute le refactoring complet."""
        print("\n" + "=" * 60)
        print("  REFACTORING AUTOMATIQUE DU PROJET")
        print("  " + ("MODE SIMULATION" if self.dry_run else "MODE RÉEL"))
        print("=" * 60)
        print(f"Racine du projet: {self.root}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if not self.dry_run:
            print("\n⚠️  ATTENTION: Les modifications seront appliquées!")
            response = input("Continuer? [o/N]: ").strip().lower()
            if response not in ['o', 'oui', 'y', 'yes']:
                print("Annulé.")
                return False

        # Exécuter les phases
        self.create_directories()
        self.copy_files()
        self.copy_documentation()
        self.create_init_files()
        self.update_imports()
        self.update_main_script()

        if not self.dry_run:
            self.cleanup_old_folders()
        else:
            self.log("\n[DRY-RUN] Les anciens dossiers seraient supprimés en mode réel")

        # Résumé
        print("\n" + "=" * 60)
        print("  RÉSUMÉ")
        print("=" * 60)
        print(f"Actions effectuées: {len(self.actions_log)}")
        print(f"Erreurs: {len(self.errors)}")

        if self.errors:
            print("\nErreurs rencontrées:")
            for error in self.errors:
                print(f"  - {error}")

        if self.dry_run:
            print("\n💡 Pour appliquer les changements, exécutez:")
            print(f"   python {Path(__file__).name}")
        else:
            print("\n✅ Refactoring terminé!")
            print("\n📋 Prochaines étapes manuelles:")
            print("   1. Vérifier que tout fonctionne: python LocalisationToolKit.py")
            print("   2. Régénérer les traductions: python i18n/extract_strings.py")
            print("   3. Commiter les changements: git add -A && git commit -m '...'")

        return len(self.errors) == 0


# =============================================================================
# POINT D'ENTRÉE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Script de réorganisation automatique du projet LocalisationToolKit"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode simulation: affiche les actions sans les exécuter"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Ne pas demander de confirmation (pour scripts automatisés)"
    )

    args = parser.parse_args()

    # Par défaut, mode dry-run pour sécurité
    dry_run = args.dry_run or not args.no_confirm

    if not args.dry_run and not args.no_confirm:
        print("⚠️  Aucun argument spécifié. Utilisation du mode --dry-run par sécurité.")
        print("    Pour exécuter réellement, utilisez: python refactor_structure.py --no-confirm")
        dry_run = True

    engine = RefactoringEngine(PROJECT_ROOT, dry_run=dry_run)
    success = engine.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
