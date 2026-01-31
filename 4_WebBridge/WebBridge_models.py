#!/usr/bin/env python3
"""
WebBridge_models.py

Classes de données pour le module WebBridge.
Définit la structure pour l'export/import entre format Lightroom SDK et i18n JSON.

Classes:
    - I18nMeta: Métadonnées du fichier JSON i18n
    - I18nEntry: Une entrée de traduction individuelle
    - I18nTranslations: Structure complète du fichier i18n JSON
    - SpacingMetadata: Métadonnées d'espacement d'une clé LOC
    - ValidationResult: Résultat de validation d'un fichier i18n

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-31
Version : 1.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime


@dataclass
class SpacingMetadata:
    """
    Métadonnées d'espacement pour une clé LOC.

    Préserve les espaces de début/fin et suffixes intentionnels
    qui sont critiques pour l'affichage dans Lightroom.

    Attributes:
        original_text: Texte original complet du code Lua
        clean_text: Texte nettoyé (sans espaces inutiles)
        base_text: Texte de base sans espaces ni suffixes
        leading_spaces: Nombre d'espaces de début
        trailing_spaces: Nombre d'espaces de fin
        suffix: Suffixe intentionnel (ex: " -", ":", "...")
        file: Fichier source Lua
        line: Numéro de ligne dans le fichier source

    Example:
        >>> meta = SpacingMetadata(
        ...     original_text="Cannot log in to Piwigo - ",
        ...     clean_text="Cannot log in to Piwigo -",
        ...     base_text="Cannot log in to Piwigo",
        ...     leading_spaces=0,
        ...     trailing_spaces=0,
        ...     suffix=" -",
        ...     file="PiwigoAPI.lua",
        ...     line=235
        ... )
    """
    original_text: str
    clean_text: str
    base_text: str
    leading_spaces: int = 0
    trailing_spaces: int = 0
    suffix: str = ""
    file: str = ""
    line: int = 0

    def has_spacing_metadata(self) -> bool:
        """Retourne True si cette entrée a des métadonnées d'espacement."""
        return self.leading_spaces > 0 or self.trailing_spaces > 0 or len(self.suffix) > 0

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour JSON."""
        result = {}
        if self.leading_spaces > 0:
            result["leading_spaces"] = self.leading_spaces
        if self.trailing_spaces > 0:
            result["trailing_spaces"] = self.trailing_spaces
        if self.suffix:
            result["suffix"] = self.suffix
        return result

    @staticmethod
    def from_dict(data: dict) -> Optional['SpacingMetadata']:
        """
        Crée une instance depuis un dictionnaire.

        Args:
            data: Dictionnaire avec les métadonnées d'espacement

        Returns:
            Instance SpacingMetadata ou None si data est None
        """
        if data is None:
            return None

        return SpacingMetadata(
            original_text="",
            clean_text="",
            base_text="",
            leading_spaces=data.get("leading_spaces", 0),
            trailing_spaces=data.get("trailing_spaces", 0),
            suffix=data.get("suffix", "")
        )


@dataclass
class I18nEntry:
    """
    Une entrée de traduction individuelle dans le format i18n.

    Attributes:
        text: Le texte traduit
        context: Contexte optionnel (fichier:ligne) - uniquement pour EN
        metadata: Métadonnées d'espacement optionnelles
        default: Chaîne originale (EN) - utile lors de l'édition du JSON pour voir la référence

    Example:
        >>> entry = I18nEntry(
        ...     text="Cannot log in to Piwigo",
        ...     context="PiwigoAPI.lua:235",
        ...     default="Cannot log in to Piwigo",
        ...     metadata={"suffix": " -"}
        ... )
    """
    text: str
    context: Optional[str] = None
    default: Optional[str] = None
    metadata: Optional[Dict[str, any]] = None

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour JSON."""
        result = {"text": self.text}
        if self.context:
            result["context"] = self.context
        if self.default:
            result["default"] = self.default
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @staticmethod
    def from_dict(data: dict) -> 'I18nEntry':
        """
        Crée une instance depuis un dictionnaire.

        Args:
            data: Dictionnaire avec text, context?, default?, metadata?

        Returns:
            Instance I18nEntry
        """
        if isinstance(data, str):
            # Format simple: juste le texte
            return I18nEntry(text=data)

        return I18nEntry(
            text=data.get("text", ""),
            context=data.get("context"),
            default=data.get("default"),
            metadata=data.get("metadata")
        )


@dataclass
class I18nMeta:
    """
    Métadonnées du fichier JSON i18n.

    Attributes:
        version: Version du format (ex: "1.0")
        generated: Timestamp de génération ISO 8601
        plugin_name: Nom du plugin Lightroom (ex: "piwigoPublish.lrplugin")
        prefix: Préfixe LOC (ex: "$$$/Piwigo")
        source_extraction: Chemin de l'extraction source (ex: "Extractor/20260130_223727")
        total_keys: Nombre total de clés
        languages: Liste des langues disponibles
        translator_notes: Notes pour les traducteurs
        webbridge_version: Version de WebBridge

    Example:
        >>> meta = I18nMeta(
        ...     version="1.0",
        ...     generated="2026-01-31T10:30:00.123456",
        ...     plugin_name="piwigoPublish.lrplugin",
        ...     prefix="$$$/Piwigo",
        ...     total_keys=272,
        ...     languages=["en", "fr"]
        ... )
    """
    version: str = "1.0"
    generated: str = ""
    plugin_name: str = ""
    prefix: str = ""
    source_extraction: str = ""
    total_keys: int = 0
    languages: List[str] = field(default_factory=list)
    translator_notes: str = "DO NOT translate: %s, %d, \\n. PRESERVE spaces around text."
    webbridge_version: str = "1.0.0"

    def __post_init__(self):
        """Génère le timestamp si non fourni."""
        if not self.generated:
            self.generated = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour JSON."""
        return {
            "version": self.version,
            "generated": self.generated,
            "plugin_name": self.plugin_name,
            "prefix": self.prefix,
            "source_extraction": self.source_extraction,
            "total_keys": self.total_keys,
            "languages": self.languages,
            "translator_notes": self.translator_notes,
            "webbridge_version": self.webbridge_version
        }

    @staticmethod
    def from_dict(data: dict) -> 'I18nMeta':
        """
        Crée une instance depuis un dictionnaire.

        Args:
            data: Dictionnaire avec les métadonnées

        Returns:
            Instance I18nMeta
        """
        return I18nMeta(
            version=data.get("version", "1.0"),
            generated=data.get("generated", ""),
            plugin_name=data.get("plugin_name", ""),
            prefix=data.get("prefix", ""),
            source_extraction=data.get("source_extraction", ""),
            total_keys=data.get("total_keys", 0),
            languages=data.get("languages", []),
            translator_notes=data.get("translator_notes", ""),
            webbridge_version=data.get("webbridge_version", "1.0.0")
        )


@dataclass
class I18nTranslations:
    """
    Structure complète du fichier i18n JSON.

    Attributes:
        meta: Métadonnées du fichier
        translations: Dictionnaire des traductions par langue
                     Format: {lang: {category: {key: I18nEntry}}}

    Example:
        >>> translations = I18nTranslations(
        ...     meta=I18nMeta(...),
        ...     translations={
        ...         "en": {
        ...             "API": {
        ...                 "AddTags": I18nEntry(text="to add tags", context="PiwigoAPI.lua:145")
        ...             }
        ...         }
        ...     }
        ... )
    """
    meta: I18nMeta
    translations: Dict[str, Dict[str, Dict[str, I18nEntry]]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convertit en dictionnaire pour JSON.

        Returns:
            Dictionnaire compatible avec le format i18n JSON
        """
        result = {
            "_meta": self.meta.to_dict(),
            "translations": {}
        }

        for lang, categories in self.translations.items():
            result["translations"][lang] = {}
            for category, keys in categories.items():
                result["translations"][lang][category] = {}
                for key, entry in keys.items():
                    result["translations"][lang][category][key] = entry.to_dict()

        return result

    @staticmethod
    def from_dict(data: dict) -> 'I18nTranslations':
        """
        Crée une instance depuis un dictionnaire.

        Args:
            data: Dictionnaire avec _meta et translations

        Returns:
            Instance I18nTranslations
        """
        meta = I18nMeta.from_dict(data.get("_meta", {}))
        translations = {}

        translations_data = data.get("translations", {})
        for lang, categories in translations_data.items():
            translations[lang] = {}
            for category, keys in categories.items():
                translations[lang][category] = {}
                for key, entry_data in keys.items():
                    translations[lang][category][key] = I18nEntry.from_dict(entry_data)

        return I18nTranslations(meta=meta, translations=translations)

    def get_all_keys(self, lang: str = "en") -> Set[str]:
        """
        Récupère toutes les clés pour une langue donnée.

        Args:
            lang: Code langue (défaut: "en")

        Returns:
            Ensemble des clés au format "category.key"
        """
        keys = set()
        if lang in self.translations:
            for category, category_keys in self.translations[lang].items():
                for key in category_keys.keys():
                    keys.add(f"{category}.{key}")
        return keys

    def get_entry(self, lang: str, category: str, key: str) -> Optional[I18nEntry]:
        """
        Récupère une entrée spécifique.

        Args:
            lang: Code langue
            category: Catégorie
            key: Nom de la clé

        Returns:
            I18nEntry ou None si introuvable
        """
        return (self.translations
                .get(lang, {})
                .get(category, {})
                .get(key))

    def add_entry(self, lang: str, category: str, key: str, entry: I18nEntry):
        """
        Ajoute une entrée de traduction.

        Args:
            lang: Code langue
            category: Catégorie
            key: Nom de la clé
            entry: Entrée à ajouter
        """
        if lang not in self.translations:
            self.translations[lang] = {}
        if category not in self.translations[lang]:
            self.translations[lang][category] = {}
        self.translations[lang][category][key] = entry


@dataclass
class ValidationError:
    """
    Représente une erreur de validation.

    Attributes:
        level: Niveau de sévérité ("error", "warning")
        message: Message d'erreur
        category: Catégorie de l'erreur optionnelle (ex: "structure", "placeholders")
        key: Clé concernée optionnelle (ex: "API.AddTags")
        language: Langue concernée optionnelle (ex: "fr")
        location: Emplacement optionnel (ex: "fr.API.AddTags")
        details: Détails supplémentaires optionnels (dict ou str)
    """
    level: str  # "error" ou "warning"
    message: str
    category: Optional[str] = None
    key: Optional[str] = None
    language: Optional[str] = None
    location: Optional[str] = None
    details: Optional[any] = None

    def __str__(self) -> str:
        """Représentation textuelle de l'erreur."""
        result = f"[{self.level.upper()}] {self.message}"
        if self.location:
            result += f" ({self.location})"
        elif self.key and self.language:
            result += f" ({self.language}.{self.key})"
        if self.details:
            if isinstance(self.details, dict):
                result += "\n  " + "\n  ".join(f"{k}: {v}" for k, v in self.details.items())
            else:
                result += f"\n  {self.details}"
        return result


@dataclass
class ValidationResult:
    """
    Résultat de validation d'un fichier i18n.

    Attributes:
        valid: True si aucune erreur bloquante
        errors: Liste des erreurs bloquantes
        warnings: Liste des avertissements non-bloquants
        stats: Statistiques de validation optionnelles

    Example:
        >>> result = ValidationResult(
        ...     valid=True,
        ...     errors=[],
        ...     warnings=[
        ...         ValidationError(
        ...             level="warning",
        ...             message="2 clés manquantes",
        ...             location="fr"
        ...         )
        ...     ]
        ... )
    """
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    stats: Dict[str, any] = field(default_factory=dict)

    def add_error(self, message: str, location: Optional[str] = None, details: Optional[str] = None):
        """Ajoute une erreur bloquante."""
        self.errors.append(ValidationError("error", message, location, details))
        self.valid = False

    def add_warning(self, message: str, location: Optional[str] = None, details: Optional[str] = None):
        """Ajoute un avertissement non-bloquant."""
        self.warnings.append(ValidationError("warning", message, location, details))

    def has_errors(self) -> bool:
        """Retourne True si des erreurs bloquantes existent."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Retourne True si des avertissements existent."""
        return len(self.warnings) > 0

    def is_valid(self) -> bool:
        """Retourne True si aucune erreur bloquante (warnings OK)."""
        return self.valid

    def error_count(self) -> int:
        """Retourne le nombre d'erreurs."""
        return len(self.errors)

    def warning_count(self) -> int:
        """Retourne le nombre d'avertissements."""
        return len(self.warnings)

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour JSON."""
        return {
            "valid": self.valid,
            "errors": [str(e) for e in self.errors],
            "warnings": [str(w) for w in self.warnings],
            "stats": self.stats
        }
