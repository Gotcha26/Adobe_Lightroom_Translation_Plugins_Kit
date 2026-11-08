#!/usr/bin/env python3
"""
Nom du fichier : paths.py

Dépendances : Aucune

Description :
Gère les chemins et répertoires pour les outils i18n du plugin Lightroom. Fournit des fonctions
pour créer, naviguer et gérer les dossiers horodatés __i18n_tmp__ où sont stockées les sorties
des outils (Extractor, Applicator, Translator, Tools).

Usage CLI :
    Non pourvu

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import re
import shutil
from datetime import datetime
from typing import Optional, List

from .i18n import _


# Nom du dossier racine par défaut pour tous les outils i18n
DEFAULT_I18N_DIR = "__i18n_tmp__"

# Variable globale pour le nom du dossier (configurable)
_i18n_dir = DEFAULT_I18N_DIR

# Format du timestamp : YYYYMMDD_HHMMSS (15 caractères)
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
TIMESTAMP_LENGTH = 15
TIMESTAMP_DIR_RE = re.compile(r'^\d{8}_\d{6}$')

# Libellé affiché à la place du chemin du plugin
PLUGIN_PLACEHOLDER = "<plugin>"

# Mapping des noms d'outils vers leurs dossiers de sortie avec préfixe numérique
# Le préfixe correspond à l'ordre dans le workflow : 1_Extractor → 2_Applicator → 3_Translator
TOOL_FOLDER_NAMES = {
    "Extractor": "1_Extractor",
    "Applicator": "2_Applicator",
    "Translator": "3_Translator",
    "Tools": "9_Tools",
}


def set_i18n_dir(name: str) -> None:
    """
    Définit le nom du dossier temporaire i18n.

    Args:
        name: Nom du dossier (ex: "__i18n_tmp__", "__i18n_kit__")
    """
    global _i18n_dir
    if name and name.strip():
        _i18n_dir = name.strip()


def get_i18n_dir() -> str:
    """
    Retourne le nom du dossier temporaire i18n configuré.

    Returns:
        Nom du dossier (ex: "__i18n_tmp__")
    """
    return _i18n_dir


def get_i18n_kit_path(plugin_path: str) -> str:
    """
    Retourne le chemin du dossier temporaire i18n dans le plugin.

    Args:
        plugin_path: Chemin absolu vers le plugin Lightroom (.lrplugin)

    Returns:
        Chemin complet: <plugin_path>/<i18n_dir>

    Example:
        >>> get_i18n_kit_path("/path/to/plugin.lrplugin")
        '/path/to/plugin.lrplugin/__i18n_tmp__'
    """
    return os.path.join(plugin_path, get_i18n_dir())


def get_tool_output_path(plugin_path: str, tool_name: str, create: bool = True) -> str:
    """
    Retourne le chemin de sortie pour un outil avec timestamp.

    Crée un nouveau dossier horodaté à chaque exécution pour
    conserver l'historique des opérations.

    Le nom du dossier outil inclut automatiquement le préfixe numérique
    défini dans TOOL_FOLDER_NAMES (ex: 1_Extractor, 2_Applicator, 3_Translator).

    Args:
        plugin_path: Chemin vers le plugin Lightroom (.lrplugin)
        tool_name: Nom de l'outil (Extractor, Applicator, Translator, Tools)
        create: Si True, crée le dossier. Si False, retourne juste le chemin.

    Returns:
        Chemin complet: <plugin>/__i18n_tmp__/<prefix_tool_name>/<YYYYMMDD_HHMMSS>/

    Example:
        >>> get_tool_output_path("/path/to/plugin.lrplugin", "Extractor")
        '/path/to/plugin.lrplugin/__i18n_tmp__/1_Extractor/20260129_143022'
    """
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)

    # Mapping TOOL_FOLDER_NAMES, sinon le nom de l'outil tel quel
    prefixed_tool_name = TOOL_FOLDER_NAMES.get(tool_name, tool_name)

    path = os.path.join(
        get_i18n_kit_path(plugin_path),
        prefixed_tool_name,
        timestamp
    )

    if create:
        os.makedirs(path, exist_ok=True)

    return path


def find_session_dirs(i18n_kit: str, tool_name: str) -> List[str]:
    """
    Sessions d'un outil dans un dossier temporaire i18n, de la plus récente à la plus ancienne.

    Point unique de reconnaissance des sessions : le dossier de l'outil doit porter
    exactement le nom créé par `get_tool_output_path` (`2_Applicator`) ou l'ancien
    nom sans préfixe (`Applicator`), et la session un nom `YYYYMMDD_HHMMSS`.
    Un dossier dont le nom contient seulement le nom de l'outil (`my_applicator_notes`)
    n'est jamais pris pour une session.

    Args:
        i18n_kit: Chemin du dossier temporaire (`<plugin>/__i18n_tmp__`)
        tool_name: Nom de l'outil (Extractor, Applicator, Translator, Tools)

    Returns:
        Chemins complets des sessions, liste vide si aucune
    """
    if not os.path.isdir(i18n_kit):
        return []

    # Correspondance exacte : dossier actuel (1_Extractor) puis ancien format (Extractor)
    folder_names = [TOOL_FOLDER_NAMES.get(tool_name, tool_name), tool_name]
    outputs = []
    for folder_name in dict.fromkeys(folder_names):
        tool_dir = os.path.join(i18n_kit, folder_name)
        if not os.path.isdir(tool_dir):
            continue
        # Uniquement les sous-dossiers au format YYYYMMDD_HHMMSS
        outputs.extend(
            os.path.join(tool_dir, d) for d in os.listdir(tool_dir)
            if TIMESTAMP_DIR_RE.match(d) and os.path.isdir(os.path.join(tool_dir, d))
        )

    # Tri décroissant sur l'horodatage (le plus récent en premier), tous dossiers confondus.
    # Le format YYYYMMDD_HHMMSS permet un tri lexicographique correct
    outputs.sort(key=os.path.basename, reverse=True)
    return outputs


def find_all_tool_outputs(plugin_path: str, tool_name: str) -> List[str]:
    """
    Trouve tous les dossiers horodatés pour un outil, triés du plus récent au plus ancien.

    Recherche parmi les dossiers horodatés (format YYYYMMDD_HHMMSS)
    et retourne tous les dossiers trouvés, triés par date décroissante.

    Supporte les dossiers avec et sans préfixe numérique
    (ex: "Extractor" ou "1_Extractor").

    Args:
        plugin_path: Chemin vers le plugin Lightroom
        tool_name: Nom de l'outil (Extractor, Applicator, etc.)

    Returns:
        Liste des chemins complets des dossiers trouvés, triés du plus récent au plus ancien.
        Liste vide si aucun dossier trouvé.

    Example:
        >>> find_all_tool_outputs("/path/to/plugin.lrplugin", "Extractor")
        ['/path/.../1_Extractor/20260129_143022', '/path/.../1_Extractor/20260129_120000']
    """
    return find_session_dirs(get_i18n_kit_path(plugin_path), tool_name)


def find_latest_tool_output(plugin_path: str, tool_name: str) -> Optional[str]:
    """
    Trouve le dossier le plus récent pour un outil.

    Recherche parmi les dossiers horodatés (format YYYYMMDD_HHMMSS)
    et retourne le plus récent par tri lexicographique.

    Supporte les dossiers avec et sans préfixe numérique
    (ex: "Extractor" ou "1_Extractor").

    Args:
        plugin_path: Chemin vers le plugin Lightroom
        tool_name: Nom de l'outil (Extractor, Applicator, etc.)

    Returns:
        Chemin complet du dernier dossier, ou None si aucun trouvé

    Example:
        >>> find_latest_tool_output("/path/to/plugin.lrplugin", "Extractor")
        '/path/to/plugin.lrplugin/__i18n_kit__/1_Extractor/20260129_143022'
    """
    all_outputs = find_all_tool_outputs(plugin_path, tool_name)
    return all_outputs[0] if all_outputs else None


def find_update_dir_in(directory: str, filename: str) -> Optional[str]:
    """Renvoie `directory` ou `directory/compare` s'il contient `filename`, sinon None."""
    for candidate in (directory, os.path.join(directory, "compare")):
        if os.path.isfile(os.path.join(candidate, filename)):
            return candidate
    return None


def find_latest_update_dir(plugin_path: str, filename: str) -> Optional[str]:
    """
    Trouve le dossier Translator le plus récent contenant le fichier UPDATE.

    Parcourt les sorties Translator du plus récent au plus ancien et renvoie le
    premier dossier contenant `filename`, directement ou dans un sous-dossier
    `compare/` (cas d'AUTOSYNC). Les sorties sans UPDATE (COMPARE-LANGS,
    ADD LANGUAGE) sont ignorées.

    Args:
        plugin_path: Chemin vers le plugin Lightroom
        filename: Nom du fichier UPDATE recherché (ex: "UPDATE_en.json")

    Returns:
        Le dossier qui contient réellement le fichier, ou None si aucun
    """
    for output in find_all_tool_outputs(plugin_path, "Translator"):
        found = find_update_dir_in(output, filename)
        if found:
            return found
    return None


def get_translator_backup_dir(plugin_path: str) -> Optional[str]:
    """
    Dossier de sauvegarde d'une opération Translator : `<sortie Translator>/backups`.

    Renvoie None si `plugin_path` est vide (le `.bak` ira alors dans le repli
    `<temp_dir>/backups` du dossier du fichier cible, voir `fallback_backup_dir`).
    Le dossier n'est créé qu'au moment de la copie.
    """
    if not plugin_path:
        return None
    return os.path.join(get_tool_output_path(plugin_path, "Translator", create=False), "backups")


def fallback_backup_dir(target_dir: str) -> str:
    """
    Dossier de sauvegarde de repli, quand ni session ni chemin de plugin ne sont connus.

    `target_dir` est le dossier du fichier à sauvegarder. Le repli est
    `<target_dir>/<temp_dir>/backups` : toujours sous le dossier temporaire configuré,
    jamais un `backups/` ni un `.bak` posé directement dans `target_dir` (qui est la
    racine du plugin pour un `TranslatedStrings_xx.txt`, cf. #28).
    """
    return os.path.join(target_dir, get_i18n_dir(), "backups")


def local_backup_path(file_path: str) -> str:
    """Chemin de sauvegarde de repli : `<temp_dir>/backups/<nom>.bak` (voir `fallback_backup_dir`)."""
    return os.path.join(fallback_backup_dir(os.path.dirname(file_path)), os.path.basename(file_path) + '.bak')


def count_bak_files(directory: str) -> int:
    """Nombre de fichiers `.bak` sous `directory` (récursif), 0 s'il n'existe pas."""
    return sum(
        1 for _root, _dirs, files in os.walk(directory)
        for name in files if name.endswith('.bak')
    )


class BackupReport:
    """
    Sauvegardes réellement écrites par une opération (INJECT, SYNC, Applicator…).

    Passé en paramètre `backups=` aux fonctions qui sauvegardent : seuls les `.bak`
    effectivement créés y sont enregistrés (un `.bak` déjà présent, conservé par
    `backup_once`, n'est pas compté). `directory` est le dossier de sauvegarde réellement utilisé.
    """

    def __init__(self) -> None:
        self.directory: Optional[str] = None
        self.files: List[str] = []

    def record(self, backup_path: str, directory: str) -> None:
        if self.directory is None:
            self.directory = directory
        if backup_path not in self.files:
            self.files.append(backup_path)


def backup_to_fallback(file_path: str, backups: Optional[BackupReport] = None) -> str:
    """Copie `file_path` vers son `.bak` de repli (voir `fallback_backup_dir`) et l'enregistre dans `backups`."""
    backup_path = local_backup_path(file_path)
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(file_path, backup_path)
    if backups is not None:
        backups.record(backup_path, os.path.dirname(backup_path))
    return backup_path


def format_backup_message(backups: BackupReport, plugin_path: str = "") -> str:
    """Message de sauvegarde précis : fichiers réellement sauvegardés et dossier, relatif au plugin."""
    if not backups.files:
        return _("Aucune nouvelle sauvegarde .bak (déjà sauvegardés ou fichiers absents)")
    return _("Sauvegardes .bak : {count} fichier(s) dans {folder}").format(
        count=len(backups.files),
        folder=display_relative(backups.directory, plugin_path),
    )


def is_valid_plugin_path(path: str) -> bool:
    """
    Vérifie si le chemin est un plugin Lightroom valide.

    Args:
        path: Chemin à vérifier

    Returns:
        True si le chemin se termine par .lrplugin et existe, False sinon
    """
    if not path:
        return False
    normalized = os.path.normpath(path)
    return os.path.isdir(normalized) and normalized.lower().endswith('.lrplugin')


def validate_plugin_path(path: str) -> tuple:
    """
    Valide un chemin de plugin et retourne des informations détaillées.

    Args:
        path: Chemin à valider

    Returns:
        Tuple (is_valid, normalized_path, warning_message)
        - is_valid: True si le chemin est utilisable (répertoire existant).
          Peut rester True quand le dossier n'a pas l'extension .lrplugin,
          auquel cas warning_message est non-None ("soft validation").
          Les appelants vérifient is_valid pour décider d'avorter,
          puis affichent warning_message s'il est présent.
        - normalized_path: Chemin normalisé (None si is_valid=False et path vide,
          sinon le chemin tel que retourné par os.path.normpath).
        - warning_message: Message à afficher (erreur ou avertissement) ou None.
    """
    if not path:
        return False, None, _("Chemin vide")

    normalized = os.path.normpath(path)

    if not os.path.isdir(normalized):
        return False, normalized, _("Répertoire introuvable: {normalized}").format(normalized=normalized)

    if not normalized.lower().endswith('.lrplugin'):
        return True, normalized, _("Ce dossier ne se termine pas par .lrplugin")

    return True, normalized, None


def normalize_path(path: str) -> str:
    """
    Normalise un chemin pour compatibilité Windows/Linux.

    - Convertit en chemin absolu
    - Normalise les séparateurs (/ ou \\ selon l'OS)
    - Résout les .. et .

    Args:
        path: Chemin à normaliser (relatif ou absolu)

    Returns:
        Chemin absolu normalisé selon l'OS

    Example:
        >>> normalize_path("./plugin.lrplugin")
        '/current/dir/plugin.lrplugin'  # sur Linux
        'C:\\current\\dir\\plugin.lrplugin'  # sur Windows
    """
    return os.path.normpath(os.path.abspath(path))


def backup_path_for(file_path: str, plugin_path: str, backup_dir: str) -> str:
    """
    Calcule le chemin du backup d'un fichier en conservant son arborescence relative au plugin.

    Exemple : <plugin>/ui/Dialog.lua -> <backup_dir>/ui/Dialog.lua.bak
    Si le fichier est hors du plugin, seul son nom de base est conservé.
    Ne crée aucun dossier : l'appelant doit faire os.makedirs(os.path.dirname(...)).
    """
    rel_path = os.path.relpath(file_path, plugin_path)
    if rel_path == os.pardir or rel_path.startswith(os.pardir + os.sep) or os.path.isabs(rel_path):
        rel_path = os.path.basename(file_path)
    return os.path.join(backup_dir, rel_path + '.bak')


def backup_once(file_path: str, plugin_path: str, backup_dir: str,
                backups: Optional[BackupReport] = None) -> str:
    """
    Sauvegarde `file_path` dans `backup_dir`, sauf si un backup existe déjà.

    Dans une même session (même `backup_dir`), le premier écrivain gagne : le
    `.bak` conserve l'état d'origine du fichier, même si plusieurs étapes
    (Applicator, INJECT, SYNC…) le modifient successivement.

    Args:
        backups: Si fourni, y enregistre le backup uniquement quand il vient d'être créé

    Returns:
        Chemin du backup (existant ou nouvellement créé)
    """
    backup_path = backup_path_for(file_path, plugin_path, backup_dir)
    if not os.path.exists(backup_path):
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(file_path, backup_path)
        if backups is not None:
            backups.record(backup_path, backup_dir)
    return backup_path


def display_relative(path: str, plugin_path: str) -> str:
    """
    Chemin à afficher : `<plugin>/sous/dossier` si `path` est dans le plugin.

    La comparaison porte sur des composants de chemin entiers (un dossier voisin
    `plugin.lrplugin-old` n'est pas confondu avec `plugin.lrplugin`) et ignore la
    casse là où le système de fichiers l'ignore (Windows, via os.path.normcase).

    Args:
        path: Chemin à afficher
        plugin_path: Chemin du plugin (vide = pas de raccourci)

    Returns:
        `<plugin>/…` avec des séparateurs `/`, ou `path` inchangé s'il est hors du plugin
    """
    if not path or not plugin_path:
        return path

    full = os.path.normpath(os.path.abspath(path))
    plugin = os.path.normpath(os.path.abspath(plugin_path))
    full_key = os.path.normcase(full)
    plugin_key = os.path.normcase(plugin)

    if full_key == plugin_key:
        return PLUGIN_PLACEHOLDER
    if not full_key.startswith(plugin_key.rstrip(os.sep) + os.sep):
        return path

    try:
        relative = os.path.relpath(full, plugin)
    except ValueError:
        # Lecteurs différents sous Windows : impossible en pratique après le test ci-dessus
        return path
    return "{placeholder}/{relative}".format(placeholder=PLUGIN_PLACEHOLDER, relative=relative.replace(os.sep, "/"))


def find_git_root(path: str) -> Optional[str]:
    """
    Remonte depuis `path` jusqu'au premier dossier contenant `.git`.

    `.git` peut être un dossier (dépôt classique) ou un fichier (worktree, sous-module).

    Args:
        path: Dossier de départ (ex: chemin du plugin)

    Returns:
        Racine du dépôt git, ou None si aucun parent n'en contient
    """
    if not path:
        return None
    current = os.path.normpath(os.path.abspath(path))
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent
