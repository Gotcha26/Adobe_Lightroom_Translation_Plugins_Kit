# WebBridge - Pont de Conversion i18n pour Lightroom Plugins

## Vue d'ensemble

Le module **WebBridge** est **pleinement opérationnel** et permet de convertir les fichiers de localisation Lightroom (format propriétaire `.txt`) vers un format JSON i18n standard, compatible avec des outils web modernes comme [quicki18n.studio](https://www.quicki18n.studio/).

### Problème résolu

Les traducteurs ne sont pas des développeurs. Éditer des fichiers `TranslatedStrings_xx.txt` directement est :
- Peu convivial (format propriétaire du SDK Lightroom)
- Sujet aux erreurs de formatage (risque de casser le plugin)
- Sans aide visuelle ou contextuelle (pas de contexte fichier:ligne)
- Difficile à organiser pour plusieurs langues (1 fichier à la fois)

### Solution apportée

WebBridge crée un **pont bidirectionnel automatique** entre :
- **Format Lightroom SDK** : `TranslatedStrings_xx.txt` (source de vérité finale, compatible Lightroom)
- **Format i18n JSON** : Compatible avec outils web modernes (édition visuelle intuitive)

**Statut** : ✅ Testé et validé sur le plugin PiwigoPublish (278 clés)

---

## Architecture

```
4_WebBridge/
├── __doc/                        # Documentation
│   ├── Lisez-moi.md             # Documentation française
│   └── README.md                # Documentation anglaise
│
├── WebBridge_main.py             # Interface principale (menu interactif)
├── WebBridge_export.py           # Export .txt → .json
├── WebBridge_import.py           # Import .json → .txt
├── WebBridge_models.py           # Classes de données
├── WebBridge_utils.py            # Utilitaires de parsing
└── WebBridge_validator.py        # Validation stricte
```

---

## Workflow complet

### 1. Développeur : Extraction et export

```bash
# Étape 1 : Extraire les chaînes du code Lua
python LocalizationToolkit.py
# Sélectionner [1] Extractor
# → Génère TranslatedStrings_en.txt

# Étape 2 : Exporter vers format JSON
python LocalizationToolkit.py
# Sélectionner [8] Export Web (WebBridge)
# → Génère translations.json

# Étape 3 : Envoyer translations.json au traducteur
# (Email, GitHub, Dropbox, etc.)
```

### 2. Traducteur : Édition visuelle (aucun outil à installer)

```
1. Recevoir le fichier translations.json
2. Ouvrir https://www.quicki18n.studio/ dans le navigateur
3. Cliquer "Import JSON" et sélectionner translations.json
4. Sélectionner la langue à traduire (FR, DE, ES, etc.)
5. Traduire visuellement clé par clé
   - Texte EN visible à gauche (référence)
   - Champ traduction à droite (éditable)
   - Contexte fichier:ligne visible
6. Cliquer "Export JSON"
7. Renvoyer translations.json au développeur
```

### 3. Développeur : Import et finalisation

```bash
# Étape 1 : Importer le JSON traduit
python LocalizationToolkit.py
# Sélectionner [9] Import Web (WebBridge)
# → Validation automatique (placeholders, structure)
# → Génère TranslatedStrings_fr.txt, TranslatedStrings_de.txt, etc.

# Étape 2 : Copier dans le plugin
cp __i18n_tmp__/4_WebBridge/<timestamp>/TranslatedStrings_*.txt .

# Étape 3 : Tester dans Lightroom
# Recharger le plugin et vérifier les traductions
```

**Note importante** : Pas besoin d'utiliser les outils COMPARE, EXTRACT, INJECT ou SYNC du TranslationManager. WebBridge gère tout automatiquement.

---

## Exemple concret : Plugin PiwigoPublish

Voici un exemple réel d'utilisation avec le plugin **PiwigoPublish** (278 clés) :

### Développeur

```bash
# Export
python LocalizationToolkit.py
# [1] Extractor → 278 clés extraites
# [8] Export Web → translations.json généré

# Résultat
__i18n_tmp__/4_WebBridge/20260131_164318/translations.json
```

### Traducteur

1. Reçoit `translations.json` (278 clés EN)
2. Ouvre https://www.quicki18n.studio/
3. Importe le fichier
4. Traduit en français (exemple) :
   - `"Cannot log in to Piwigo"` → `"Impossible de se connecter à Piwigo"`
   - `"Albums created on Piwigo: %s"` → `"Albums créés sur Piwigo : %s"`
   - Contexte visible : `PiwigoAPI.lua:1352`
5. Exporte `translations.json` (FR ajouté)
6. Renvoie au développeur

### Développeur

```bash
# Import
python LocalizationToolkit.py
# [9] Import Web → TranslatedStrings_fr.txt généré (278 clés)

# Résultat
__i18n_tmp__/4_WebBridge/20260131_165500/TranslatedStrings_fr.txt

# Copier
cp __i18n_tmp__/4_WebBridge/20260131_165500/TranslatedStrings_*.txt piwigoPublish.lrplugin/
```

**Temps total développeur** : 5-10 minutes
**Aucune erreur de formatage** : Validation automatique

---

## Format JSON i18n

### Structure

```json
{
  "_meta": {
    "version": "1.0",
    "generated": "2026-01-31T10:30:00",
    "plugin_name": "monPlugin.lrplugin",
    "prefix": "$$$/MonPlugin",
    "source_extraction": "Extractor/20260130_223727",
    "total_keys": 272,
    "languages": ["en", "fr", "de"],
    "translator_notes": "DO NOT translate: %s, %d, \\n. PRESERVE spaces.",
    "webbridge_version": "1.0.0"
  },
  "translations": {
    "en": {
      "Category1": {
        "Key1": {
          "text": "English text",
          "context": "FileName.lua:123 - Description",
          "metadata": {
            "suffix": ":",
            "trailing_spaces": 1
          }
        }
      }
    },
    "fr": {
      "Category1": {
        "Key1": {
          "text": "Texte français",
          "default": "English text",
          "context": "FileName.lua:123 - Description"
        }
      }
    }
  }
}
```

### Champs

- **`_meta`** : Métadonnées de version et traçabilité
- **`translations`** : Traductions par langue
  - **Niveau 1** : Code langue (ISO 639-1)
  - **Niveau 2** : Catégorie (ex: API, Dialogs)
  - **Niveau 3** : Clé
  - **Valeur** : Objet avec :
    - `text` (obligatoire) : Le texte traduit
    - `context` (présent par défaut) : Contexte du code source (fichier:ligne) - peut être désactivé via option [4]
    - `default` (absent par défaut) : Chaîne originale (EN) - peut être activée via option [5] pour référence directe lors de l'édition
    - `metadata` (optionnel) : Métadonnées d'espacement

### Champ `default` (chaîne de référence) - OPTIONNEL

Optionnellement, vous pouvez inclure le champ `default` contenant la chaîne originale EN dans chaque clé (toutes les langues). Cela facilite la traduction et le maintien de la qualité :

```json
"en": {
  "API": {
    "AddTags": {
      "text": "to add tags",
      "default": "to add tags",  // ← Même valeur pour EN (référence)
      "context": "PiwigoAPI.lua:123"
    }
  }
},
"fr": {
  "API": {
    "AddTags": {
      "text": "pour ajouter des tags",
      "default": "to add tags",  // ← Référence EN visible lors de l'édition
      "context": "PiwigoAPI.lua:123"
    }
  }
}
```

**Avantages** :
- Les traducteurs voient directement le texte original en éditant le JSON
- Pas besoin de chercher dans plusieurs fichiers
- Maintien plus facile de la cohérence de traduction
- Comparaison directe lors de l'édition manuelle
- Pour EN: permet une cohérence visuelle du JSON

**Quand l'inclure ?**
- ✓ Utile si les traducteurs éditent manuellement le JSON et veulent voir la référence
- ✓ Aide à la comparaison directe EN/traduction
- ✗ Ajoute du volume au JSON (non-bloquant)
- ✗ Non nécessaire si utilisant uniquement quicki18n.studio

**Configuration** :
- Menu interactif : Option **[5] Inclure champ 'default'** en mode export
- CLI : Ajouter le flag `--include-default` à l'export
- Défaut : **Désactivé** (pour un JSON plus léger)

### Métadonnées critiques

Certaines chaînes ont des **espaces ou suffixes intentionnels** :

```json
"metadata": {
  "suffix": " -",           // Suffixe à réappliquer (ex: "Cannot log in to Piwigo -")
  "leading_spaces": 2,      // Espaces avant le texte (alignement)
  "trailing_spaces": 1      // Espaces après le texte (concaténation)
}
```

**Ces métadonnées sont préservées automatiquement** lors de l'export/import.

### Option: Inclure le contexte (fichier:ligne)

Par défaut, le JSON exporté inclut le **contexte source** (fichier:ligne) pour chaque clé :

```json
"CannotLogPiwigo": {
  "text": "Cannot log in to Piwigo",
  "context": "PiwigoAPI.lua:1352"  // ← Présent par défaut
}
```

**Quand le désactiver ?**
- ✓ Si vous voulez un JSON plus léger (sans contexte source)
- ✓ Si les traducteurs utilisent uniquement quicki18n.studio
- ✗ Utile de garder si naviguer dans le code source Lua pendant la traduction
- ✗ Aide à comprendre le contexte d'utilisation

**Configuration** :
- Menu interactif : Option **[4] Inclure contexte** en mode export (désactiver si souhaité)
- CLI : Ajouter le flag `--no-context` à l'export
- Défaut : **Activé** (inclusion du contexte source)

---

## Validation stricte

### À l'export

- Vérification présence `TranslatedStrings_en.txt` (obligatoire)
- Détection métadonnées d'espacement
- Extraction du contexte si disponible

### À l'import

**Validations critiques (bloquent l'import)** :
- Structure JSON valide (schéma respecté)
- Langue de référence `en` présente
- **Placeholders identiques** (`%s`, `%d`, `\n`, etc.)

**Validations non-bloquantes (avertissements)** :
- Clés manquantes dans langues cibles (→ utiliseront valeur EN)
- Clés supplémentaires (→ ignorées)

### Exemple de rapport de validation

```
═══════════════════════════════════════════════════════════
RAPPORT DE VALIDATION
═══════════════════════════════════════════════════════════

✓ Structure JSON valide
✓ Langue de référence (en) présente
✓ 272 clés validées

[FR] Statut :
  ✓ 270 clés traduites
  ⚠ 2 clés manquantes (utiliseront valeur EN)
  ✓ Placeholders préservés

[DE] Statut :
  ✓ 272 clés traduites
  ✓ Placeholders préservés

═══════════════════════════════════════════════════════════
AUCUNE ERREUR CRITIQUE - Import autorisé
═══════════════════════════════════════════════════════════
```

---

## Utilisation

### Mode interactif (recommandé)

```bash
# Depuis le toolkit principal
python LocalizationToolkit.py

# Menu affiché :
# [8] Export Web     - Exporter pour quicki18n.studio
# [9] Import Web     - Importer depuis quicki18n.studio
```

### Mode CLI

```bash
# Export
python LocalizationToolkit.py web-export

# Import
python LocalizationToolkit.py web-import

# Validation seule (sans import)
python 4_WebBridge/WebBridge_import.py \
    --json-file "i18n_translations.json" \
    --plugin-path "D:/plugin.lrplugin" \
    --validate-only
```

### Utilisation directe

```bash
# Export avec options
python 4_WebBridge/WebBridge_export.py \
    --plugin-path "D:/plugin.lrplugin" \
    --extraction-dir "Extractor/20260130_223727" \
    --output "i18n_translations.json" \
    --languages en fr de

# Import avec options
python 4_WebBridge/WebBridge_import.py \
    --json-file "i18n_translations.json" \
    --plugin-path "D:/plugin.lrplugin" \
    --output-dir "__i18n_tmp__/WebBridge/20260131_143000"
```

---

## Tests

### Lancer les tests

```bash
# Tous les tests
python -m pytest tests/ -v

# Test spécifique
python -m pytest tests/test_export.py -v

# Test aller-retour (critique)
python -m pytest tests/test_roundtrip.py -v
```

### Test aller-retour

Le test le plus important vérifie qu'**aucune donnée n'est perdue** :

1. Charger `TranslatedStrings_en.txt` original
2. Export → `i18n_translations.json`
3. Import → `TranslatedStrings_en_new.txt`
4. Comparer original vs new (doivent être identiques)

---

## Compatibilité

### Outils web supportés

- ✅ [quicki18n.studio](https://www.quicki18n.studio/) - Éditeur browser-based, 100% local
- ⚠️ Autres outils i18n (à tester)

### Lightroom SDK

Compatible avec toutes les versions du SDK Adobe Lightroom Classic qui utilisent le format `TranslatedStrings_xx.txt`.

### Plateformes

- ✅ Windows
- ✅ macOS
- ✅ Linux

---

## Sécurité des données

### Règles absolues

1. **Source de vérité** : Les fichiers `TranslatedStrings_xx.txt` restent la seule source de vérité finale
2. **Pas de perte** : Le format JSON est un format **intermédiaire de travail** uniquement
3. **Validation stricte** : Placeholders, métadonnées, structure vérifiés avant tout import
4. **Backups automatiques** : L'Applicator crée toujours des backups avant modification

### Tests de sécurité

- ✅ Test aller-retour (roundtrip) → Aucune perte de données
- ✅ Validation des placeholders → Runtime Lightroom sûr
- ✅ Préservation métadonnées → Formatage correct

---

## Limitations connues

1. **quicki18n.studio** : Outil externe (mais gratuit, local dans le navigateur, aucune installation)
2. **Commentaires personnalisés** : Les commentaires ajoutés manuellement dans `.txt` ne sont pas préservés (régénérés automatiquement à l'import)
3. **Ordre des clés** : L'ordre des clés peut changer lors de l'import (groupées par catégorie alphabétique)
4. **Métadonnées d'espacement** : Les espaces intentionnels (alignement dans le code Lua) ne sont pas préservés dans les fichiers `.txt` générés (normal, car ces métadonnées sont pour le code source uniquement)

---

## Dépannage

### Erreur : "Langue de référence 'en' manquante"

**Cause** : Le JSON importé ne contient pas la section `translations.en`

**Solution** : Assurez-vous que le fichier JSON contient bien la langue anglaise (référence obligatoire)

### Erreur : "Placeholders différents"

**Cause** : Les placeholders (`%s`, `\n`, etc.) ont été modifiés ou supprimés en traduction

**Solution** : Vérifiez et corrigez les traductions pour préserver les placeholders exacts de la version EN

### Avertissement : "X clés manquantes"

**Cause** : Certaines clés EN ne sont pas traduites dans une langue cible

**Solution** : Normal si traduction incomplète. Les clés manquantes utiliseront la valeur EN par défaut.

---

## Contribution

### Standards de code

- **Style** : Suivre le style des modules existants (`1_Extractor`, `3_Translation_manager`)
- **Docstrings** : Obligatoires pour toutes les fonctions publiques
- **Tests** : Coverage > 80% requis
- **Validation** : Linting avec `pylint` et `flake8`

### Avant de commit

```bash
# Tests
python -m pytest tests/ -v

# Linting
pylint 4_WebBridge/*.py
flake8 4_WebBridge/

# Test aller-retour critique
python -m pytest tests/test_roundtrip.py -v
```

---

## Ressources

### Documentation

- [Plan d'intégration complet](../../.claude/webbridge-mission.md)
- [Contexte technique détaillé](../../.claude/webbridge-context.md)
- [Skills WebBridge](../../.claude/webbridge-skills.md)
- [Historique du champ 'default'](../MODIFICATIONS_DEFAULT_FIELD.md)
- [Historique de l'option 'context'](../MODIFICATIONS_INCLUDE_CONTEXT.md)

### Outils externes

- [quicki18n.studio](https://www.quicki18n.studio/) - Éditeur i18n browser-based
- [i18next JSON format](https://www.i18next.com/misc/json-format) - Référence format i18n

### Fichiers de référence

- `1_Extractor/` - Parsing de fichiers, extraction de données
- `3_Translation_manager/` - Validation, comparaison
- `common/paths.py` - Gestion des chemins
- `common/colors.py` - Formatage console

---

## Licence

Partie du **Adobe Lightroom Translation Plugins Kit**

**Auteur** : Claude (Anthropic) pour Julien Moreau
**Date** : 2026-01-31
**Version** : 1.0
