# WebBridge - i18n Conversion Bridge for Lightroom Plugins

## Overview

The **WebBridge** module allows you to convert Lightroom localization files (proprietary `.txt` format) to a standard JSON i18n format, compatible with modern web tools like [quicki18n.studio](https://www.quicki18n.studio/).

### Problem Solved

Translators are not developers. Editing `TranslatedStrings_xx.txt` files directly is:
- Not user-friendly (proprietary format)
- Prone to formatting errors
- Without visual or contextual help
- Difficult to organize for multiple languages

### Solution Provided

WebBridge creates a **safe bidirectional bridge** between:
- **Lightroom SDK Format**: `TranslatedStrings_xx.txt` (ultimate source of truth)
- **i18n JSON Format**: Compatible with modern web tools (visual editing)

---

## Architecture

```
4_WebBridge/
├── __doc/                        # Documentation
│   ├── Lisez-moi.md             # French documentation
│   └── README.md                # English documentation
│
├── WebBridge_main.py             # Main interface (interactive menu)
├── WebBridge_export.py           # Export .txt → .json
├── WebBridge_import.py           # Import .json → .txt
├── WebBridge_models.py           # Data classes
├── WebBridge_utils.py            # Parsing utilities
└── WebBridge_validator.py        # Strict validation
```

---

## Complete Workflow

### 1. Developer: Extraction and Export

```bash
# 1. Extract strings from Lua code
python LocalizationToolkit.py
# Select [1] Extractor

# 2. Export to i18n JSON format
python LocalizationToolkit.py
# Select [8] Export Web
# → Generates i18n_translations.json

# 3. Send JSON file to translator
```

### 2. Translator: Visual Editing

```bash
# 1. Open https://www.quicki18n.studio/
# 2. Import i18n_translations.json
# 3. Translate missing keys visually
# 4. Export i18n_translations.json (modified)
# 5. Send file back to developer
```

### 3. Developer: Import and Apply

```bash
# 1. Import translated JSON
python LocalizationToolkit.py
# Select [9] Import Web
# → Auto-validation
# → Generates TranslatedStrings_fr.txt, TranslatedStrings_de.txt, etc.

# 2. Copy into plugin
# Generated files are ready for Lightroom

# 3. (Optional) Synchronize with TranslationManager
python LocalizationToolkit.py
# Select [3] Translation → SYNC
```

---

## JSON i18n Format

### Structure

```json
{
  "_meta": {
    "version": "1.0",
    "generated": "2026-01-31T10:30:00",
    "plugin_name": "myPlugin.lrplugin",
    "prefix": "$$$/MyPlugin",
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
          "default": "English text",
          "context": "FileName.lua:123"
        }
      }
    },
    "fr": {
      "Category1": {
        "Key1": {
          "text": "Texte français",
          "default": "English text",
          "context": "FileName.lua:123"
        }
      }
    }
  }
}
```

### Fields

- **`_meta`**: Version metadata and traceability
- **`translations`**: Translations by language
  - **Level 1**: Language code (ISO 639-1)
  - **Level 2**: Category (ex: API, Dialogs)
  - **Level 3**: Key
  - **Value**: Object with:
    - `text` (required): The translated text
    - `context` (present by default): Source code context (file:line) - can be disabled via option [4]
    - `default` (absent by default): Original string (EN) - can be enabled via option [5] for direct reference when editing
    - `metadata` (optional): Spacing metadata

### `default` Field (Reference String) - OPTIONAL

Optionally, you can include the `default` field containing the original EN string in each key (all languages). This facilitates translation and maintains quality:

```json
"en": {
  "API": {
    "AddTags": {
      "text": "to add tags",
      "default": "to add tags",  // ← Same value for EN (reference)
      "context": "PiwigoAPI.lua:123"
    }
  }
},
"fr": {
  "API": {
    "AddTags": {
      "text": "pour ajouter des tags",
      "default": "to add tags",  // ← EN reference visible when editing
      "context": "PiwigoAPI.lua:123"
    }
  }
}
```

**Benefits**:
- Translators see the original text directly when editing JSON
- No need to search in multiple files
- Easier translation consistency maintenance
- Direct comparison when editing manually
- For EN: provides visual JSON consistency

**When to Include?**
- ✓ Useful if translators manually edit the JSON and want to see the reference
- ✓ Helps with direct EN/translation comparison
- ✗ Adds file size to JSON (non-blocking)
- ✗ Not necessary if using only quicki18n.studio

**Configuration**:
- Interactive menu: Option **[5] Include 'default' field** in export mode
- CLI: Add `--include-default` flag to export
- Default: **Disabled** (for lighter JSON)

### Critical Metadata

Some strings have **intentional spaces or suffixes**:

```json
"metadata": {
  "suffix": " -",           // Suffix to reapply (ex: "Cannot log in to Piwigo -")
  "leading_spaces": 2,      // Spaces before text (alignment)
  "trailing_spaces": 1      // Spaces after text (concatenation)
}
```

**These metadata are automatically preserved** during export/import.

### Option: Include Context (file:line)

By default, the exported JSON includes **source context** (file:line) for each key:

```json
"CannotLogPiwigo": {
  "text": "Cannot log in to Piwigo",
  "context": "PiwigoAPI.lua:1352"  // ← Present by default
}
```

**When to Disable?**
- ✓ If you want lighter JSON (without source context)
- ✓ If translators use only quicki18n.studio
- ✗ Useful to keep if navigating Lua source code during translation
- ✗ Helps understand usage context

**Configuration**:
- Interactive menu: Option **[4] Include context** in export mode (disable if desired)
- CLI: Add `--no-context` flag to export
- Default: **Enabled** (inclusion of source context)

---

## Strict Validation

### On Export

- Verify presence of `TranslatedStrings_en.txt` (required)
- Detect spacing metadata
- Extract context if available

### On Import

**Critical validations (block import)**:
- Valid JSON structure (schema respected)
- Reference language `en` present
- **Identical placeholders** (`%s`, `%d`, `\n`, etc.)

**Non-blocking validations (warnings)**:
- Missing keys in target languages (→ will use EN value)
- Extra keys (→ ignored)

### Validation Report Example

```
═══════════════════════════════════════════════════════════
VALIDATION REPORT
═══════════════════════════════════════════════════════════

✓ Valid JSON structure
✓ Reference language (en) present
✓ 272 keys validated

[FR] Status:
  ✓ 270 keys translated
  ⚠ 2 missing keys (will use EN value)
  ✓ Placeholders preserved

[DE] Status:
  ✓ 272 keys translated
  ✓ Placeholders preserved

═══════════════════════════════════════════════════════════
NO CRITICAL ERRORS - Import authorized
═══════════════════════════════════════════════════════════
```

---

## Usage

### Interactive Mode (Recommended)

```bash
# From the main toolkit
python LocalizationToolkit.py

# Menu displayed:
# [8] Export Web     - Export for quicki18n.studio
# [9] Import Web     - Import from quicki18n.studio
```

### CLI Mode

```bash
# Export
python LocalizationToolkit.py web-export

# Import
python LocalizationToolkit.py web-import

# Validation only (without import)
python 4_WebBridge/WebBridge_import.py \
    --json-file "i18n_translations.json" \
    --plugin-path "D:/plugin.lrplugin" \
    --validate-only
```

### Direct Usage

```bash
# Export with options
python 4_WebBridge/WebBridge_export.py \
    --plugin-path "D:/plugin.lrplugin" \
    --extraction-dir "Extractor/20260130_223727" \
    --output "i18n_translations.json" \
    --languages en fr de \
    --include-context

# Import with options
python 4_WebBridge/WebBridge_import.py \
    --json-file "i18n_translations.json" \
    --plugin-path "D:/plugin.lrplugin" \
    --output-dir "__i18n_tmp__/WebBridge/20260131_143000"
```

---

## Testing

### Run Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific test
python -m pytest tests/test_export.py -v

# Critical roundtrip test
python -m pytest tests/test_roundtrip.py -v
```

### Roundtrip Test

The most important test verifies that **no data is lost**:

1. Load original `TranslatedStrings_en.txt`
2. Export → `i18n_translations.json`
3. Import → `TranslatedStrings_en_new.txt`
4. Compare original vs new (must be identical)

---

## Compatibility

### Supported Web Tools

- ✅ [quicki18n.studio](https://www.quicki18n.studio/) - Browser-based i18n editor, 100% local
- ⚠️ Other i18n tools (to be tested)

### Lightroom SDK

Compatible with all Adobe Lightroom Classic SDK versions using the `TranslatedStrings_xx.txt` format.

### Platforms

- ✅ Windows
- ✅ macOS
- ✅ Linux

---

## Data Security

### Absolute Rules

1. **Source of Truth**: `TranslatedStrings_xx.txt` files remain the only final source of truth
2. **No Loss**: JSON format is an **intermediate work format** only
3. **Strict Validation**: Placeholders, metadata, structure verified before any import
4. **Automatic Backups**: The Applicator always creates backups before modification

### Security Tests

- ✅ Roundtrip test (roundtrip) → No data loss
- ✅ Placeholder validation → Safe Lightroom runtime
- ✅ Metadata preservation → Correct formatting

---

## Known Limitations

1. **quicki18n.studio**: Manual validation required (test import/export on site)
2. **Comments**: Comments in `.txt` are not preserved (regenerated on import)
3. **Key Order**: Order may change (grouped by alphabetical category)
4. **Multiple Languages**: Translator must have access to all languages in JSON (or work language by language)

---

## Troubleshooting

### Error: "Reference language 'en' missing"

**Cause**: The imported JSON does not contain the `translations.en` section

**Solution**: Ensure the JSON file contains English language (required reference)

### Error: "Different placeholders"

**Cause**: The placeholders (`%s`, `\n`, etc.) were modified or removed in translation

**Solution**: Check and correct translations to preserve exact placeholders from EN version

### Warning: "X missing keys"

**Cause**: Some EN keys are not translated in a target language

**Solution**: Normal if translation is incomplete. Missing keys will use EN value by default.

---

## Contributing

### Code Standards

- **Style**: Follow the style of existing modules (`1_Extractor`, `3_Translation_manager`)
- **Docstrings**: Required for all public functions
- **Tests**: Coverage > 80% required
- **Validation**: Linting with `pylint` and `flake8`

### Before Committing

```bash
# Tests
python -m pytest tests/ -v

# Linting
pylint 4_WebBridge/*.py
flake8 4_WebBridge/

# Critical roundtrip test
python -m pytest tests/test_roundtrip.py -v
```

---

## Resources

### Documentation

- [Complete integration plan](../../.claude/webbridge-mission.md)
- [Detailed technical context](../../.claude/webbridge-context.md)
- [WebBridge Skills](../../.claude/webbridge-skills.md)
- [History: 'default' field](../MODIFICATIONS_DEFAULT_FIELD.md)
- [History: 'context' option](../MODIFICATIONS_INCLUDE_CONTEXT.md)

### External Tools

- [quicki18n.studio](https://www.quicki18n.studio/) - Browser-based i18n editor
- [i18next JSON format](https://www.i18next.com/misc/json-format) - i18n format reference

### Reference Files

- `1_Extractor/` - File parsing, data extraction
- `3_Translation_manager/` - Validation, comparison
- `common/paths.py` - Path management
- `common/colors.py` - Console formatting

---

## License

Part of the **Adobe Lightroom Translation Plugins Kit**

**Author**: Claude (Anthropic) for Julien Moreau
**Date**: 2026-01-31
**Version**: 1.0
