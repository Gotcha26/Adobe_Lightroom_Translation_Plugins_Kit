#!/usr/bin/env python3
"""
WebBridge_validator.py

Validation du fichier JSON i18n avant import.

Fonctions principales:
    - validate_structure: Valide la structure de base du JSON
    - validate_reference_language: Valide la langue de référence (EN)
    - validate_key_consistency: Valide la cohérence des clés entre langues
    - validate_placeholders: Valide les placeholders entre EN et traductions
    - validate_i18n_file: Fonction principale de validation

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-31
Version : 1.0
"""

import os
import re
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime

from WebBridge_models import ValidationError, ValidationResult, I18nTranslations
from WebBridge_utils import (
    extract_placeholders, compare_placeholders, load_json_file
)


def extract_all_keys(lang_translations: Dict) -> Set[str]:
    """
    Extrait toutes les clés d'une langue sous forme de set.

    Args:
        lang_translations: Dictionnaire des traductions d'une langue
                          Format: {category: {key: entry}}

    Returns:
        Set de clés au format "category.key"

    Example:
        >>> trans = {"API": {"AddTags": {...}, "Cancel": {...}}}
        >>> extract_all_keys(trans)
        {'API.AddTags', 'API.Cancel'}
    """
    keys = set()
    for category, category_dict in lang_translations.items():
        if not isinstance(category_dict, dict):
            continue
        for key in category_dict.keys():
            keys.add(f"{category}.{key}")
    return keys


def validate_structure(data: Dict) -> List[ValidationError]:
    """
    Valide la structure de base du JSON i18n.

    Vérifie:
    - Présence de _meta
    - Présence de translations
    - Structure des sections

    Args:
        data: Dictionnaire chargé depuis le JSON

    Returns:
        Liste d'erreurs de validation (vide si valide)
    """
    errors = []

    # 1. Vérifier _meta
    if "_meta" not in data:
        errors.append(ValidationError(
            level="error",
            category="structure",
            message="Section '_meta' manquante dans le JSON"
        ))
    else:
        meta = data["_meta"]
        required_meta_fields = ["version", "plugin_name", "prefix", "total_keys", "languages"]
        for field in required_meta_fields:
            if field not in meta:
                errors.append(ValidationError(
                    level="warning",
                    category="structure",
                    message=f"Champ '_meta.{field}' manquant"
                ))

    # 2. Vérifier translations
    if "translations" not in data:
        errors.append(ValidationError(
            level="error",
            category="structure",
            message="Section 'translations' manquante dans le JSON"
        ))
    else:
        translations = data["translations"]
        if not isinstance(translations, dict):
            errors.append(ValidationError(
                level="error",
                category="structure",
                message="Section 'translations' doit être un dictionnaire"
            ))

    return errors


def validate_reference_language(data: Dict) -> List[ValidationError]:
    """
    Valide la présence et la complétude de la langue de référence (EN).

    Args:
        data: Dictionnaire chargé depuis le JSON

    Returns:
        Liste d'erreurs de validation
    """
    errors = []

    if "translations" not in data:
        return errors  # Déjà signalé dans validate_structure

    translations = data["translations"]

    # Vérifier présence de "en"
    if "en" not in translations:
        errors.append(ValidationError(
            level="error",
            category="reference_language",
            message="Langue de référence 'en' manquante dans 'translations'"
        ))
        return errors

    # Vérifier que EN n'est pas vide
    en_trans = translations["en"]
    if not en_trans or len(en_trans) == 0:
        errors.append(ValidationError(
            level="error",
            category="reference_language",
            message="Langue de référence 'en' est vide"
        ))

    # Vérifier structure de EN
    for category, category_dict in en_trans.items():
        if not isinstance(category_dict, dict):
            errors.append(ValidationError(
                level="error",
                category="reference_language",
                message=f"Catégorie 'en.{category}' doit être un dictionnaire"
            ))
            continue

        for key, entry in category_dict.items():
            if not isinstance(entry, dict):
                errors.append(ValidationError(
                    level="error",
                    category="reference_language",
                    message=f"Entrée 'en.{category}.{key}' doit être un dictionnaire"
                ))
                continue

            if "text" not in entry:
                errors.append(ValidationError(
                    level="error",
                    category="reference_language",
                    message=f"Champ 'text' manquant dans 'en.{category}.{key}'"
                ))

    return errors


def validate_key_consistency(data: Dict) -> List[ValidationError]:
    """
    Valide la cohérence des clés entre EN et les autres langues.

    Vérifie:
    - Clés manquantes dans les traductions (warning)
    - Clés supplémentaires dans les traductions (warning)

    Args:
        data: Dictionnaire chargé depuis le JSON

    Returns:
        Liste d'erreurs/avertissements de validation
    """
    errors = []

    if "translations" not in data or "en" not in data["translations"]:
        return errors  # Déjà signalé ailleurs

    translations = data["translations"]
    en_keys = extract_all_keys(translations["en"])

    for lang, lang_trans in translations.items():
        if lang == "en":
            continue

        lang_keys = extract_all_keys(lang_trans)
        missing = en_keys - lang_keys
        extra = lang_keys - en_keys

        if missing:
            errors.append(ValidationError(
                level="warning",
                category="key_consistency",
                message=f"[{lang}] {len(missing)} clé(s) manquante(s) (utiliseront EN par défaut)",
                details={"missing_keys": sorted(list(missing)[:10])}  # Limiter à 10 pour lisibilité
            ))

        if extra:
            errors.append(ValidationError(
                level="warning",
                category="key_consistency",
                message=f"[{lang}] {len(extra)} clé(s) supplémentaire(s) (seront ignorées)",
                details={"extra_keys": sorted(list(extra)[:10])}
            ))

    return errors


def validate_placeholders(data: Dict) -> List[ValidationError]:
    """
    Valide que les placeholders sont identiques entre EN et les traductions.

    Args:
        data: Dictionnaire chargé depuis le JSON

    Returns:
        Liste d'erreurs de validation
    """
    errors = []

    if "translations" not in data or "en" not in data["translations"]:
        return errors

    translations = data["translations"]
    en_trans = translations["en"]

    for lang, lang_trans in translations.items():
        if lang == "en":
            continue

        for category, category_dict in en_trans.items():
            if not isinstance(category_dict, dict):
                continue

            for key, en_entry in category_dict.items():
                if not isinstance(en_entry, dict) or "text" not in en_entry:
                    continue

                en_text = en_entry["text"]
                en_placeholders = extract_placeholders(en_text)

                if not en_placeholders:
                    continue  # Pas de placeholders à vérifier

                # Vérifier si la clé existe dans la traduction
                if category not in lang_trans or key not in lang_trans[category]:
                    continue  # Déjà signalé dans key_consistency

                target_entry = lang_trans[category][key]
                if not isinstance(target_entry, dict) or "text" not in target_entry:
                    continue

                target_text = target_entry["text"]

                # Comparer les placeholders
                match, en_only, target_only = compare_placeholders(en_text, target_text)

                if not match:
                    errors.append(ValidationError(
                        level="error",
                        category="placeholders",
                        message=f"[{lang}] {category}.{key}: Placeholders différents",
                        key=f"{category}.{key}",
                        language=lang,
                        details={
                            "en_text": en_text,
                            "target_text": target_text,
                            "en_placeholders": sorted(extract_placeholders(en_text)),
                            "target_placeholders": sorted(extract_placeholders(target_text)),
                            "missing": sorted(en_only),
                            "extra": sorted(target_only)
                        }
                    ))

    return errors


def validate_metadata(data: Dict) -> List[ValidationError]:
    """
    Valide les métadonnées d'espacement.

    Vérifie:
    - Format des métadonnées
    - Champs valides

    Args:
        data: Dictionnaire chargé depuis le JSON

    Returns:
        Liste d'avertissements de validation
    """
    errors = []

    if "translations" not in data:
        return errors

    translations = data["translations"]
    valid_metadata_fields = {"leading_spaces", "trailing_spaces", "suffix"}

    for lang, lang_trans in translations.items():
        for category, category_dict in lang_trans.items():
            if not isinstance(category_dict, dict):
                continue

            for key, entry in category_dict.items():
                if not isinstance(entry, dict):
                    continue

                if "metadata" not in entry:
                    continue

                metadata = entry["metadata"]
                if not isinstance(metadata, dict):
                    errors.append(ValidationError(
                        level="warning",
                        category="metadata",
                        message=f"[{lang}] {category}.{key}: 'metadata' doit être un dictionnaire",
                        key=f"{category}.{key}",
                        language=lang
                    ))
                    continue

                # Vérifier les champs
                for field in metadata.keys():
                    if field not in valid_metadata_fields:
                        errors.append(ValidationError(
                            level="warning",
                            category="metadata",
                            message=f"[{lang}] {category}.{key}: Champ 'metadata.{field}' inconnu",
                            key=f"{category}.{key}",
                            language=lang
                        ))

    return errors


def validate_i18n_file(
    filepath: Optional[str] = None,
    data: Optional[Dict] = None
) -> ValidationResult:
    """
    Fonction principale de validation d'un fichier JSON i18n.

    Args:
        filepath: Chemin du fichier JSON (optionnel si data fourni)
        data: Dictionnaire JSON (optionnel si filepath fourni)

    Returns:
        ValidationResult avec erreurs et avertissements

    Raises:
        ValueError: Si ni filepath ni data n'est fourni
        FileNotFoundError: Si le fichier n'existe pas

    Example:
        >>> result = validate_i18n_file("translations.json")
        >>> if result.is_valid():
        ...     print("Fichier valide!")
        >>> else:
        ...     for error in result.errors:
        ...         print(f"[{error.level}] {error.message}")
    """
    if filepath is None and data is None:
        raise ValueError("filepath ou data doit être fourni")

    # Charger le fichier si nécessaire
    if data is None:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Fichier introuvable: {filepath}")
        data = load_json_file(filepath)
        if not data:
            return ValidationResult(
                valid=False,
                errors=[ValidationError(
                    level="error",
                    category="file",
                    message=f"Impossible de charger le fichier JSON: {filepath}"
                )]
            )

    # Exécuter toutes les validations
    all_errors = []

    # 1. Structure
    all_errors.extend(validate_structure(data))

    # Si structure invalide, arrêter ici
    structure_errors = [e for e in all_errors if e.level == "error"]
    if structure_errors:
        return ValidationResult(valid=False, errors=all_errors)

    # 2. Langue de référence
    all_errors.extend(validate_reference_language(data))

    # Si langue de référence invalide, arrêter ici
    ref_errors = [e for e in all_errors if e.level == "error" and e.category == "reference_language"]
    if ref_errors:
        return ValidationResult(valid=False, errors=all_errors)

    # 3. Cohérence des clés
    all_errors.extend(validate_key_consistency(data))

    # 4. Placeholders
    all_errors.extend(validate_placeholders(data))

    # 5. Métadonnées
    all_errors.extend(validate_metadata(data))

    # Déterminer si valide (pas d'erreurs, warnings OK)
    errors = [e for e in all_errors if e.level == "error"]
    warnings = [e for e in all_errors if e.level == "warning"]

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_i18n_object(translations: I18nTranslations) -> ValidationResult:
    """
    Valide un objet I18nTranslations.

    Args:
        translations: Objet I18nTranslations à valider

    Returns:
        ValidationResult
    """
    data = translations.to_dict()
    return validate_i18n_file(data=data)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        filepath = sys.argv[1]

        print(f"Validation de: {filepath}\n")
        result = validate_i18n_file(filepath)

        print(f"Valide: {'OUI' if result.is_valid() else 'NON'}")
        print(f"Erreurs: {result.error_count()}")
        print(f"Avertissements: {result.warning_count()}\n")

        if result.errors:
            print("ERREURS:")
            print("-" * 80)
            for error in result.errors:
                print(f"  [{error.category}] {error.message}")
                if error.details:
                    for k, v in error.details.items():
                        print(f"    {k}: {v}")
            print()

        if result.warnings:
            print("AVERTISSEMENTS:")
            print("-" * 80)
            for warning in result.warnings:
                print(f"  [{warning.category}] {warning.message}")
                if warning.details:
                    for k, v in warning.details.items():
                        print(f"    {k}: {v}")
            print()

        sys.exit(0 if result.is_valid() else 1)
    else:
        print("Usage: python WebBridge_validator.py <fichier_json>")
        sys.exit(1)
