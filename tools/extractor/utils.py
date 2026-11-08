#!/usr/bin/env python3
"""
Nom du fichier : utils.py

Dépendances : .config

Description :
Fonctions utilitaires pour l'extraction des chaînes localisables.
Traitement du texte, extraction d'espaces/suffixes, détection des chaînes techniques, génération des clés LOC.

Usage CLI :
    Non pourvu

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import re
import os
import sys
from typing import Tuple, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .config import (
    COMMON_SUFFIXES, STOP_WORDS,
    TECHNICAL_CONTEXT_PATTERNS, LUA_STRING_LITERAL_PATTERN, BLOCK_COMMENT_OPEN_PATTERN, LOG_LINE_REGEX,
    PluginRules
)

# Échappements simples d'un littéral Lua (forme source -> caractère)
_LUA_SIMPLE_ESCAPES = {
    '\\': '\\', '"': '"', "'": "'",
    'n': '\n', 'r': '\r', 't': '\t',
    'a': '\a', 'b': '\b', 'f': '\f', 'v': '\v',
    '\n': '\n',  # \ suivi d'un vrai saut de ligne
}
# Caractères à ré-échapper dans un littéral Lua entre guillemets doubles
_LUA_ESCAPE_OUT = {
    '\\': '\\\\', '"': '\\"',
    '\n': '\\n', '\r': '\\r', '\t': '\\t',
    '\a': '\\a', '\b': '\\b', '\f': '\\f', '\v': '\\v',
}
# Morceaux d'un littéral : séquence \ddd, autre \c, texte brut, ou \ final isolé.
# \xXX et \u{...} n'existent pas en Lua 5.1 (celui de Lightroom) : ils tombent
# dans « autre \c » et sont conservés tels quels.
_LUA_ESCAPE_TOKEN = re.compile(r'\\(?:(\d{1,3})|(.))|([^\\]+)|\\', re.DOTALL)

# Marque le `\` d'une séquence conservée telle quelle par unescape_lua_string
# (non décodable sans ambiguïté). Surrogate isolé : n'apparaît jamais dans un
# texte lu depuis un fichier ni dans une séquence décodée, donc aucune confusion
# avec une barre oblique réelle. escape_lua_string le rend en `\` simple.
# Un texte qui le contient n'est pas représentable dans un fichier UTF-8 :
# l'Extractor ignore la chaîne (voir has_undecoded_escape).
VERBATIM_BACKSLASH = '\udc5c'


def _verbatim(sequence: str) -> str:
    """Séquence source conservée : chaque `\\` devient VERBATIM_BACKSLASH."""
    return sequence.replace('\\', VERBATIM_BACKSLASH)


def unescape_lua_string(text: str) -> str:
    """
    Dés-échappe le contenu d'un littéral Lua (forme source -> texte réel).

    Lightroom exécute Lua 5.1 : seuls les échappements de Lua 5.1 sont décodés.

    - Échappements simples (\\\\, \\", \\', \\n, \\r, \\t, \\a, \\b, \\f, \\v,
      \\ + saut de ligne) : décodés.
    - \\ddd (<= 255) : octets. Une suite contiguë de ces séquences est décodée
      en UTF-8 (« \\195\\169 » -> « é ») ; si la suite n'est pas de l'UTF-8
      valide, elle est conservée telle quelle.
    - \\xXX, \\u{X...}, \\z, \\ddd > 255 et tout autre échappement : conservés
      tels quels. \\xXX, \\u{...} et \\z n'existent qu'à partir de Lua 5.2/5.3 :
      en Lua 5.1, « \\x41 » s'affiche « x41 » ; les décoder changerait le texte
      que Lightroom affiche.

    Une séquence conservée garde son texte source, son `\\` remplacé par
    VERBATIM_BACKSLASH : escape_lua_string la restitue à l'identique, sans
    la confondre avec une barre oblique réelle. L'aller-retour
    escape_lua_string(unescape_lua_string(s)) donne donc toujours un
    littéral de même valeur Lua.
    """
    if '\\' not in text:
        return text

    out: List[str] = []
    run_bytes = bytearray()   # Octets \ddd contigus en attente
    run_source: List[str] = []

    def _flush_run():
        if not run_bytes:
            return
        try:
            out.append(run_bytes.decode('utf-8'))
        except UnicodeDecodeError:
            out.append(_verbatim(''.join(run_source)))
        run_bytes.clear()
        run_source.clear()

    for match in _LUA_ESCAPE_TOKEN.finditer(text):
        decimal, other, plain = match.groups()
        source = match.group(0)

        if decimal is not None and int(decimal) <= 255:
            run_bytes.append(int(decimal))
            run_source.append(source)
            continue

        _flush_run()
        if plain is not None:
            out.append(plain)
        elif other is not None and other in _LUA_SIMPLE_ESCAPES:
            out.append(_LUA_SIMPLE_ESCAPES[other])
        else:
            # \xXX, \u{...}, \z, \ddd > 255, échappement inconnu, \ final isolé
            out.append(_verbatim(source))

    _flush_run()
    return ''.join(out)


def has_undecoded_escape(text: str) -> bool:
    """Vrai si le texte réel contient une séquence Lua conservée telle quelle."""
    return VERBATIM_BACKSLASH in text


def _escape_char(ch: str) -> str:
    if ch == VERBATIM_BACKSLASH:
        return '\\'
    escaped = _LUA_ESCAPE_OUT.get(ch)
    if escaped is not None:
        return escaped
    if ord(ch) < 0x20 or ch == '\x7f':
        # Toujours 3 chiffres : un chiffre qui suit ne prolonge pas la séquence
        return '\\%03d' % ord(ch)
    return ch


def escape_lua_string(text: str) -> str:
    """
    Échappe un texte pour l'insérer entre guillemets doubles Lua
    (inverse de unescape_lua_string).

    `"` et `\\` réels sont échappés, les caractères de contrôle sans
    échappement simple deviennent \\ddd, et une séquence conservée par
    unescape_lua_string (VERBATIM_BACKSLASH) ressort telle qu'elle était.
    """
    return ''.join(_escape_char(ch) for ch in text)


# Littéraux Lua d'une ligne : "…", '…' (échappements tolérés) et chaînes longues
# [[…]] / [=*[…]=*] fermées sur la même ligne (hors --[[, qui ouvre un commentaire)
_ANY_LUA_LITERAL_PATTERN = re.compile(
    r'"(?:[^"\\]|\\.)*"'
    r"|'(?:[^'\\]|\\.)*'"
    r'|(?<!-)\[(=*)\[.*?\]\1\]'
)


def find_literal_positions(line: str, original_text: str) -> List[int]:
    """
    Positions des littéraux entiers "…" de la ligne dont le contenu source
    (forme échappée) vaut original_text.

    La recherche est ancrée sur les bornes des littéraux énumérés : elle ne
    trouve jamais `"X"` à l'intérieur d'un autre littéral (ex. la fin de
    `"Open \\"X\\""`), ni entre la fin d'un littéral et le début du suivant.

    Returns:
        Positions (guillemet ouvrant) par ordre croissant
    """
    quoted = f'"{original_text}"'
    return [match.start() for match in _ANY_LUA_LITERAL_PATTERN.finditer(line)
            if match.group(0) == quoted]


# Après « log: » : nom de méthode éventuel, puis l'argument
_LOG_METHOD_TAIL = re.compile(r'\s*(?:\w+\s*)?')


def log_call_spans(line: str) -> List[Tuple[int, int]]:
    """
    Zones (début, fin) des arguments d'appels de log d'une ligne.

    Un appel de log est repéré par LOG_LINE_REGEX (la même notion que
    l'option « ignorer les logs » de l'Extractor), cherché hors des
    littéraux : « log( » à l'intérieur d'une chaîne n'en est pas un.
    La zone va de la parenthèse ouvrante à la parenthèse fermante
    correspondante (fin de ligne si l'appel continue sur la ligne suivante).
    Pour un appel sans parenthèses (sucre Lua), c'est le littéral argument
    (`log:trace "msg"`) ou la table argument, de `{` à l'accolade fermante
    correspondante (`log:info{ ... }`). Un littéral qui commence dans une zone
    est un argument de log.

    Returns:
        Liste de (début, fin) en positions de la ligne
    """
    masked = _mask_string_literals(line)
    spans = []
    for match in LOG_LINE_REGEX.finditer(masked):
        if masked[match.end() - 1] == '(':
            open_pos = match.end() - 1
        else:
            # « log: » : sauter le nom de méthode jusqu'à l'argument
            open_pos = _LOG_METHOD_TAIL.match(line, match.end()).end()
            if not line.startswith(('(', '{'), open_pos):
                literal = _ANY_LUA_LITERAL_PATTERN.match(line, open_pos)
                if literal:
                    spans.append(literal.span())
                continue

        opening = masked[open_pos]
        closing = ')' if opening == '(' else '}'
        depth = 0
        close_pos = len(line.rstrip('\r\n'))
        for index in range(open_pos, len(masked)):
            if masked[index] == opening:
                depth += 1
            elif masked[index] == closing:
                depth -= 1
                if depth == 0:
                    close_pos = index + 1
                    break
        spans.append((open_pos, close_pos))
    return spans


def blank_spans(line: str, spans: List[Tuple[int, int]]) -> str:
    """Remplace les zones par des espaces : même longueur, colonnes inchangées."""
    for start, end in spans:
        line = line[:start] + ' ' * (end - start) + line[end:]
    return line


def pick_literal_position(line: str, original_text: str, used: set,
                          preferred: int | None = None) -> int | None:
    """
    Choisit le littéral entier "original_text" à remplacer dans la ligne.

    Parmi les littéraux non encore utilisés (`used`), prend celui qui commence
    à `preferred` (colonne relevée par l'Extractor) s'il existe, sinon le
    premier. La position choisie est ajoutée à `used`.

    Returns:
        Position du guillemet ouvrant, ou None si aucun littéral ne convient
    """
    positions = [pos for pos in find_literal_positions(line, original_text) if pos not in used]
    if not positions:
        return None
    position = preferred if preferred in positions else positions[0]
    used.add(position)
    return position


def _mask_string_literals(text: str) -> str:
    """Remplace chaque littéral Lua de la ligne par des espaces (même longueur)."""
    return _ANY_LUA_LITERAL_PATTERN.sub(lambda m: ' ' * len(m.group(0)), text)


def block_comment_close_end(line: str, open_level: str, start: int = 0) -> int | None:
    """
    Offset de fin d'un commentaire bloc de niveau open_level dans la ligne.

    Returns:
        Position qui suit le délimiteur fermant `]=*]` (à partir de start),
        ou None si le commentaire ne se ferme pas sur cette ligne
    """
    closing = ']' + open_level + ']'
    idx = line.find(closing, start)
    return None if idx == -1 else idx + len(closing)


def block_comment_state(line: str, open_level: str | None) -> str | None:
    """
    Calcule l'état « commentaire bloc » Lua à la fin d'une ligne.

    Un commentaire bloc s'ouvre par --[[ ou --[=*[ et se ferme par ]] ou ]=*]
    de même niveau (même nombre de '='). Un `--` hors chaîne qui n'est pas
    suivi de [=*[ est un commentaire de ligne : il clôt l'analyse de la ligne.

    Args:
        line: La ligne de code Lua
        open_level: Niveau ('=' * n) du commentaire bloc ouvert au début de la
                    ligne, ou None si la ligne commence hors commentaire

    Returns:
        Le niveau du commentaire bloc encore ouvert en fin de ligne, ou None
    """
    pos = 0
    while True:
        if open_level is not None:
            close_end = block_comment_close_end(line, open_level, pos)
            if close_end is None:
                return open_level
            pos = close_end
            open_level = None

        rest = _mask_string_literals(line[pos:])
        dash = rest.find('--')
        if dash == -1:
            return None
        opening = BLOCK_COMMENT_OPEN_PATTERN.match(rest, dash)
        if not opening:
            return None  # Commentaire de ligne : le reste est ignoré
        open_level = opening.group(1)
        pos += opening.end()


def comment_spans(line: str, open_level: str | None) -> List[Tuple[int, int]]:
    """
    Zones (début, fin) des commentaires Lua d'une ligne, hors chaînes.

    - Fin d'un commentaire bloc ouvert au début de la ligne : de 0 au
      délimiteur fermant `]=*]` de même niveau inclus.
    - Commentaire bloc `--[=*[ … ]=*]` ouvert et fermé sur la ligne : zone
      du `--` au délimiteur fermant ; le code qui suit reste du code.
    - Commentaire bloc qui reste ouvert, ou commentaire de ligne `--` : zone
      jusqu'à la fin de la ligne (saut de ligne exclu).

    Effacer ces zones par des espaces (blank_spans) donne le code seul,
    aux mêmes colonnes que la ligne source.

    Args:
        line: La ligne de code Lua
        open_level: Niveau du commentaire bloc ouvert au début de la ligne
                    (voir block_comment_state), ou None

    Returns:
        Liste de (début, fin) en positions de la ligne, par ordre croissant
    """
    end_of_line = len(line.rstrip('\r\n'))
    spans = []
    pos = 0
    start = 0  # Début du commentaire bloc en cours
    while True:
        if open_level is not None:
            close_end = block_comment_close_end(line, open_level, pos)
            if close_end is None:
                spans.append((start, end_of_line))
                return spans
            spans.append((start, close_end))
            pos = close_end
            open_level = None

        rest = _mask_string_literals(line[pos:])
        dash = rest.find('--')
        if dash == -1:
            return spans
        start = pos + dash
        opening = BLOCK_COMMENT_OPEN_PATTERN.match(rest, dash)
        if not opening:
            spans.append((start, end_of_line))  # Commentaire de ligne
            return spans
        open_level = opening.group(1)
        pos += opening.end()


def extract_spacing(text: str) -> Tuple[str, int, int]:
    """
    CONTRAINTE 3: Extrait les espaces de formatage d'une chaîne.

    Les espaces de formatage sont situés:
    - Immédiatement après le guillemet ouvrant
    - Immédiatement avant le guillemet fermant

    Args:
        text: Le contenu entre guillemets (sans les guillemets)

    Returns:
        (texte_nettoyé, espaces_début, espaces_fin)
    """
    if not text:
        return text, 0, 0

    # Compter espaces en début
    leading = len(text) - len(text.lstrip(' '))

    # Compter espaces en fin
    trailing = len(text) - len(text.rstrip(' '))

    # Texte nettoyé
    # Seuls les espaces sont du formatage : \n, \t (texte réel) restent dans la valeur
    clean = text.strip(' ')

    return clean, leading, trailing


def extract_all_string_literals(line: str) -> List[Tuple[str, int, int]]:
    """
    Extrait TOUTES les chaines litterales d'une ligne (guillemets doubles uniquement).

    Note: Les guillemets simples ne sont PAS supportés volontairement.
    Le plugin doit utiliser des guillemets doubles conformément au SDK Adobe.
    Les guillemets échappés (\\") font partie du littéral.

    Args:
        line: La ligne de code Lua

    Returns:
        Liste de (texte, position_debut, position_fin) ; le texte est la forme
        source (échappée), à dés-échapper avec unescape_lua_string
    """
    results = []

    # Guillemets doubles uniquement, échappements tolérés
    for match in LUA_STRING_LITERAL_PATTERN.finditer(line):
        text = match.group(1)

        # Filtrer les fausses captures qui contiennent du code Lua
        # Exemple: 'boundary="' .. boundary .. '"' capture '"' .. boundary .. '"'
        # Si la chaîne contient '..' c'est l'opérateur de concaténation Lua
        if '..' in text:
            # C'est probablement du code Lua capturé par erreur, pas une vraie chaîne
            continue

        results.append((text, match.start(), match.end()))

    return results


def is_line_concatenated(line: str) -> bool:
    """
    Vérifie si une ligne contient des concaténations avec ..

    Returns:
        True si la ligne contient ".." entre des chaînes
    """
    return '..' in line


def extract_suffix(text: str) -> Tuple[str, str]:
    """
    Extrait les suffixes communs en fin de chaîne.

    Ces suffixes (" - ", " -", "...") sont fréquents et multiplient
    inutilement le nombre de clés à traduire.

    Args:
        text: Texte nettoyé (sans espaces début/fin)

    Returns:
        (texte_base, suffixe)

    Exemples:
        "Cannot upload - " → ("Cannot upload", " - ")
        "Starting..." → ("Starting", "...")
        "Hello World" → ("Hello World", "")
    """
    if not text:
        return text, ""

    # Tester chaque suffixe (du plus long au plus court)
    for suffix in COMMON_SUFFIXES:
        if text.endswith(suffix):
            base = text[:-len(suffix)]
            # S'assurer que le texte de base n'est pas vide
            if base.strip():
                return base, suffix

    return text, ""


def is_in_technical_context(line: str, rules: PluginRules | None = None) -> bool:
    """
    Vérifie si la ligne est dans un contexte technique.

    Utilisé pour filtrer les chaînes 'value' dans des contextes
    comme les headers HTTP où elles ne doivent pas être traduites.

    Args:
        line: La ligne de code complète
        rules: Règles du plugin (défaut: motifs génériques TECHNICAL_CONTEXT_PATTERNS)

    Returns:
        True si la ligne est dans un contexte technique
    """
    patterns = TECHNICAL_CONTEXT_PATTERNS if rules is None else rules.technical_context_patterns
    for pattern in patterns:
        if pattern.search(line):
            return True
    return False


def is_technical_string(text: str, line_context: str | None = None,
                        rules: PluginRules | None = None) -> bool:
    """
    Vérifie si une chaîne est technique et doit être ignorée.

    Args:
        text: Le texte à vérifier
        line_context: La ligne complète (optionnel, pour contexte)
        rules: Règles du plugin (défaut: règles génériques seules)

    Returns:
        True si la chaîne est technique
    """
    if rules is None:
        rules = PluginRules()
    text_clean = text.strip().lower()
    text_original = text.strip()

    # Chaînes exactes à ignorer (insensible à la casse pour certaines)
    if text_clean in rules.ignore_exact or text_original in rules.ignore_exact:
        return True

    # Patterns techniques
    for pattern in rules.technical_patterns:
        if pattern.search(text_original):
            return True

    # Si on a le contexte de la ligne, vérifier le contexte technique
    if line_context and is_in_technical_context(line_context, rules):
        # Dans un contexte technique, filtrer plus agressivement
        # Ignorer les chaînes qui ressemblent à des identifiants/headers
        if re.match(r'^[A-Za-z][-A-Za-z0-9]*$', text_original):
            return True

    return False


def generate_loc_key(text: str, file_name: str, prefix: str, existing_keys: set,
                     strip_file_prefixes: List[str] | None = None) -> str:
    """
    Génère une clé LOC unique à partir du texte et du nom de fichier.

    Args:
        text: Texte à convertir en clé
        file_name: Nom du fichier source
        prefix: Préfixe LOC (ex: $$$/MyApp)
        existing_keys: Set des clés déjà utilisées pour éviter les doublons
        strip_file_prefixes: Préfixes à retirer du nom de fichier pour la catégorie (défaut: aucun)

    Returns:
        Clé LOC unique
    """
    clean = text.strip()

    # Garder trace de certains suffixes significatifs
    has_ellipsis = clean.endswith('...')
    has_colon = clean.endswith(':')
    has_question = clean.endswith('?')

    # Nettoyer pour extraire les mots
    clean_for_words = clean.rstrip(':?.! ')

    # Extraire les mots significatifs
    words = re.findall(r'[A-Za-z]+', clean_for_words)
    if not words:
        return ""

    # Filtrer les stop words SAUF si le mot est en MAJUSCULES (emphase intentionnelle)
    # Exemple: "Connection NOT successful" → garde "NOT" car il est en majuscules
    key_words = [w for w in words[:6] if w.isupper() or w.lower() not in STOP_WORDS]
    if not key_words:
        key_words = words[:4]

    key_part = ''.join(w.capitalize() for w in key_words[:4])

    # Ajouter suffixe si présent
    if has_ellipsis:
        key_part += "Ellipsis"
    elif has_question:
        key_part += "Question"
    elif has_colon:
        key_part += "Colon"

    # Catégorie basée sur le fichier
    file_base = os.path.splitext(file_name)[0]
    category = file_base
    for file_prefix in strip_file_prefixes or []:
        category = category.replace(file_prefix, '')
    if not category:
        category = 'General'

    base_key = f"{prefix}/{category}/{key_part}"

    # Assurer l'unicité
    final_key = base_key
    counter = 2
    while final_key in existing_keys:
        final_key = f"{base_key}{counter}"
        counter += 1

    return final_key


def build_loc_call(loc_key: str, base_text: str, leading_spaces: int = 0,
                   trailing_spaces: int = 0, suffix: str = "") -> str:
    """
    Construit l'appel LOC Lua (source unique, partagée Extractor/Applicator).

    Les espaces et suffixes sont des littéraux Lua ordinaires : jamais de `_()`,
    qui n'existe pas dans un plugin Lightroom.

    base_text et suffix sont des textes réels (dés-échappés) : `"` et `\\`
    y sont ré-échappés pour produire un littéral Lua valide.

    Exemples:
    - LOC "$$$/K=V"
    - " " .. LOC "$$$/K=V" .. " "
    - LOC "$$$/K=V" .. " - "
    - LOC "$$$/K=Say \\"hi\\""
    """
    parts = []
    if leading_spaces > 0:
        parts.append('"' + ' ' * leading_spaces + '" .. ')
    parts.append('LOC "' + escape_lua_string(loc_key) + '=' + escape_lua_string(base_text) + '"')
    # Le suffixe remplace trailing_spaces (il inclut souvent l'espace)
    if suffix:
        parts.append(' .. "' + escape_lua_string(suffix) + '"')
    elif trailing_spaces > 0:
        parts.append(' .. "' + ' ' * trailing_spaces + '"')
    return ''.join(parts)


def generate_replacement_code(pattern_name: str, loc_key: str,
                               leading: int, trailing: int,
                               suffix: str,
                               original_text: str,
                               base_text: str) -> str:
    """
    Génère le code de remplacement Lua avec gestion des espaces ET des suffixes.

    Format ZString du SDK Lightroom: LOC "$$$/Key=Default Value"
    La valeur par défaut EST OBLIGATOIRE sinon Lightroom affiche la clé brute.

    Exemples:
    - Sans rien: LOC "$$$/key=My Text"
    - 1 espace fin: LOC "$$$/key=My Text" .. " "
    - Suffixe " - ": LOC "$$$/key=My Text" .. " - "
    - 2 espaces début + suffixe: "  " .. LOC "$$$/key=My Text" .. " - "
    """
    replace_str = build_loc_call(loc_key, base_text, leading, trailing, suffix)

    return f'"{original_text}" → {replace_str}'
