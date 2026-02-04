# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-02-04

### Added
- **Extractor**: Scans Lua code and extracts localizable text strings
- **Applicator**: Replaces text with `LOC()` calls while preserving strings
- **Translator**: Synchronizes all language files
  - `extract` - Extract strings from TranslatedStrings files
  - `inject` - Inject translations back
  - `sync` - Synchronize with reference language
  - `autosync` - One-click synchronization
  - `compare` - Compare translation files
  - `addlang` - Add a new language
  - `install` - Install translations in plugin
- **Toolbox**: Utilities
  - Backup restoration
  - Temporary folder cleanup
- **LocalizationToolKit.py**: Unified launcher with interactive menu
- Bilingual documentation (EN/FR)
- Bilingual UI (EN/FR) via gettext
- Configuration persistence (`config.json`)

### Technical
- Python 3.7+ compatibility
- Zero external dependencies (standard library only)
- Adobe Lightroom SDK compliance

---

## [Unreleased]

### Planned
- Additional UI languages
- GitHub Actions for CI/CD
- Unit tests

---

*For detailed documentation, see the [README](README.md) or 🇫🇷 [Lisez-moi](Lisez-moi.md).*
