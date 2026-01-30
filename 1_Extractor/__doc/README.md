# Extractor - Technical Documentation

**Version 5.1 | January 2026**

## Overview

Extractor is the first tool in the localization chain. Its role is to analyze the Lua files of a Lightroom plugin and automatically extract all text strings that should be localized.

## Project Architecture

```
1_Extractor/
├── Extractor_main.py         ← Entry point, orchestration
├── Extractor_config.py       ← Regex patterns and constants
├── Extractor_models.py       ← Data classes (StringMember, ExtractedString, etc.)
├── Extractor_utils.py        ← Utility functions (spaces, keys, filters)
├── Extractor_engine.py       ← Main extraction engine
├── Extractor_output.py       ← Output file generation
├── Extractor_report.py       ← Report generation
├── Extractor_menu.py         ← Interactive interface
└── __doc/
    └── README.md             ← This file
```
```
┌─────────────────────────────────────────────────────────────┐
│                    Extractor_main.py                        │
│                    (orchestrator)                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│ LocalizableString│ │Output        │ │Report            │
│Extractor         │ │Generator     │ │Generator         │
│(engine.py)       │ │(output.py)   │ │(report.py)       │
└────────┬─────────┘ └──────┬───────┘ └──────┬───────────┘
         │                  │                │
         ├─ Uses:           ├─ Uses:         └─ Uses:
         │  • config.py     │  • models.py      • models.py
         │  • models.py     │  • utils.py       • output.py
         │  • utils.py      │
         │
```

The architecture is modular to facilitate maintenance and evolution. Each module has a clear responsibility.

## Detailed Operation

### Phase 1: File Analysis

```
Lightroom Plugin (.lrplugin)
    │
    ├── Recursive scan of .lua files
    │   │
    │   ├── Line-by-line reading
    │   │
    │   └── Pattern detection
    │       │
    │       ├── UI strings (title = "Submit")
    │       ├── Concatenations (a .. "text" .. b)
    │       └── UI contexts (bind_to_object, f:static_text, etc.)
    │
    └── Smart filtering
        │
        ├── Ignore existing LOC keys
        ├── Ignore logs (logInfo, logError)
        ├── Ignore technical values
        └── Ignore strings too short
```

### Phase 2: Extraction and Metadata

For each detected string:

```
"  Hello World  :  "
    │
    ├── Base text: "Hello World"
    ├── Leading spaces: 2
    ├── Trailing spaces: 2
    ├── Suffix: " : "
    │
    └── LOC key generation
        │
        ├── Normalization (alphanumerics + underscores)
        ├── Camel case (HelloWorld)
        ├── Add file context (MyDialog_HelloWorld)
        └── Uniqueness (HelloWorld_2 if collision)
```

All this metadata is preserved so that the Applicator can reconstruct exactly the original string.

### Phase 3: File Generation

#### TranslatedStrings_en.txt

Lightroom SDK format, directly usable in the plugin:

```
-- =============================================================================
-- Plugin Localization - EN
-- Generated: 2026-01-30 15:00:00
-- Total keys: 124
-- =============================================================================

-- -----------------------------------------------------------------------------
-- IMPORTANT NOTES FOR TRANSLATORS:
-- -----------------------------------------------------------------------------
-- 1. DO NOT translate the following patterns (keep them exactly as-is):
--    - %s, %d, %f, %i, %u, %x, %X, %o, %c, %e, %E, %g, %G (format specifiers)
--    - %1, %2, %3... (numbered placeholders)
--    - \n (newline character)
--    - \t (tab character)
--    - \" (escaped quote)
--    - \\ (escaped backslash)
--    - ... (ellipsis used as placeholder)
--    - Technical terms in UPPERCASE (API, URL, HTTP, JSON, etc.)
--
-- 2. PRESERVE spaces around text exactly as they appear:
--    - Leading spaces (before text) are used for layout/alignment
--    - Trailing spaces (after text) are used for concatenation
--    - Example: "  Hello  " must keep both leading and trailing spaces
--
-- 3. Keep the same punctuation style (colons, periods, etc.)
-- -----------------------------------------------------------------------------

"$$$/Piwigo/Submit=Submit"
"$$$/Piwigo/Cancel=Cancel"
"$$$/Piwigo/Dialog_PleaseWait=Please wait..."
```

Each line contains:
- The complete LOC key with prefix
- The `=` symbol
- The default value in English (or other base language)

The header includes important notes for translators regarding patterns not to translate and space preservation.

#### spacing_metadata.json

Metadata to reconstruct spaces and suffixes:

```json
{
  "$$$/Piwigo/Submit": {
    "leading_spaces": 0,
    "trailing_spaces": 0,
    "suffix": ""
  },
  "$$$/Piwigo/Dialog_PleaseWait": {
    "leading_spaces": 2,
    "trailing_spaces": 3,
    "suffix": "..."
  }
}
```

#### replacements.json

Precise instructions for Applicator:

```json
{
  "files": {
    "MyDialog.lua": {
      "total_replacements": 15,
      "replacements": [
        {
          "line_num": 42,
          "original_line": "title = \"Submit\",",
          "members": [
            {
              "original_text": "Submit",
              "base_text": "Submit",
              "loc_key": "$$$/Piwigo/Submit",
              "leading_spaces": 0,
              "trailing_spaces": 0,
              "suffix": ""
            }
          ]
        }
      ]
    }
  }
}
```

#### extraction_report.txt

Detailed report with statistics:

```
================================================================================
EXTRACTION REPORT - PiwigoPublish Plugin
================================================================================

GLOBAL STATISTICS
--------------------------------------------------------------------------------
Files analyzed           : 12
Files with extractions   : 8
UI lines detected        : 156
Unique strings           : 124
Ignored strings          : 32
Existing LOC keys        : 18

DETAIL BY FILE
--------------------------------------------------------------------------------

MyDialog.lua
  UI lines : 42
  Strings  : 35
  LOC keys : 7 (already localized)

  $$$/Piwigo/Submit          → "Submit"
  $$$/Piwigo/Cancel          → "Cancel"
  ...
```

## Configuration Options

### Interactive Mode

Simply launch `Extractor_main.py` to access the interactive menu:

```
==================================================
        EXTRACTOR - Configuration
==================================================

Current options:
  Plugin path    : ./myPlugin.lrplugin
  LOC prefix     : $$$/MyPlugin
  Language       : en
  Min length     : 3
  Ignore logs    : Yes

[1] Modify plugin path
[2] Modify LOC prefix
[3] Modify language
[4] Advanced options
[5] Launch extraction
[0] Exit
```

### CLI Mode

```bash
python Extractor_main.py --plugin-path ./plugin.lrplugin [OPTIONS]
```

**Available options:**

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--plugin-path` | Plugin path (REQUIRED) | - | `./myPlugin.lrplugin` |
| `--output-dir` | Custom output directory | `<plugin>/__i18n_tmp__/Extractor/` | `./output` |
| `--prefix` | LOC keys prefix | `$$$/Piwigo` | `$$$/MyApp` |
| `--lang` | Base language code | `en` | `fr`, `de`, `es` |
| `--exclude` | Files to exclude (repeatable) | - | `--exclude test.lua --exclude debug.lua` |
| `--min-length` | Minimum string length | `3` | `5` |
| `--no-ignore-log` | Don't ignore logs | false | - |

### Usage Examples

**Standard extraction:**
```bash
python Extractor_main.py --plugin-path ./piwigoPublish.lrplugin
```

**Extraction with custom prefix:**
```bash
python Extractor_main.py --plugin-path ./myPlugin.lrplugin --prefix $$$/MyApp
```

**Extraction with exclusions:**
```bash
python Extractor_main.py \
  --plugin-path ./plugin.lrplugin \
  --exclude test.lua \
  --exclude deprecated.lua \
  --min-length 5
```

**Extraction with French as base language:**
```bash
python Extractor_main.py \
  --plugin-path ./plugin.lrplugin \
  --lang fr \
  --prefix $$$/MyApp
```

## Extraction Patterns

Extractor automatically detects several UI contexts in Lua code.

### Recognized UI Contexts

```lua
-- 1. Widget titles and labels
f:static_text {
    title = "Hello World",      -- ✓ Extracted
}

-- 2. bind_to_object (bound components)
f:edit_field {
    bind_to_object = propertyTable,
    value = LrBinding.keyToProp("apiKey"),
    title = "API Key:",         -- ✓ Extracted
}

-- 3. Menu items
f:popup_menu {
    items = {
        { title = "Option 1", value = "opt1" },  -- ✓ Extracts "Option 1"
        { title = "Option 2", value = "opt2" },  -- ✓ Extracts "Option 2"
    }
}

-- 4. String concatenations
local message = "Upload " .. count .. " photos"  -- ✓ Extracts "Upload " and " photos"

-- 5. Function returns
function getTitle()
    return "My Title"           -- ✓ Extracted
end

-- 6. Strings in arrays
local messages = {
    "First message",            -- ✓ Extracted
    "Second message",           -- ✓ Extracted
}
```

### Ignored Patterns

```lua
-- Logs (if --no-ignore-log not specified)
logInfo("Debug message")        -- ✗ Ignored
log:trace("Trace info")         -- ✗ Ignored

-- Technical values
color = "red"                   -- ✗ Ignored (technical value)
format = "jpg"                  -- ✗ Ignored (format)

-- Existing LOC keys
title = LOC "$$$/App/Title=Title"  -- ✗ Ignored (already localized)

-- Strings too short (< min_length)
x = "OK"                        -- ✗ Ignored if min_length > 2
```

## Space and Suffix Management

Extractor intelligently preserves spaces and suffixes to ensure identical rendering after application.

### Spaces

```lua
-- Before
title = "  Hello World  "

-- Extraction
{
  "base_text": "Hello World",
  "leading_spaces": 2,
  "trailing_spaces": 2
}

-- After Applicator
title = "  " .. LOC "$$$/App/HelloWorld=Hello World" .. "  "
```

### Suffixes

```lua
-- Before
label = "Username:"

-- Extraction
{
  "base_text": "Username",
  "suffix": ":"
}

-- After Applicator
label = LOC "$$$/App/Username=Username" .. ":"
```

### Complex Concatenations

```lua
-- Before
message = "  Processing " .. count .. " files...  "

-- Extraction (2 members)
[
  {
    "base_text": "Processing ",
    "leading_spaces": 2
  },
  {
    "base_text": " files",
    "suffix": "...",
    "trailing_spaces": 2
  }
]

-- After Applicator
message = "  " .. LOC "$$$/App/Processing=Processing " .. count .. LOC "$$$/App/Files=files" .. "..." .. "  "
```

## LOC Key Generation

LOC keys are generated using a strict algorithm to ensure their uniqueness and readability.

### Generation Steps

```
Original text: "Please wait..."
    │
    ├── 1. Cleanup (alphanumerics + spaces)
    │   └── "Please wait"
    │
    ├── 2. Camel case
    │   └── "PleaseWait"
    │
    ├── 3. File context (name without extension)
    │   └── "MyDialog_PleaseWait"
    │
    ├── 4. Uniqueness check
    │   └── If exists: "MyDialog_PleaseWait_2"
    │
    └── 5. Prefix
        └── "$$$/Piwigo/MyDialog_PleaseWait"
```

### Generation Examples

| Original text | File | Generated key |
|---------------|------|---------------|
| `"Submit"` | `Dialog.lua` | `$$$/Piwigo/Dialog_Submit` |
| `"Please wait..."` | `Upload.lua` | `$$$/Piwigo/Upload_PleaseWait` |
| `"API Key:"` | `Settings.lua` | `$$$/Piwigo/Settings_APIKey` |
| `"Photo(s)"` | `Main.lua` | `$$$/Piwigo/Main_Photos` |

### Collision Handling

If a key already exists, a numeric suffix is added:

```
$$$/Piwigo/Submit       → First occurrence
$$$/Piwigo/Submit_2     → Second occurrence
$$$/Piwigo/Submit_3     → Third occurrence
```

## Statistics and Reports

The extraction report provides detailed information about the process.

### Global Metrics

- **Files analyzed**: Total number of `.lua` files scanned
- **Files with extractions**: Files containing at least one string to extract
- **UI lines detected**: Number of lines containing UI patterns
- **Unique strings**: Number of LOC keys generated
- **Ignored strings**: Filtered strings (logs, technical, too short)
- **Existing LOC keys**: Keys already localized in the code

### Details by File

For each file:
- List of generated LOC keys
- Default value of each key
- Metadata (spaces, suffixes)
- Extraction context

## Advanced Use Cases

### Multilingual Base Extraction

If your plugin is initially in French and you want to anglicize it:

```bash
python Extractor_main.py \
  --plugin-path ./myPlugin.lrplugin \
  --lang fr \
  --prefix $$$/MyApp
```

This generates `TranslatedStrings_fr.txt` instead of `TranslatedStrings_en.txt`. You can then create `TranslatedStrings_en.txt` by duplicating and translating.

### Re-execution on a Partially Localized Project

Extractor automatically detects existing LOC keys and doesn't re-extract them. You can therefore re-run the extraction after adding new code.

```bash
# First extraction
python Extractor_main.py --plugin-path ./plugin.lrplugin

# ... development, new features ...

# New extraction (doesn't touch existing keys)
python Extractor_main.py --plugin-path ./plugin.lrplugin
```

Already localized keys are listed in the report but are not added to the output file.

### Targeted Extraction with Exclusions

To extract only certain files:

```bash
python Extractor_main.py \
  --plugin-path ./plugin.lrplugin \
  --exclude test.lua \
  --exclude debug.lua \
  --exclude vendor/external.lua
```

### Custom Prefix per Plugin

Each plugin should have its own prefix to avoid conflicts:

```bash
# Plugin 1
python Extractor_main.py --plugin-path ./pluginA.lrplugin --prefix $$$/PluginA

# Plugin 2
python Extractor_main.py --plugin-path ./pluginB.lrplugin --prefix $$$/PluginB
```

## Troubleshooting

### No Strings Extracted

**Possible causes:**
- The `--min-length` parameter is too high
- Strings are already localized
- Patterns don't match your code
- Plugin path is incorrect

**Solutions:**
```bash
# Reduce minimum length
python Extractor_main.py --plugin-path ./plugin.lrplugin --min-length 1

# Check path
ls ./plugin.lrplugin/*.lua

# Consult report to understand what was ignored
```

### Too Many Strings Extracted (logs included)

If log messages are extracted by mistake:

```bash
# Make sure default option is active
python Extractor_main.py --plugin-path ./plugin.lrplugin
```

Logs are ignored by default. If you used `--no-ignore-log`, remove this option.

### Unreadable Generated LOC Keys

If generated keys are too long or complex:

1. Shorten original texts in the code
2. Or manually edit the `TranslatedStrings_xx.txt` file after extraction
3. **Important**: If you change keys, also update `replacements.json` for Applicator

### Incorrect Encoding (special characters)

All files are read and written in UTF-8. If you see incorrectly encoded characters:

```bash
# Check encoding of your .lua files
file --mime-encoding *.lua

# Convert if necessary (Linux/Mac example)
iconv -f ISO-8859-1 -t UTF-8 file.lua > file_utf8.lua
```

## Technical FAQ

### Can I modify detection patterns?

Yes, edit the [Extractor_config.py:1](1_Extractor/Extractor_config.py#L1) file. Patterns are defined in the constants `UI_CONTEXT_PATTERNS`, `UI_KEYWORDS`, etc.

### Is metadata really necessary?

Yes, it ensures that Applicator reconstructs exactly the original strings with spaces and suffixes. Without it, the rendering would be different.

### How to add a new widget type to detect?

Add the pattern in [Extractor_config.py:1](1_Extractor/Extractor_config.py#L1):

```python
UI_KEYWORDS = [
    "title", "label", "value", "placeholder",
    "my_new_widget",  # Add here
]
```

### Can I use Extractor on other types of projects?

Extractor is specific to Lua format and Lightroom SDK. For other languages or frameworks, you would need to adapt patterns in `Extractor_config.py` and potentially the engine in `Extractor_engine.py`.

### Can generated files be versioned (Git)?

- **TranslatedStrings_xx.txt**: Yes, at plugin root
- **__i18n_tmp__/**: No, add it to `.gitignore` (temporary files)

## Performance

### Typical Execution Times

- Small plugin (5-10 files, < 1000 lines): < 1 second
- Medium plugin (20-30 files, ~5000 lines): 2-3 seconds
- Large plugin (50+ files, > 10000 lines): 5-10 seconds

### Possible Optimizations

Extractor is already optimized, but if you work on very large projects:

1. Use `--exclude` to ignore large irrelevant files
2. Increase `--min-length` to filter more strings
3. Run extraction outside active development hours

## Integration in Automated Workflow

Extractor can be integrated into a build script or CI/CD pipeline.

### Bash Script Example

```bash
#!/bin/bash
# extract_and_check.sh

PLUGIN_PATH="./myPlugin.lrplugin"
OUTPUT_DIR="./extraction_output"

# Launch extraction
python 1_Extractor/Extractor_main.py \
  --plugin-path "$PLUGIN_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --prefix '$$$/MyApp'

# Check success
if [ $? -eq 0 ]; then
  echo "✓ Extraction successful"
  # Copy language file to plugin root
  cp "$OUTPUT_DIR/TranslatedStrings_en.txt" "$PLUGIN_PATH/"
else
  echo "✗ Extraction failed"
  exit 1
fi
```

### Python Script Example

```python
#!/usr/bin/env python3
import subprocess
import sys

def run_extraction(plugin_path, prefix="$$$/MyApp"):
    """Launch Extractor via subprocess."""
    cmd = [
        sys.executable,
        "1_Extractor/Extractor_main.py",
        "--plugin-path", plugin_path,
        "--prefix", prefix
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Extraction successful")
        print(result.stdout)
        return True
    else:
        print("✗ Failed")
        print(result.stderr)
        return False

if __name__ == "__main__":
    success = run_extraction("./myPlugin.lrplugin")
    sys.exit(0 if success else 1)
```

## Additional Resources

- **Lightroom SDK**: [Adobe Developer Console](https://developer.adobe.com/console)
- **LOC Format**: `LOC "$$$/Key=Default"` (default value mandatory)
- **Python Regular Expressions**: [re documentation](https://docs.python.org/3/library/re.html)
- **Python JSON**: [json documentation](https://docs.python.org/3/library/json.html)

## Contributions

This project is open to contributions. If you want to:
- Add new detection patterns
- Improve key generation
- Optimize performance
- Fix bugs

Don't hesitate to propose your changes!

---

**Developed by Julien MOREAU with the help of Claude (Anthropic)**

For any questions or issues, consult the main README or open an issue on the GitHub repository.
