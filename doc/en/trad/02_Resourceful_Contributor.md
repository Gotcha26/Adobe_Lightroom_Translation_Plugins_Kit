# Translator Guide: Resourceful Contributor

The plugin you want to translate **doesn't yet have a** `TranslatedStrings_xx.txt` **file** for your language? This guide shows you how to create it yourself.

---

## 📋 Typical Situation

You found an interesting Lightroom plugin, but it only exists in English:

```
myPlugin.lrplugin/
├── Info.lua
├── PluginCode.lua
└── TranslatedStrings_en.txt      ← Only existing file
```

You want to create the French version (or another language).

---

## 🎯 Two Possible Approaches

### Approach A: Simple Duplication (without the toolkit)

If you don't have Python or don't want to install the toolkit:

1. **Copy** the English file
2. **Rename** it with your language code
3. **Translate** line by line

```bash
# In the plugin folder
cp TranslatedStrings_en.txt TranslatedStrings_fr.txt
```

Then open `TranslatedStrings_fr.txt` and translate each value.

### Approach B: With the toolkit (recommended)

If you have Python installed, the toolkit makes the work easier.

---

## 🚀 Approach B in Detail: With the Toolkit

### Step 1: Install the toolkit

```bash
git clone https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit.git
cd Adobe_Lightroom_Translation_Plugins_Kit
```

### Step 2: Configure the target plugin

```bash
python LocalisationToolKit.py
# Choose [6] Configuration
# Enter the path to the plugin
```

### Step 3: Extract strings (optional but recommended)

If the plugin doesn't have a `TranslatedStrings_en.txt` file or if you want to validate its structure:

```bash
# Choose [1] Extractor
```

This generates a clean reference file.

### Step 4: Create the file for your language

**Simple option**: Manually duplicate the English file:

```bash
cp myPlugin.lrplugin/TranslatedStrings_en.txt myPlugin.lrplugin/TranslatedStrings_fr.txt
```

**Toolkit option**: Use ***Translator***:

```bash
python LocalisationToolKit.py
# Choose [3] Translator
# Choose the option to create a new language file
```

### Step 5: Translate

Open your `TranslatedStrings_fr.txt` file and translate each line:

```
BEFORE : "$$$/Plugin/Menu/File=File"
AFTER  : "$$$/Plugin/Menu/File=Fichier"
```

See the [Simple Contributor Guide](01_Simple_Contributor.md) for translation details.

---

## 📝 Points of Attention

### Respect the exact format

Each line must retain its structure:

```
"$$$/Prefix/Category/Key=Translated value"
```

- Quotes `"` at the beginning and end
- Complete key before the `=`
- No space around the `=`

### Preserve placeholders

```
✅ "$$$/Status=Uploaded %d files to %s"
❌ "$$$/Status=Uploaded files to"  (placeholders removed)
```

### Encode in UTF-8

For accents (é, è, ê, ç, etc.), the file must be in UTF-8.

---

## 🧪 Test Your Translations

### Immediate Local Test

1. Place your translated file in the plugin:
   ```
   myPlugin.lrplugin/TranslatedStrings_fr.txt
   ```

2. Change your system language to French

3. Restart Lightroom **completely** (not just "Reload Plugin")

4. Check that your translations appear

### If It Doesn't Work

- Check the filename: `TranslatedStrings_fr.txt` (not `FR`, not `french`)
- Check that the file is at the root of the `.lrplugin`
- Check UTF-8 encoding
- Restart Lightroom completely

---

## 📤 Share Your Translation

Once satisfied with your translation, share it with the community!

### Via GitHub (recommended)

1. **Fork** the plugin's repository
2. **Add** your `TranslatedStrings_fr.txt` file
3. **Create a Pull Request**

```bash
git add TranslatedStrings_fr.txt
git commit -m "i18n(fr): Add French translation"
git push origin main
# Then create the Pull Request on GitHub
```

### Without GitHub

Simply send the file to the developer by email or message.

---

## 💡 Tips for Quality Translation

### Understand the Context

- Download and install the plugin
- Use it to understand where each text appears
- Adapt the translation to the context (menu, button, error message...)

### Create a Glossary

Before you start, define your translation choices:

```
GLOSSARY
─────────────────────────
Export      → Exporter (not "Exportation")
Settings    → Paramètres (not "Réglages")
Publish     → Publier
Upload      → Téléverser
Download    → Télécharger
Sync        → Synchroniser
```

### Test Regularly

Don't translate everything at once. Translate by sections and test as you go.

---

## 🔗 Resources

- [Simple Contributor Guide](01_Simple_Contributor.md) — Details on format and translation
- [Professional Contributor Guide](03_Professional_Contributor.md) — Advanced tools
- [Technical Documentation](../README.md)

---

| 📜 | Traceability |  |  |
|--|--|--|--|
| **Name** | *02_Resourceful_Contributor.md* | **Version** | 1.0 |
| **Type** | Traductor guide - Intermediate | **Language** | EN - *[FR](../../fr/trad/01_Contributeur_simple.md)* |
| **GitHub Project** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **License** | Open source | | |
