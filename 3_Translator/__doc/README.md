# Translator - Technical Documentation

**Version 7.0 | January 2026**

## Overview

Translator is the third tool in the localization chain. Its role is to manage translation evolution over time.

**New in v7.0**: Added INSTALL and AUTO-SYNC to drastically simplify daily workflow.

## Project Architecture

```
3_Translator/
├── Translator_main.py     ← Entry point (menu + CLI)
├── TM_common.py             ← Common functions (parser, utils, UI)
├── TM_install.py            ← INSTALL command (new v7.0)
├── TM_autosync.py           ← AUTO-SYNC command (new v7.0) ⭐
├── TM_compare.py            ← COMPARE command (diff between 2 EN versions)
├── TM_extract.py            ← EXTRACT command (generates TRANSLATE_xx.txt)
├── TM_inject.py             ← INJECT command (reinjects translations)
├── TM_sync.py               ← SYNC command (synchronizes languages)
└── __doc/
    ├── Lisez-moi.md         ← French version
    └── README.md            ← This file
```

Modular architecture with one command per module. Each command can be used independently or via the interactive menu.

---

## 🎯 Main Commands (Recommended)

### 1. INSTALL - Initial Installation

**Use case**: First installation of translation files in the plugin.

Copies `TranslatedStrings_xx.txt` files from the latest Extractor output to the plugin root.

```
Extractor output:
  __i18n_tmp__/1_Extractor/20260131_120000/
    └── TranslatedStrings_en.txt

          │
          ▼
       INSTALL
          │
          ▼

Plugin root:
  plugin.lrplugin/
    └── TranslatedStrings_en.txt  ← Copied here
```

**Files installed**:
- `TranslatedStrings_en.txt` (English reference)
- Other language files if present in extraction

**When to use**:
- ✅ First initialization of multilingual plugin
- ⚠️ Files already exist? Use AUTO-SYNC instead

**CLI command**:
```bash
python Translator_main.py install --plugin-path ./plugin.lrplugin
```

---

### 2. AUTO-SYNC - Automatic Synchronization ⭐

**Use case**: Regular maintenance after code modifications.

**This is the command to use 99% of the time!**

Automatically detects the latest extraction and synchronizes all existing language files.

```
Latest extraction detected:
  __i18n_tmp__/1_Extractor/20260131_150000/
    └── TranslatedStrings_en.txt (new version)

          │
          ▼
      AUTO-SYNC ⭐
          │
          ├─→ Syncs TranslatedStrings_fr.txt
          ├─→ Syncs TranslatedStrings_de.txt
          └─→ Syncs TranslatedStrings_es.txt
          │
          ▼

Output:
  __i18n_tmp__/3_Translator/20260131_151000/
    ├── TranslatedStrings_fr.txt  ← Synchronized (new keys added)
    ├── TranslatedStrings_de.txt  ← Synchronized (new keys added)
    └── TranslatedStrings_es.txt  ← Synchronized (new keys added)
```

**What AUTO-SYNC does**:
1. Detects the latest Extractor output
2. Finds all existing `TranslatedStrings_xx.txt` files in the plugin
3. For each language file:
   - Adds new keys with EN default value
   - Updates existing keys (preserves translations)
   - Removes obsolete keys
   - Preserves all existing translations
4. Generates synchronized files in `__i18n_tmp__/3_Translator/`

**Note**: AUTO-SYNC does NOT generate markers. It's a simple workflow for daily maintenance.

**Markers (COMPARE workflow only)**:
- `-- [NEW]`: New key, not yet translated
- `-- [NEEDS_REVIEW]`: English value modified, review translation

**IMPORTANT**: AUTO-SYNC does NOT generate these markers. They are reserved for the advanced COMPARE → SYNC workflow.

**When to use**:
- ✅ After adding new features to the code
- ✅ After modifying existing texts
- ✅ To synchronize all language files at once

**Advantages**:
- ⚡ Ultra fast: Single command
- 🎯 Automatic: Detects everything
- 🔒 Safe: Preserves existing translations
- 📊 Report: Displays summary of changes

**CLI command**:
```bash
python Translator_main.py autosync --plugin-path ./plugin.lrplugin
```

**Example output**:
```
► Language: fr
  ✓ 15 added, 3 modified, 2 deleted

► Language: de
  ✓ 15 added, 3 modified, 2 deleted

✓ 2 file(s) synchronized
```

---

## 🔧 Advanced Commands (Specific Usage)

These commands are kept for advanced use cases but are generally not needed with AUTO-SYNC.

### 3. COMPARE - Change Detection

Compares two versions of the English file (`TranslatedStrings_en.txt`) and generates an update file.

```
Old EN            New EN
(v1.0)            (v1.1)
    │                 │
    └────────┬────────┘
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
                 ├── Addition details
                 ├── Modification details
                 └── Deletion details
```

**Generated files**:
- **UPDATE_en.json**: Structured file with all differences
- **CHANGELOG.txt**: Human-readable report

**When to use**:
- ⚠️ Advanced workflow with EXTRACT/INJECT
- ⚠️ Need for detailed changelog

**Note**: AUTO-SYNC makes this command optional in most cases.

---

### 4. EXTRACT - Key Isolation

Generates small files containing only keys to translate (new or modified).

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

**Advantages**:
- Lightweight files (few KB vs several MB)
- Easy to send to translators
- Focus only on new content

**When to use**:
- ⚠️ Advanced workflow with external translators without GitHub
- ⚠️ Need for partial files

**Note**: AUTO-SYNC makes this command optional for GitHub workflows.

---

### 5. INJECT - Translation Merge

Reinjects translations from `TRANSLATE_xx.txt` files into complete `TranslatedStrings_xx.txt` files.

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
                     ├── Empty key → uses EN default value
                     └── Missing key → stays unchanged
                     │
                     ▼
          TranslatedStrings_fr.txt (updated)
          ├── Key0=Old text
          ├── Key1=Bonjour          ← Added
          ├── Key2=Monde            ← Added
          ├── Key3=Default EN       ← EN fallback
          └── ...
```

**Fallback mechanism**:
If a key is empty in `TRANSLATE_xx.txt`, INJECT uses the default English value from `UPDATE_en.json`.

**When to use**:
- ⚠️ Advanced workflow with EXTRACT
- ⚠️ Translators working on partial files

**Note**: AUTO-SYNC makes this command optional.

---

### 6. SYNC - Manual Synchronization

Synchronizes a language file with the English reference version.

```
UPDATE_en.json              TranslatedStrings_fr.txt
TranslatedStrings_en.txt    (foreign language)
(reference)
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
    ├── -- [NEW] To translate
    ├── "$$$/App/NewKey=New Key"
    ├── -- [NEEDS_REVIEW] English text was modified
    ├── "$$$/App/Changed=Old Translation"
    ├── "$$$/App/Existing=Traduction existante"
    └── (obsolete key removed)
```

**Markers (COMPARE workflow only)**:
- `-- [NEW]`: New key, not yet translated
- `-- [NEEDS_REVIEW]`: English value modified, review translation

**IMPORTANT**: AUTO-SYNC does NOT generate these markers. They are reserved for the advanced COMPARE → SYNC workflow.

**When to use**:
- ⚠️ Synchronize ONE language file manually
- ⚠️ Advanced workflow with fine control

**Note**: AUTO-SYNC does the same but for ALL files at once.

---

## 🚀 Recommended Workflows

### Workflow 1: Initialization (First Time)

**Situation**: Plugin never localized, first installation.

```bash
# 1. Extract strings from code
[Option 1] Extractor

# 2. Install translation files
[Option 3] Translation Manager → [1] INSTALL

# 3. Apply to code
[Option 2] Applicator

# 4. Test in Lightroom
```

**Duration**: 15-30 minutes

---

### Workflow 2: Maintenance (Daily) ⭐

**Situation**: Plugin already localized, new features added.

```bash
# 1. Develop normally

# 2. Extract new strings
[Option 1] Extractor

# 3. AUTOMATICALLY synchronize all files
[Option 3] Translation Manager → [2] AUTO-SYNC

# 4. Copy to plugin
cp __i18n_tmp__/3_Translator/<timestamp>/TranslatedStrings_*.txt ./plugin.lrplugin/

# 5. Commit to GitHub
git add .
git commit -m "i18n: Add new translation keys"
git push
```

**Duration**: 5 minutes

**This is the workflow to use 99% of the time!**

---

### Workflow 3: Advanced (Specific Cases)

**Situation**: Established workflow with COMPARE/EXTRACT/INJECT.

```bash
# 1. Extract
[Option 1] Extractor

# 2. Compare
[Option 3] Translation Manager → [3] COMPARE

# 3. Extract partial keys
[4] EXTRACT

# 4. Send TRANSLATE_xx.txt to translators

# 5. Receive translations

# 6. Inject
[5] INJECT

# 7. Finalize
[6] SYNC
```

**Duration**: 15-30 minutes

**Note**: This workflow is kept for compatibility but AUTO-SYNC replaces it in most cases.

---

## 📊 Workflow Comparison

| Criteria | AUTO-SYNC ⭐ | COMPARE+EXTRACT+INJECT+SYNC |
|----------|-------------|----------------------------|
| **Steps** | 1 command | 4 commands |
| **Automatic detection** | ✅ Yes | ❌ No (manual) |
| **Intermediate files** | ❌ No | ✅ TRANSLATE_xx.txt |
| **Complexity** | ✅ Simple | ⚠️ Complex |
| **Duration** | 1 minute | 10-15 minutes |
| **Use case** | 99% of cases | Established workflows |

---

## 🎓 Generated File Format

### TranslatedStrings_xx.txt (synchronized)

```
"$$$/Prefix/Category/Key=Default value"
-- [NEW] To translate
"$$$/Prefix/Category/NewKey=New value"
-- [NEEDS_REVIEW] English text was modified
"$$$/Prefix/Category/ModifiedKey=Old translation"
```

**Structure**:
- Existing keys: Preserved as is
- New keys: `-- [NEW]` marker at line start
- Modified keys: `-- [NEEDS_REVIEW]` marker at line start
- Obsolete keys: Automatically removed

**New format advantages**:
- Markers are OUTSIDE the translation string
- Visually clean even in production
- Easy to spot for translators
- Don't pollute Lightroom display

### UPDATE_en.json (COMPARE)

```json
{
  "metadata": {
    "timestamp": "20260131_151000",
    "old_file": "TranslatedStrings_en_v1.txt",
    "new_file": "TranslatedStrings_en_v2.txt"
  },
  "added": [
    {"key": "$$$/App/NewFeature", "value": "New feature text"}
  ],
  "changed": [
    {
      "key": "$$$/App/Modified",
      "old_value": "Old text",
      "new_value": "New text"
    }
  ],
  "deleted": [
    {"key": "$$$/App/Obsolete", "value": "Removed feature"}
  ],
  "unchanged": [...]
}
```

### TRANSLATE_xx.txt (EXTRACT)

```
"$$$/Prefix/NewKey1=[NEW] "
"$$$/Prefix/NewKey2=[NEW] "
"$$$/Prefix/ModifiedKey=[NEEDS_REVIEW] Old translation here"
```

Lightweight files containing only keys to translate.

---

## ⚙️ Configuration

Translator uses the `__i18n_tmp__` structure automatically if the plugin is configured.

**Default paths**:
```
plugin.lrplugin/
└── __i18n_tmp__/
    ├── 1_Extractor/          ← Source of TranslatedStrings_en.txt
    └── 3_Translator/ ← Output INSTALL/AUTO-SYNC/SYNC
```

---

## 💡 Usage Tips

### For Developers

1. **Use AUTO-SYNC** for 99% of cases
2. **INSTALL** only for first initialization
3. **Advanced tools** only if established workflow
4. **Commit to GitHub** to enable Pull Requests

### For Translators

1. Search for `[NEW]` and `[NEEDS_REVIEW]` markers
2. Translate values
3. Remove markers after translation
4. Create a Pull Request on GitHub

---

## ❓ FAQ

### When to use AUTO-SYNC vs SYNC?

**AUTO-SYNC**:
- Synchronizes ALL language files at once
- Automatically detects latest extraction
- Recommended for daily maintenance

**SYNC**:
- Synchronizes ONE language file
- Requires manual file specification
- For advanced workflows with fine control

### Are COMPARE/EXTRACT/INJECT commands obsolete?

**No**, they are kept for:
- Established enterprise workflows
- Specific use cases (translators without GitHub)
- Detailed changelog generation

But **AUTO-SYNC replaces them** in 99% of cases.

### Can I combine AUTO-SYNC with advanced tools?

**Yes!**

Example:
1. AUTO-SYNC for quick synchronization
2. COMPARE for detailed changelog
3. EXTRACT to send partial files to external translator

---

## 📚 Resources

- [Main Documentation](../../README.md)
- [Extractor Documentation](../../1_Extractor/__doc/)
- [Applicator Documentation](../../2_Applicator/__doc/)

---

**Version**: 7.0
**Last update**: 2026-01-31
**New in v7.0**: INSTALL and AUTO-SYNC
