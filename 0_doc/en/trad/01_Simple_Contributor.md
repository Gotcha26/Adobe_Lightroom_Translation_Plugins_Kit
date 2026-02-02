# Translator Guide: Simple Contributor

Do you want to translate a Lightroom plugin into your language? This guide is made for you. **No technical skills required**, just mastery of your target language.

---

## 📋 Typical Situation

The developer has sent you a `TranslatedStrings_fr.txt` file (or your language) to translate. The file already exists, it contains English keys that you need to translate.

---

## 🛠️ What You Need

### A Simple Text Editor

| Editor | Platform | Recommendation |
|--------|----------|----------------|
| [VS Code](https://code.visualstudio.com/) | Windows, Mac, Linux | Recommended (free) |
| [Notepad++](https://notepad-plus-plus.org/) | Windows | Excellent |
| [Sublime Text](https://www.sublimetext.com/) | Windows, Mac, Linux | Excellent |

**Absolutely avoid:**
- Microsoft Word
- Google Docs
- LibreOffice Writer

These programs add hidden formatting that corrupts the file.

### Important Checks

- **UTF-8 Encoding**: For accents and special characters
- **No Formatting**: Plain text only

---

## 🎯 Understanding the Format

Each line in the file looks like this:

```
"$$$/MyPlugin/Menu/File=File"
```

**Anatomy:**
```
"$$$/MyPlugin/Menu/File=File"
 └────────KEY─────────┘ └VALUE┘
       DO NOT TOUCH    TRANSLATE THIS
```

**Golden Rule**: Translate **only** what comes after the `=`

---

## 📝 The Translation Process

### Step 1: Open the File

1. Open your text editor
2. Open the `TranslatedStrings_fr.txt` file
3. Check the encoding (UTF-8) at the bottom of the window

### Step 2: Translate Line by Line

**Before:**
```
"$$$/MyPlugin/Menu/File=File"
"$$$/MyPlugin/Menu/Edit=Edit"
"$$$/MyPlugin/Menu/View=View"
"$$$/MyPlugin/Dialog/OK=OK"
"$$$/MyPlugin/Dialog/Cancel=Cancel"
```

**After (French):**
```
"$$$/MyPlugin/Menu/File=Fichier"
"$$$/MyPlugin/Menu/Edit=Édition"
"$$$/MyPlugin/Menu/View=Affichage"
"$$$/MyPlugin/Dialog/OK=Valider"
"$$$/MyPlugin/Dialog/Cancel=Annuler"
```

### Step 3: Handle Placeholders

Some strings contain **special codes** that you should **never translate**:

| Code | Meaning | Example |
|------|---------|---------|
| `%s` | Variable text | `"Uploaded %s"` → `"Téléversé %s"` |
| `%d` | Number | `"Found %d photos"` → `"Trouvé %d photos"` |
| `\n` | Line break | Keep as is |
| `\t` | Tabulation | Keep as is |

**Example:**
```
BEFORE : "$$$/Plugin/Status/Count=%d items selected"
AFTER  : "$$$/Plugin/Status/Count=%d éléments sélectionnés"
                                   ↑
                            Keep the %d!
```

### Step 4: Save and Verify

1. Save the file (Ctrl+S)
2. Check that the encoding is still UTF-8
3. Reread a few lines to check consistency

---

## ✅ Checklist Before Sending

- [ ] All lines are translated
- [ ] The keys (before the `=`) have not been modified
- [ ] Placeholders (`%s`, `%d`, `\n`) are intact
- [ ] Encoding is UTF-8
- [ ] No lines deleted

---

## 💡 Practical Tips

### Be Consistent

Always use the same word for the same concept:

```
PERSONAL GLOSSARY
───────────────────────────────────
File        → Fichier
Edit        → Édition
View        → Affichage
Settings    → Paramètres
OK          → Valider
Cancel      → Annuler
Save        → Enregistrer
Delete      → Supprimer
Export      → Exporter
Import      → Importer
```

### Think About the Interface

The translated text will appear in menus, buttons, dialogs. Check that:
- The text is not too long
- The meaning is clear in the context of a photo software

### Useful Tools

| Tool | Usage |
|------|-------|
| [DeepL](https://www.deepl.com/) | Reference translation (best quality) |
| [Reverso Context](https://context.reverso.net/) | See terms in context |
| [Google Translate](https://translate.google.com/) | Quick translation |

---

## 📤 Return the File

Once complete, return the file to the developer by:
- Email
- GitHub Pull Request (if you know how)
- Any other agreed method

**Typical Email:**
```
Subject: MyPlugin Translation - French Complete

Hello,

Please find attached the TranslatedStrings_fr.txt file
that I have fully translated.

- All keys are translated
- UTF-8 encoding verified
- Placeholders preserved

Best regards,
[Your name]
```

---

## ❓ Frequently Asked Questions

### Do I have to translate everything at once?

**No.** Lightroom displays English by default for untranslated keys. You can translate progressively and return partial versions.

### How do I test my translations?

1. Place the translated file in the plugin folder
2. Change your system language
3. Restart Lightroom completely
4. Check the display

### I don't understand the context of a string

Ask the developer! They can provide you with screenshots or explanations about where and how the string appears.

---

## 🔗 Resources

- [Resourceful Contributor Guide](02_Resourceful_Contributor.md) — If the file doesn't exist yet
- [Professional Contributor Guide](03_Professional_Contributor.md) — Advanced tools and workflows

---

| 📜 | Traceability |  |  |
|--|--|--|--|
| **Name** | *01_Simple_Contributor.md* | **Version** | 1.0 |
| **Type** | Traductor guide - Easy | **Language** | EN - *[FR](../../fr/trad/01_Contributeur_simple.md)* |
| **GitHub Project** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **License** | Open source | | |
