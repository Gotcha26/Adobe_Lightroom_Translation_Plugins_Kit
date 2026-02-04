# Adobe Lightroom Translation Plugins Kit

Are you developing a plugin for **Adobe Lightroom Classic** and would like it to support multiple languages?
Are you a translator and want to contribute to an existing plugin?
This toolkit is made for you!

---

## 🎯 The Challenge

Internationalizing a Lightroom plugin is tedious:
- Dozens (or even hundreds) of text strings to extract
- Localization keys to create and maintain
- Translation files to synchronize with each update
- Adobe SDK format that isn't always intuitive

**Result?** Many plugins remain monolingual, due to lack of time or appropriate tools.

---

## ✨ The Solution

This toolkit automates all the tedious work:

```
    Your Lua code                      Multilingual plugin
   (hardcoded text)                  (ready for translation)
        │                                      ▲
        │                                      │
        └──────────►  TOOLKIT  ►───────────────┘
                   (3 integrated tools)
```

**In just a few clicks**, you transform a monolingual plugin into one ready for international translation — without manually touching localization files.
And it's 100% compliant with the Adobe SDK.

---

## 💎 The Promise: Absolute Simplicity

Forget about `.pot`, `.mo`, `.po` files and complicated editors like POEdit with mandatory compilation. Say goodbye to tedious resynchronization hassles.

**Here's what you really get:**

### A Guided Interface, Zero Risk

Everything happens in **a simple terminal window** (Windows, macOS, Linux). No obscure interface, no command-line syntax to memorize, very explicit names for tools and actions.

```
┌────────────────────────────────────┐
│ LocalizationToolKit Menu           │
├────────────────────────────────────┤
│ 1. Extractor                       │
│ 2. Applicator                      │
│ 3. Translator                      │
│ 4. AUTOSYNC                        │
│ 5. Tools & Utilities               │
│ Q. Quit                            │
│                                    │
│ Choose an option: █                │
└────────────────────────────────────┘
```

**Every step is guided.** The toolkit explains exactly what will happen, asks for confirmation if needed, and warns you before any action. No risky manipulations, no risk of breaking anything.

### The Real Workflow

- **First time: 2 clicks**
  - Click 1: *Extractor* → analyzes your code and extracts text.
  - Click 2: *Applicator* → set up keys [`loc()` calls] while **retaining** text strings.

  **That's it.** Your plugin is ready for translation, 100% functional, straight out of the box. No compilation, no additional tools needed.

- **Code update: 1 click**
  - Click: *AUTOSYNC* → automatically synchronizes existing translations

  That's all. If you modified text in your code, translators are notified. If not, nothing to do.

- **Simple format**
  - No obscure tool configuration
  - Strict Adobe SDK compliance — no exotic dependencies
  - Configuration preserved automatically

**Result: less time tinkering, more time creating.**

In short: **ELEGANT AND EFFORTLESS!**

---

## 👥 Who Is This For?

### Lightroom Plugin Developers

You code, the toolkit handles the rest:
- **Automatic extraction** of all text strings
- **Key generation** according to Adobe SDK conventions
- **Synchronization** of language files with each update
- **Automatic backups** to revert if needed

> *"I code in English, I run the toolkit, and boom: my plugin is ready to receive translations in French, German, Spanish..."*

### Translators & Contributors

No need to be a developer to contribute:
- Translation files in simple text format
- Clear instructions for each level of involvement
- Ability to test your translations immediately

> *"I received a file, translated the lines, sent it back. Simple."*

> *"My favorite plugin deserves to be translated, I'll give it a try without pressure."*

---

## 🛠️ Three Tools, One Launcher

The toolkit brings together three complementary tools, accessible through a single menu:

| Tool | Role |
|------|------|
| ***Extractor*** | Scans your lua code and extracts text |
| ***Applicator*** | Replaces text with `LOC()` calls |
| ***Translator*** | Synchronizes all language files |

Each tool can work independently, but the ***LocalisationToolKit*** launcher orchestrates them intelligently while preserving your configuration.

---

## 🚀 Quick Start

```bash
# 1. Get the toolkit
git clone https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit.git

# 2. Navigate to the folder
cd Adobe_Lightroom_Translation_Plugins_Kit

# 3. Launch the menu
python LocalisationToolKit.py
```

**No external dependencies** — just Python 3.7+ and the standard library.

---

## 📖 Documentation

### To go further

- [Toolkit overview - general view](doc/en/README.md)

### Guides by Profile

| You are... | Start here... |
|------------|---------------|
| Lightroom plugin developer | [Installation Guide](doc/en/dev/01_Dev_Installation.md) |
| Developer in maintenance mode | [Maintenance Guide](doc/en/dev/02_Dev_Maintenance.md) |
| Advanced developer | [Advanced Workflows](doc/en/dev/03_Dev_Advanced.md) |
| Beginner translator | [Simple Contributor](doc/en/trad/01_Simple_Contributor.md) |
| Self-taught translator | [Resourceful Contributor](doc/en/trad/02_Resourceful_Contributor.md) |
| Professional translator | [Professional Contributor](doc/en/trad/03_Professional_Contributor.md) |

### Technical Documentation of Tools

Each tool has its own detailed documentation:
- [Extractor](tools/extractor/__doc__/en/README.md) — String extraction
- [Applicator](tools/applicator/__doc__/en/README.md) — Application of LOC() keys
- [Translator](tools/translator/__doc__/en/README.md) — Translation management
- [Toolbox](tools/toolbox/__doc__/en/README.md) — Utilities (restore, cleanup)

---

## 🤝 Contributing

### To the toolkit itself
- Report a bug or suggest an improvement via [GitHub Issues](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit/issues)
- Pull requests are welcome

### To plugin translations
- Consult the documentation of the plugin in question
- Fork, translate, submit a PR
- Or simply send your translated file to the developer

---

## 🙏 Acknowledgments

This project was born from a personal need: making my own Lightroom plugin multilingual without spending hours on it. Thanks to the assistance of **Claude (Anthropic)**, it has become a tool that I hope will be useful to the entire community.

Feedback, suggestions, and contributions are warmly encouraged!

*Made in France 🇫🇷 with love and sunshine in the south of Drôme Provençale, between Mistral and lavender.*

---

| 📜 | Traceability |  |  |
|--|--|--|--|
| **Name** | *README.md* | **Version** | 1.0 |
| **Type** | Presentation - Self-promotion | **Language** | EN - *[FR](Lisez-moi.md)* |
| **GitHub Project** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **License** | [MIT](LICENSE) | | |
