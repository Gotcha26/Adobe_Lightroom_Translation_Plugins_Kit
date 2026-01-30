# TranslationManager - Technical Documentation

**Version 5.0 | January 2026**

## Overview

TranslationManager is the third tool in the localization chain. Its role is to manage the evolution of translations over time: compare different versions, isolate new keys to translate, inject translations, and synchronize all language files.

## Project Architecture

```
3_Translation_manager/
├── TranslationManager.py     ← Entry point (menu + CLI)
├── TM_common.py             ← Common functions (parser, utils, UI)
├── TM_compare.py            ← COMPARE command (diff between 2 EN versions)
├── TM_extract.py            ← EXTRACT command (generates TRANSLATE_xx.txt)
├── TM_inject.py             ← INJECT command (reinjects translations)
├── TM_sync.py               ← SYNC command (synchronizes languages)
└── __doc/
    └── README.md            ← This file
```

The architecture is modular with one command per module. Each command can be used independently or via the interactive menu.

## The 4 Commands

TranslationManager offers 4 main commands that form a complete workflow.

### 1. COMPARE - Change Detection

Compares two versions of the English file (`TranslatedStrings_en.txt`) and generates an update file.

```
Old EN          New EN
(v1.0)             (v1.1)
    │                  │
    └─────────┬────────┘
              ▼
         COMPARE
              │
              ├── UPDATE_en.json
              │   ├── added: [...]      ← New keys
              │   ├── changed: [...]    ← Modified keys
              │   ├── deleted: [...]    ← Deleted keys
              │   └── unchanged: [...]  ← Identical keys
              │
              └── CHANGELOG.txt
                  ├── Statistical summary
                  ├── Details of additions
                  ├── Details of modifications
                  └── Details of deletions
```

**Generated files:**

- **UPDATE_en.json**: Structured file with all differences
- **CHANGELOG.txt**: Human-readable report

### 2. EXTRACT - Isolate New Keys

Generates small files containing only the keys to translate (new or modified).

```
UPDATE_en.json
    │
    ├── added: 15 keys
    ├── changed: 5 keys
    │
    └────────┬──────────────────────────────────┐
             ▼                                  ▼
     TRANSLATE_fr.txt                  TRANSLATE_de.txt
     ├── [NEW] Key1=                   ├── [NEW] Key1=
     ├── [NEW] Key2=                   ├── [NEW] Key2=
     ├── [NEEDS_REVIEW] Key3=...       ├── [NEEDS_REVIEW] Key3=...
     └── ...                           └── ...
```

**Advantages:**
- Lightweight files (a few KB vs several MB)
- Easy to send to translators
- Focus only on new content

### 3. INJECT - Merge Translations

Reinjects translations from `TRANSLATE_xx.txt` files into the complete `TranslatedStrings_xx.txt` files.

```
TRANSLATE_fr.txt              TranslatedStrings_fr.txt
(new translations)            (complete file)
    │                              │
    ├── Key1=Bonjour               ├── Key0=Old text
    ├── Key2=Monde                 ├── ...
    └── Key3=(empty)               └── ...
          │                              │
          └──────────┬───────────────────┘
                     ▼
                  INJECT
                     │
                     ├── Translated key → uses translation
                     ├── Empty key → uses default EN value
                     └── Missing key → remains unchanged
                     │
                     ▼
          TranslatedStrings_fr.txt (updated)
          ├── Key0=Old text
          ├── Key1=Bonjour          ← Added
          ├── Key2=Monde            ← Added
          ├── Key3=Default EN       ← EN fallback
          └── ...
```

**Fallback mechanism:**
If a key is empty in `TRANSLATE_xx.txt`, INJECT uses the default English value from `UPDATE_en.json`. This ensures no text is lost.

### 4. SYNC - Final Synchronization

Synchronizes all language files with the reference English version.

```
UPDATE_en.json              TranslatedStrings_fr.txt
TranslatedStrings_en.txt    TranslatedStrings_de.txt
(reference)                 (foreign languages)
    │                            │
    └──────────┬─────────────────┘
               ▼
             SYNC
               │
               ├── Adds [NEW] for new keys
               ├── Marks [NEEDS_REVIEW] for modified keys
               ├── Removes obsolete keys
               └── Preserves existing translations
               │
               ▼
    TranslatedStrings_fr.txt (synchronized)
    ├── "$$$/App/NewKey=[NEW]"
    ├── "$$$/App/Changed=[NEEDS_REVIEW] Old Translation"
    ├── "$$$/App/Existing=Existing translation"
    └── (obsolete key removed)
```

**Markers added:**
- `[NEW]`: New key, not yet translated
- `[NEEDS_REVIEW]`: English value modified, review translation

## Complete Workflow

Here is the typical workflow when updating a plugin:

```
┌─────────────────────────────────────────────────────────┐
│ Step 1: Development                                     │
│ - Add new features to the plugin                       │
│ - Modify existing text                                 │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 2: Extraction (Extractor)                         │
│ - Run Extractor on modified code                       │
│ - Generate new TranslatedStrings_en.txt                │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 3: Comparison (TranslationManager COMPARE)        │
│ - Compare old vs new EN                                │
│ - Generate UPDATE_en.json + CHANGELOG.txt              │
│ - Result: 10 new keys, 3 modified, 2 deleted           │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 4: Targeted Extraction (EXTRACT)                  │
│ - Generate TRANSLATE_fr.txt (13 keys to translate)     │
│ - Generate TRANSLATE_de.txt (13 keys to translate)     │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 5: Translation                                     │
│ - Send TRANSLATE_xx.txt files to translators           │
│ - Or manual translation                                │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 6: Injection (INJECT)                             │
│ - Reinject translations into complete files            │
│ - EN fallback for untranslated keys                    │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 7: Synchronization (SYNC)                         │
│ - Add [NEW] and [NEEDS_REVIEW]                         │
│ - Remove obsolete keys                                 │
│ - Finalize all language files                          │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Step 8: Testing                                         │
│ - Restart Lightroom                                    │
│ - Verify translations in the interface                 │
└─────────────────────────────────────────────────────────┘
```

## Configuration Options

### Interactive Mode

Launch `TranslationManager.py` to access the menu:

```
==================================================
     TRANSLATION MANAGER v5.0
==================================================

Options:
  1. COMPARE
     Compare old EN vs new EN
     → Generates UPDATE_en.json + CHANGELOG.txt

  2. EXTRACT (optional)
     Generate mini TRANSLATE_xx.txt files for translation

  3. INJECT (optional)
     Reinject translations (EN default if empty)

  4. SYNC
     Update languages with EN
     → Add [NEW], mark [NEEDS_REVIEW], remove obsolete

  5. Help

  0. Quit
```

### CLI Mode

Each command can be launched independently:

**COMPARE:**
```bash
python TranslationManager.py compare \
  --old old_en.txt \
  --new new_en.txt \
  --plugin-path ./plugin.lrplugin
```

**EXTRACT:**
```bash
python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

**INJECT:**
```bash
python TranslationManager.py inject \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

**SYNC:**
```bash
python TranslationManager.py sync \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

### Detailed Options

#### COMPARE Command

| Option | Description | Required | Example |
|--------|-------------|--------|---------|
| `--old` | Old EN file | Yes | `./v1/TranslatedStrings_en.txt` |
| `--new` | New EN file | Yes | `./v2/TranslatedStrings_en.txt` |
| `--plugin-path` | Plugin path (output in `__i18n_tmp__/`) | No | `./plugin.lrplugin` |
| `--output` | Custom output directory | No | `./output` |

#### EXTRACT Command

| Option | Description | Required | Example |
|--------|-------------|--------|---------|
| `--update` | UPDATE folder (or auto-detection if `--plugin-path`) | No* | `./20260129_143000` |
| `--plugin-path` | Plugin path (auto-detection in `__i18n_tmp__/`) | No* | `./plugin.lrplugin` |
| `--locales` | Directory of existing translations | No | `./plugin.lrplugin` |
| `--lang` | Specific language to extract | No | `fr`, `de`, `es` |
| `--output` | Custom output directory | No | `./output` |

\* At least one of these options is required

#### INJECT Command

| Option | Description | Required | Example |
|--------|-------------|--------|---------|
| `--translate` | Individual TRANSLATE_xx.txt file | No* | `./TRANSLATE_fr.txt` |
| `--target` | Target TranslatedStrings_xx.txt file | No* | `./TranslatedStrings_fr.txt` |
| `--translate-dir` | Folder containing multiple TRANSLATE_*.txt | No* | `./translations/` |
| `--plugin-path` | Plugin path (auto-detection) | No* | `./plugin.lrplugin` |
| `--locales` | Language files folder | No* | `./plugin.lrplugin` |
| `--update` | UPDATE folder (EN fallback values) | No | `./20260129_143000` |

\* Specify either (`--translate` + `--target`) OR (`--translate-dir` + `--locales`) OR (`--plugin-path` + `--locales`)

#### SYNC Command

| Option | Description | Required | Example |
|--------|-------------|--------|---------|
| `--ref` | Reference EN file | No* | `./TranslatedStrings_en.txt` |
| `--plugin-path` | Plugin path (auto-detection) | No* | `./plugin.lrplugin` |
| `--locales` | Language files directory | Yes | `./plugin.lrplugin` |
| `--update` | UPDATE folder (with UPDATE_en.json) | No | `./20260129_143000` |

\* At least one of these options is required

## Usage Examples

### Complete Workflow with --plugin-path

```bash
# 1. Compare two versions
python TranslationManager.py compare \
  --old ./backup/TranslatedStrings_en.txt \
  --new ./plugin.lrplugin/__i18n_tmp__/Extractor/20260129_143022/TranslatedStrings_en.txt \
  --plugin-path ./plugin.lrplugin

# 2. Extract keys to translate (auto-detection of UPDATE_en.json)
python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin

# 3. Manually translate the TRANSLATE_xx.txt files
# (edit in your favorite editor)

# 4. Inject translations (auto-detection)
python TranslationManager.py inject \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin

# 5. Synchronize all language files
python TranslationManager.py sync \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

### Extraction and Injection for a Single Language

```bash
# Extract only for French
python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin \
  --lang fr

# Inject only French
python TranslationManager.py inject \
  --translate ./plugin.lrplugin/__i18n_tmp__/3_TranslationManager/<timestamp>/TRANSLATE_fr.txt \
  --target ./plugin.lrplugin/TranslatedStrings_fr.txt \
  --update ./plugin.lrplugin/__i18n_tmp__/3_TranslationManager/<timestamp>/
```

### Legacy Mode (without --plugin-path)

```bash
# Compare with manual output
python TranslationManager.py compare \
  --old ./v1/en.txt \
  --new ./v2/en.txt \
  --output ./comparison_output/

# Extract from a specific UPDATE folder
python TranslationManager.py extract \
  --update ./comparison_output/20260129_143000/ \
  --locales ./plugin.lrplugin/

# Inject from a specific TRANSLATE folder
python TranslationManager.py inject \
  --translate-dir ./comparison_output/20260129_143000/ \
  --locales ./plugin.lrplugin/ \
  --update ./comparison_output/20260129_143000/

# Synchronize
python TranslationManager.py sync \
  --update ./comparison_output/20260129_143000/ \
  --locales ./plugin.lrplugin/
```

## Generated File Structure

### UPDATE_en.json

Structured JSON file containing all differences:

```json
{
  "metadata": {
    "old_file": "./v1/TranslatedStrings_en.txt",
    "new_file": "./v2/TranslatedStrings_en.txt",
    "timestamp": "2026-01-29 14:30:00",
    "total_keys_old": 120,
    "total_keys_new": 133
  },
  "summary": {
    "added": 15,
    "changed": 5,
    "deleted": 2,
    "unchanged": 113
  },
  "added": {
    "$$$/Piwigo/NewFeature_Title": "New Feature Title",
    "$$$/Piwigo/NewFeature_Description": "Description of the new feature",
    ...
  },
  "changed": {
    "$$$/Piwigo/Upload_Status": {
      "old": "Uploading...",
      "new": "Upload in progress..."
    },
    ...
  },
  "deleted": {
    "$$$/Piwigo/OldFeature_Title": "Old Feature Title",
    ...
  },
  "unchanged": {
    "$$$/Piwigo/Submit": "Submit",
    "$$$/Piwigo/Cancel": "Cancel",
    ...
  }
}
```

### CHANGELOG.txt

Human-readable report:

```
================================================================================
CHANGELOG - Translation Comparison
================================================================================

Old file: ./v1/TranslatedStrings_en.txt (120 keys)
New file: ./v2/TranslatedStrings_en.txt (133 keys)
Date: 2026-01-29 14:30:00

================================================================================
SUMMARY
================================================================================

Added keys      : 15
Modified keys   : 5
Deleted keys    : 2
Unchanged keys  : 113

================================================================================
ADDED KEYS (15)
================================================================================

"$$$/Piwigo/NewFeature_Title"
  → "New Feature Title"

"$$$/Piwigo/NewFeature_Description"
  → "Description of the new feature"

...

================================================================================
MODIFIED KEYS (5)
================================================================================

"$$$/Piwigo/Upload_Status"
  OLD: "Uploading..."
  NEW: "Upload in progress..."

...

================================================================================
DELETED KEYS (2)
================================================================================

"$$$/Piwigo/OldFeature_Title"
  ← "Old Feature Title"

...
```

### TRANSLATE_xx.txt

Lightweight files for translation:

```
# Translation file for: fr
# Generated on: 2026-01-29 14:35:00
#
# Instructions:
# - Translate values after the = sign
# - [NEW] = New key
# - [NEEDS_REVIEW] = English value modified, review translation
# - Leave empty to use default English value

"$$$/Piwigo/NewFeature_Title=[NEW]"
"$$$/Piwigo/NewFeature_Description=[NEW]"
"$$$/Piwigo/Upload_Status=[NEEDS_REVIEW] Téléchargement..."
```

After translation:

```
"$$$/Piwigo/NewFeature_Title=Nouvelle fonctionnalité"
"$$$/Piwigo/NewFeature_Description=Description de la nouvelle fonctionnalité"
"$$$/Piwigo/Upload_Status=Téléchargement en cours..."
```

## Marker Management

### [NEW] Marker

Indicates a completely new key, absent from the previous version.

```
# Before translation
"$$$/App/NewKey=[NEW]"

# After translation
"$$$/App/NewKey=My translation"

# Untranslated (EN fallback via INJECT)
"$$$/App/NewKey=Default English Value"
```

### [NEEDS_REVIEW] Marker

Indicates that the English value has changed and the translation should be reviewed.

```
# Old EN value: "Uploading..."
# New EN value: "Upload in progress..."

# In TRANSLATE_fr.txt
"$$$/App/Upload=[NEEDS_REVIEW] Téléchargement..."

# After review
"$$$/App/Upload=Téléchargement en cours..."
```

The `[NEEDS_REVIEW]` marker is followed by the old translation to facilitate updating.

## Advanced Use Cases

### Comparing Two Extractor Extractions

Compare two Extractor runs to see what changed in the code:

```bash
python TranslationManager.py compare \
  --old ./plugin/__i18n_tmp__/Extractor/20260120_100000/TranslatedStrings_en.txt \
  --new ./plugin/__i18n_tmp__/Extractor/20260129_143022/TranslatedStrings_en.txt \
  --plugin-path ./plugin.lrplugin
```

### Selective Extraction by Language

If you only manage a few languages:

```bash
# Extract only French and German
python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin \
  --lang fr

python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin \
  --lang de
```

### Injection Without Translation (EN Fallback)

If you want to add new keys with default English values:

```bash
# Don't translate TRANSLATE_xx.txt files, leave them empty
# Then inject: EN values will be used

python TranslationManager.py inject \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

This adds new keys in English, which is better than missing text.

### Synchronization After Manual Editing

If you directly edited `TranslatedStrings_xx.txt`:

```bash
# Synchronize to add [NEW] and [NEEDS_REVIEW] markers
python TranslationManager.py sync \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

SYNC will detect missing keys and add them with `[NEW]`.

### Workflow Without EXTRACT/INJECT (Direct Editing)

If you prefer to directly edit complete files:

```bash
# 1. Compare
python TranslationManager.py compare \
  --old old_en.txt \
  --new new_en.txt \
  --plugin-path ./plugin.lrplugin

# 2. Consult CHANGELOG.txt to know what to translate
cat ./plugin/__i18n_tmp__/3_TranslationManager/<timestamp>/CHANGELOG.txt

# 3. Manually edit TranslatedStrings_fr.txt, TranslatedStrings_de.txt, etc.
# (add new keys, update modified ones)

# 4. Synchronize to clean up and finalize
python TranslationManager.py sync \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

## Troubleshooting

### Error: "No TranslationManager folder found"

**Cause:** No `__i18n_tmp__/3_TranslationManager/` folder with `UPDATE_en.json`.

**Solution:**
```bash
# First run COMPARE
python TranslationManager.py compare \
  --old old.txt \
  --new new.txt \
  --plugin-path ./plugin.lrplugin
```

### EXTRACT Generates No Files

**Possible causes:**
1. No foreign languages detected in `--locales`
2. No differences in `UPDATE_en.json` (nothing to translate)
3. The `--locales` folder doesn't contain `TranslatedStrings_xx.txt`

**Solutions:**
```bash
# Check language files
ls ./plugin.lrplugin/TranslatedStrings_*.txt

# Check UPDATE_en.json
cat ./plugin/__i18n_tmp__/3_TranslationManager/<timestamp>/UPDATE_en.json
```

### INJECT Adds Nothing

**Possible causes:**
1. The `TRANSLATE_xx.txt` files are empty
2. Keys already exist in `TranslatedStrings_xx.txt`
3. The `--update` folder is incorrect (EN values not found)

**Solutions:**
```bash
# Check TRANSLATE_fr.txt
cat ./plugin/__i18n_tmp__/3_TranslationManager/<timestamp>/TRANSLATE_fr.txt

# Check UPDATE_en.json
cat ./plugin/__i18n_tmp__/3_TranslationManager/<timestamp>/UPDATE_en.json
```

### SYNC Removes Translations

SYNC only removes obsolete keys (present in "deleted" of `UPDATE_en.json`). This is normal.

If you want to keep them:

1. Edit `UPDATE_en.json` and remove keys from "deleted"
2. Re-run SYNC

### Incorrect Encoding

All files are in UTF-8. If you see incorrectly encoded characters:

```bash
# Check encoding
file --mime-encoding TranslatedStrings_fr.txt

# Convert if necessary
iconv -f ISO-8859-1 -t UTF-8 TranslatedStrings_fr.txt > TranslatedStrings_fr_utf8.txt
```

## Technical FAQ

### Can I Use EXTRACT Without COMPARE?

No, EXTRACT needs `UPDATE_en.json` generated by COMPARE to know which keys to extract.

### Can I Skip INJECT and Directly Edit Files?

Yes, it's possible. INJECT is a convenience to easily merge small `TRANSLATE_xx.txt` files into complete files.

### Is SYNC Mandatory?

No, but it's strongly recommended. SYNC cleans up files (removes obsolete keys) and adds `[NEW]` and `[NEEDS_REVIEW]` markers to facilitate future reviews.

### What Happens If I Don't Translate a Key?

INJECT will use the default English value from `UPDATE_en.json`. The user will see English text instead of empty text or a raw key.

### Can I Reuse an Old UPDATE_en.json?

Yes, as long as it corresponds to the files you want to synchronize. But it's better to do a new COMPARE with current versions.

### How to Manage Multiple Git Branches?

```bash
# Dev branch
git checkout dev
python TranslationManager.py compare --old main_en.txt --new dev_en.txt --output ./dev_update/

# Feature branch
git checkout feature
python TranslationManager.py compare --old main_en.txt --new feature_en.txt --output ./feature_update/
```

Each branch can have its own update folder.

## Performance

### Typical Execution Times

- **COMPARE** (120 vs 133 keys): < 1 second
- **EXTRACT** (3 languages, 15 keys): < 1 second
- **INJECT** (3 languages, 15 keys): < 1 second
- **SYNC** (3 languages, 133 keys): 1-2 seconds

TranslationManager is very fast because it only manipulates text files.

### Possible Optimizations

If you have many languages (10+) or keys (1000+):

1. Use EXTRACT with `--lang` to process one language at a time
2. Run commands outside active development hours
3. Exclude unmaintained languages from `--locales`

## Integration into an Automated Workflow

### Complete Bash Script

```bash
#!/bin/bash
# update_translations.sh

PLUGIN_PATH="./plugin.lrplugin"
OLD_EN="./backup/TranslatedStrings_en.txt"
NEW_EN="$PLUGIN_PATH/__i18n_tmp__/Extractor/latest/TranslatedStrings_en.txt"

echo "=== Step 1: Comparison ==="
python TranslationManager.py compare \
  --old "$OLD_EN" \
  --new "$NEW_EN" \
  --plugin-path "$PLUGIN_PATH"

if [ $? -ne 0 ]; then
  echo "Error during comparison"
  exit 1
fi

echo ""
echo "=== Step 2: Extraction ==="
python TranslationManager.py extract \
  --plugin-path "$PLUGIN_PATH" \
  --locales "$PLUGIN_PATH"

echo ""
echo "=== Step 3: Translation ==="
echo "Please translate TRANSLATE_xx.txt files in:"
echo "$PLUGIN_PATH/__i18n_tmp__/3_TranslationManager/<timestamp>/"
read -p "Press Enter when translations are ready..."

echo ""
echo "=== Step 4: Injection ==="
python TranslationManager.py inject \
  --plugin-path "$PLUGIN_PATH" \
  --locales "$PLUGIN_PATH"

echo ""
echo "=== Step 5: Synchronization ==="
python TranslationManager.py sync \
  --plugin-path "$PLUGIN_PATH" \
  --locales "$PLUGIN_PATH"

echo ""
echo "✓ Translations successfully updated"
echo "  Restart Lightroom to test"
```

### Python Script with API

```python
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run_tm_command(command, args):
    """Execute a TranslationManager command."""
    cmd = [sys.executable, "TranslationManager.py", command] + args
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False

    print(result.stdout)
    return True

def main():
    plugin_path = "./plugin.lrplugin"
    old_en = "./backup/TranslatedStrings_en.txt"
    new_en = f"{plugin_path}/__i18n_tmp__/Extractor/latest/TranslatedStrings_en.txt"

    # 1. COMPARE
    print("=== Comparison ===")
    if not run_tm_command("compare", [
        "--old", old_en,
        "--new", new_en,
        "--plugin-path", plugin_path
    ]):
        return 1

    # 2. EXTRACT
    print("\n=== Extraction ===")
    if not run_tm_command("extract", [
        "--plugin-path", plugin_path,
        "--locales", plugin_path
    ]):
        return 1

    # 3. Wait for translation (interactive or automated)
    input("\nTranslate TRANSLATE_xx.txt files then press Enter...")

    # 4. INJECT
    print("\n=== Injection ===")
    if not run_tm_command("inject", [
        "--plugin-path", plugin_path,
        "--locales", plugin_path
    ]):
        return 1

    # 5. SYNC
    print("\n=== Synchronization ===")
    if not run_tm_command("sync", [
        "--plugin-path", plugin_path,
        "--locales", plugin_path
    ]):
        return 1

    print("\n✓ Translations successfully updated")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Translation Update Checklist

- [ ] Backup old `TranslatedStrings_en.txt`
- [ ] Run Extractor on modified code
- [ ] Run COMPARE (old vs new EN)
- [ ] Consult `CHANGELOG.txt` to understand changes
- [ ] Run EXTRACT to generate `TRANSLATE_xx.txt`
- [ ] Translate `TRANSLATE_xx.txt` files
- [ ] Run INJECT to merge translations
- [ ] Run SYNC to finalize and clean up
- [ ] Verify `TranslatedStrings_xx.txt` files
- [ ] Commit changes to Git
- [ ] Restart Lightroom and test
- [ ] Delete `__i18n_tmp__/` if desired (cleanup)

## Additional Resources

- **Lightroom SDK**: [Adobe Developer Console](https://developer.adobe.com/console)
- **Translation file format**: Simple text format `"Key=Value"`
- **Python JSON**: [json documentation](https://docs.python.org/3/library/json.html)
- **Python difflib**: Used internally to compare files

## Contributions

To improve TranslationManager, you can:
- Add new output formats (CSV, XLSX, etc.)
- Improve change detection (fuzzy matching)
- Add a graphical interface
- Support new marker types

Feel free to propose your modifications!

---

**Developed by Julien MOREAU with the help of Claude (Anthropic)**

For any questions or issues, consult the main README or open an issue on the GitHub repository.
