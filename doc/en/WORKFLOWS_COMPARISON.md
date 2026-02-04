# Translation Workflows Comparison

## Overview

This toolkit offers **3 workflows** depending on your situation and needs.

```
┌─────────────────────────────────────────────────────────────┐
│ NEW PLUGIN                                                  │
│ → Simple duplication (NEW_PLUGIN.md)                        │
│ ✓ For beginners                                             │
│ ✓ Plugin with no existing translations                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ STANDARD MAINTENANCE                                        │
│ → AUTO-SYNC (README.md / WORKFLOW_UPDATE.md)                │
│ ✓ For daily use                                             │
│ ✓ New/modified keys in English in complete file             │
│ ✗ No [NEW]/[NEEDS_REVIEW] markers                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ADVANCED CONTROL                                            │
│ → COMPARE → EXTRACT → INJECT (WORKFLOW_ADVANCED.md)         │
│ ✓ For professional translators                              │
│ ✓ Isolation of changes in TRANSLATE_xx.txt                  │
│ ✓ [NEW]/[NEEDS_REVIEW] markers if COMPARE → SYNC            │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Comparison

| Criteria | New LrC Plugin | AUTO-SYNC | COMPARE → EXTRACT → INJECT |
|----------|---------------|-----------|----------------------------|
| **Commands** | ***Extractor*** → *Duplicate* | ***Extractor*** → **AUTO-SYNC** | **COMPARE** → **EXTRACT** → **INJECT** |
| **Translator File** | `TranslatedStrings_xx.txt` (all in English) | `TranslatedStrings_xx.txt` (new keys in EN) | `TRANSLATE_xx.txt` (changes only) |
| **Markers** | ❌ No | ❌ No | ✅ Yes (if **COMPARE** → **SYNC**) |
| **File Size** | 300 lines (all) | 300 lines (complete) | 62 lines (changes) |
| **Identifying Changes** | Everything to translate | Look for English keys | Isolated `TRANSLATE-xx.txt` file |
| **Complexity** | Simple | Simple | Advanced |
| **Use Case** | New LrC plugin | Regular maintenance | Large volumes, fine control |

---

## Visual Examples

### Workflow 1: **New LrC Plugin**

**File `TranslatedStrings_fr.txt` after duplication**:
```
"$$$/MyPlugin/Menu/File=File"                    ← All in English
"$$$/MyPlugin/Menu/Edit=Edit"                    ← To translate
"$$$/MyPlugin/Dialog/OK=OK"                      ← To translate
```

**Action for translator**: Translate all lines.

---

### Workflow 2: **AUTO-SYNC**

**Before AUTO-SYNC** (278 keys, 100% translated):
```
"$$$/MyPlugin/Menu/File=Fichier"
"$$$/MyPlugin/Menu/Edit=Édition"
"$$$/MyPlugin/Dialog/OK=Valider"
```

**After AUTO-SYNC** (330 keys, new ones in English):
```
"$$$/MyPlugin/Menu/File=Fichier"                 ← Preserved
"$$$/MyPlugin/Menu/Edit=Édition"                 ← Preserved
"$$$/MyPlugin/Dialog/OK=Valider"                 ← Preserved
"$$$/MyPlugin/NewFeature=Export to Cloud"        ← NEW (in English)
"$$$/MyPlugin/Modified=New text here"            ← MODIFIED (in English)
```

**Action for translator**: Look for English keys and translate them.

---

### Workflow 3: **COMPARE** → **EXTRACT** → **INJECT**

**Step 1: EXTRACT generates TRANSLATE_fr.txt**:
```
# ======================================================================
# NEW KEYS (50)
# ======================================================================

[KEY] $$$/MyPlugin/NewFeature
[EN]  Export to Cloud
[FR] →

# ======================================================================
# MODIFIED KEYS (12)
# ======================================================================

[KEY] $$$/MyPlugin/Modified
[EN BEFORE]  Old text
[EN AFTER]   New text here
[FR CURRENT] Ancien texte
[FR] →
```

**Step 2: Translator edits `TRANSLATE_fr.txt`**:
```
[FR] → Exporter vers le Cloud

[FR] → Nouveau texte ici
```

**Step 3: **INJECT** merges into `TranslatedStrings_fr.txt`**:
```
"$$$/MyPlugin/Menu/File=Fichier"                 ← Preserved
"$$$/MyPlugin/NewFeature=Exporter vers le Cloud" ← Merged
"$$$/MyPlugin/Modified=Nouveau texte ici"        ← Merged
```

**Bonus: **SYNC** with `UPDATE_xx.json` adds markers**:
```
"$$$/MyPlugin/Menu/File=Fichier"
-- [NEW] To translate
"$$$/MyPlugin/NewFeature=Exporter vers le Cloud"
-- [NEEDS_REVIEW] English text was modified
"$$$/MyPlugin/Modified=Nouveau texte ici"
```

#### The [NEW] and [NEEDS_REVIEW] Markers

> ℹ️ These markers appear only within the context of [Workflow 3](#workflow-3--compare--extract--inject).

##### ❌ Do NOT appear with:
- New plugin workflow (simple duplication)
- **AUTO-SYNC** (standard workflow)

##### ✅ Appear ONLY with:
- **COMPARE** → **SYNC** (with `UPDATE_xx.json`)

##### What are they for?
In a specific large-scale translation workflow, they help highlight keys that require special attention because they are "buried in the mass" within the `TranslatedString_xx.txt` file.
Since it's better to use a dedicated file for this task... More info: [SYNC.md](../../3_Translator/__doc/en/commands/SYNC.md)

##### Source Code Responsible

```python
# TR_sync.py lines 131-141
# ONLY if update_data provided via COMPARE
if update_data and key in changed_keys:
    markers[key] = "-- [NEEDS_REVIEW] English text was modified"

if update_data:
    markers[key] = "-- [NEW] To translate"
```

---

## Which Workflow to Choose?

### New LrC Plugin (first localization)
→ **Workflow 1: Extractor → Applicator**
- ***Extractor***
- ***Applicator***
- Duplicate `TranslatedStrings_xx.txt` for each language
- Send to translators

**Why**: Simple, straightforward, no need for complexity.

---

### Existing LrC Plugin with Some Changes
→ **Workflow 2: Extractor → Translator → AUTO-SYNC**
- ***Extractor***
- ***Translator***
- **AUTO-SYNC**
- Translators visually search for English keys in the complete file.

**Why**: Fast, automatic, no intermediate files.

---

### Plugin with Major Changes + Professional Translators
→ **Workflow 3: COMPARE → EXTRACT → INJECT**
- **COMPARE** (difference analysis)
- **EXTRACT** (generates `TRANSLATE_xx.txt` with changes only)
- Translators edit `TRANSLATE_xx.txt`
- **INJECT** (merges into `TranslatedStrings_xx.txt`)
- **SYNC** with `UPDATE_en.json` (adds optional markers)

**Why**: Complete isolation, fine control, markers for professional translators.

---

## Technical Summary

| Workflow | Uses UPDATE_en.json | [NEW]/[NEEDS_REVIEW] Markers | Translator File |
|----------|------------------------|--------------------------------|--------------------|
| **New plugin** | ❌ No | ❌ No | `TranslatedStrings_xx.txt` (complete) |
| **AUTO-SYNC** | ❌ No | ❌ No | `TranslatedStrings_xx.txt` (complete) |
| **COMPARE** → **EXTRACT** → **INJECT** | ✅ Yes | ❌ No (unless SYNC after) | `TRANSLATE_xx.txt` (partial) |
| **COMPARE** → **SYNC** | ✅ Yes | ✅ Yes | `TranslatedStrings_xx.txt` (with markers) |

---

## Related Documentation

### Guides for Developers

| Resource | Description |
| --- | --- |
| 🗒 [Installation new plugin](dev/01_Installation.md) | *Initial setup* |
| 🗒 [Maintenance](dev/02_Maintenance.md) | *Daily AUTO-SYNC workflow* |
| 🗒 [Advanced Workflows](dev/03_Advanced.md) | *COMPARE/EXTRACT/INJECT* |

### Guides for Translators

| Resource | Description |
| --- | --- |
| 🗒 [Simple Contributor](trad/01_Simple_Contributor.md) | *Existing file, ready to translate* |
| 🗒 [Independent Contributor](trad/02_Independent_Contributor.md) | *Create file yourself* |
| 🗒 [Professional Contributor](trad/03_Professional_Contributor.md) | *CAT tools and large volumes* |

### Technical Documentation
- [README.md](README.md) — Complete technical documentation

---

| 📜 | Traceability |  |  |
|--|--|--|--|
| **Name** | *WORKFLOWS_COMPARISON.md* | **Version** | 1.1 |
| **Type** | Help - choice - understanding | **Language** | EN - *[FR](../fr/WORKFLOWS_COMPARAISON.md)* |
| **GitHub Project** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **License** | Open source | | |
