#!/usr/bin/env python3
"""
common/output_formatters.py

Formatage unifié pour tous les outils (Extractor, Applicator, etc.).
Assure un affichage cohérent et aligné des informations.

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-02-01
Version : 1.0
"""

import os
from typing import Dict, List, Optional, Tuple
from core.colors import Colors
from core.i18n import _

# Instance couleurs
c = Colors()


class OutputFormatter:
    """Formatte les outputs de manière uniforme et alignée."""

    def __init__(self):
        """Initialise le formatteur."""
        self.max_key_length = 0

    def print_section_header(self, title: str, width: int = 80) -> None:
        """Affiche un header de section avec style cohérent."""
        print()
        print(c.HEADER + "=" * width + c.RESET)
        print(c.title(title))
        print(c.HEADER + "=" * width + c.RESET)

    def print_section_divider(self, width: int = 80) -> None:
        """Affiche un diviseur de section."""
        print(c.HEADER + "=" * width + c.RESET)

    def aligned_output(self, items: List[Tuple[str, str]], width: int = 80) -> None:
        """
        Affiche des items alignés avec ':' correctement positionnés.

        Args:
            items: Liste de tuples (clé, valeur)
            width: Largeur totale disponible (défaut 80)

        Example:
            items = [
                ("Plugin", "path/to/plugin"),
                ("Sortie", "path/to/output"),
            ]
            formatter.aligned_output(items)
        """
        if not items:
            return

        # Calculer la largeur max des clés
        max_key_len = max(len(key) for key, _ in items)

        # Afficher chaque item aligné
        for key, value in items:
            print(f"  {c.KEY}{key:<{max_key_len}}{c.RESET} : {c.VALUE}{value}{c.RESET}")

    def print_summary_stats(self, stats: Dict[str, int], title: Optional[str] = None) -> None:
        """
        Affiche les statistiques du résumé avec alignement.

        Args:
            stats: Dictionnaire {nom: valeur}
            title: Titre optionnel de la section
        """
        if title:
            print(c.title(title))
            print()

        if not stats:
            return

        # Calculer la largeur max des clés
        max_key_len = max(len(key) for key in stats.keys())

        # Afficher les stats principales
        for key, value in stats.items():
            print(f"  {c.KEY}{key:<{max_key_len}}{c.RESET} : {c.VALUE}{value}{c.RESET}")

    def print_summary_details(self, details: Dict[str, int], title: Optional[str] = None) -> None:
        """
        Affiche les détails supplémentaires avec alignement.

        Args:
            details: Dictionnaire {nom: valeur}
            title: Titre optionnel de la section
        """
        if title:
            print()
            print(c.title(title))
            print()

        if not details:
            return

        # Calculer la largeur max des clés
        max_key_len = max(len(key) for key in details.keys())

        # Afficher les détails
        for key, value in details.items():
            print(f"  {c.KEY}{key:<{max_key_len}}{c.RESET} : {c.VALUE}{value}{c.RESET}")

    def print_files_generated(self, files: List[Tuple[str, str, str]], output_dir: str) -> None:
        """
        Affiche les fichiers générés de manière structurée.

        Args:
            files: Liste de tuples (name, relative_path, description)
            output_dir: Répertoire de sortie (pour affichage du contexte)

        Example:
            files = [
                ("TranslatedStrings_en.txt", "272 clés", "Fichier de chaînes"),
                ("spacing_metadata.json", "82 entrées", "Métadonnées"),
            ]
            formatter.print_files_generated(files, "/path/to/output")
        """
        self.print_section_header(_("FICHIERS GÉNÉRÉS"))

        # Afficher le dossier de sortie
        print(f"\n  [" + _("Sortie") + f"] {c.VALUE}{output_dir}{c.RESET}\n")

        # Afficher la liste des fichiers
        if files:
            for name, count, description in files:
                print(f"    [{c.OK}OK{c.RESET}] {c.KEY}{name:<30}{c.RESET} {c.DIM}({count}){c.RESET}")
                if description:
                    print(f"        {c.DIM}{description}{c.RESET}")

        print()
        self.print_section_divider()
        print()

    def print_extraction_summary(self, plugin_path: str, output_dir: str,
                                prefix: str, lang: str,
                                main_stats: Dict[str, int],
                                detail_stats: Dict[str, int],
                                existing_loc_count: int) -> None:
        """
        Affiche le résumé d'extraction complet et formaté.

        Args:
            plugin_path: Chemin du plugin
            output_dir: Dossier de sortie (chemin complet)
            prefix: Préfixe LOC
            lang: Langue extraite
            main_stats: Stats principales {nom: valeur}
            detail_stats: Stats détaillées {nom: valeur}
            existing_loc_count: Nombre de clés LOC existantes
        """
        self.print_section_header(_("RÉSUMÉ DE L'EXTRACTION"))

        # Afficher les paramètres de base (une seule fois)
        base_info = [
            (_("Plugin"), self._extract_plugin_name(plugin_path)),
            (_("Dossier"), self._extract_relative_path(output_dir, plugin_path)),
            (_("Préfixe LOC"), prefix),
            (_("Langue"), lang),
        ]
        self.aligned_output(base_info)

        # Statistiques principales
        print()
        main_stats[_("Clés LOC existantes")] = existing_loc_count
        self.print_summary_stats(main_stats)

        # Détails supplémentaires
        if detail_stats:
            self.print_summary_details(detail_stats, _("Détails"))

        print()
        self.print_section_divider()
        print()

    @staticmethod
    def _extract_plugin_name(plugin_path: str) -> str:
        """Extrait le nom du plugin du chemin."""
        return os.path.basename(plugin_path)

    @staticmethod
    def _extract_relative_path(full_path: str, plugin_path: str) -> str:
        """
        Extrait le chemin relatif du dossier de sortie par rapport au plugin.

        Example:
            full_path: /path/to/plugin.lrplugin/__i18n_tmp__/1_Extractor/20260201_154842
            plugin_path: /path/to/plugin.lrplugin
            returns: __i18n_tmp__/1_Extractor/20260201_154842
        """
        if plugin_path in full_path:
            # Obtenir le chemin relatif après le plugin
            relative = full_path.replace(plugin_path, "").lstrip(os.sep)
            return relative
        return full_path


# Instance globale pour import facile
formatter = OutputFormatter()
