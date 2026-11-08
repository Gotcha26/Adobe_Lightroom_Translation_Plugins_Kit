# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-11-08

> **Upgrade note:** `replacements.json` files produced by an Extractor older than 1.1.0
> must be regenerated. Escape handling changed (escaped quotes, block comments), so
> positions and texts recorded by earlier versions no longer match.

### Fixed
- **Critical**: AUTOSYNC was inoperative because file names were corrupted by the automatic i18n pass (#11)
- **Critical**: Applicator generated invalid Lua `_(" ")` for strings with leading/trailing spaces (#12)
- **Critical**: ADD LANGUAGE raised `NameError` (missing `config_loader` imports) (#13)
- SYNC (menu) raised `NameError` on `get_update_filename` (#14)
- CLI `inject` raised `KeyError` `from_en` (the function returns `from_ref`) (#15)
- Residues of the automatic i18n pass: default suffix `"_("`, `[N_(]` prompts, corrupted regexes (#16)
- Backups were flattened by file name: collisions, and restoration to the plugin root for `.lua` files in subfolders (#17)
- `ConfigManager.save()` wrote `config.local.json` overrides into the versioned `config.json`; personal path removed from the defaults (#18)
- COMPARE ignored the configured reference language (`UPDATE_en.json` / `TranslatedStrings_en.txt` were hard-coded) (#19)
- Surgical update of TranslatedStrings: "removed" keys were kept, regexes were not escaped, sections were inconsistent (#20)
- `TRANSLATE_xx.txt` format: translatable markers and parser are no longer hard-coded to `[EN]` / `[EN APRÈS]`, so INJECT works with any UI language or reference language (#21)
- Extractor: escaped quotes `\"` were split incorrectly and `--[[ ]]` block comments were not ignored (#22)
- Language detection no longer relies on the deprecated `locale.getdefaultlocale()` and no longer silently falls back to EN (#23)
- `pyproject.toml` declared Python >= 3.7 while the code requires 3.10; the non-functional pip entry point was removed (#24)
- Wrong and contradictory references in help texts, docstrings, `epilog`s and the generated `CHANGELOG.txt` (`Translator_main.py`, `common.paths`...), contradictory version numbers, and missing i18n scripts in `CONTRIBUTING.md` (#31)
- Path handling by `str.replace`, loose folder matching, Applicator encoding, repeated `Colors()` instances and duplicated git blocks (#32)

### Changed
- AUTOSYNC uses the configured prefix instead of `$$$/Piwigo`, asks for confirmation before the real Applicator run, and creates a single backup session (#25)
- Unified CLI: `apply` no longer forces `--dry-run`, `install` / `addlang` / `autosync` sub-commands added, blocking prompts avoided in scripted mode (#26)
- Piwigo-specific rules moved out of the generic Extractor into an optional per-plugin `.i18n_kit.json` (#27)
- Outputs are no longer written into the toolkit tree, `.bak` files no longer land at the plugin root, and the Translator output folder is consistent with the other tools (#28)
- Single version source: `core.__version__` (`1.1.0`) is used by the banners; `pyproject.toml` and the `.po` header carry the same value, checked by a test (#31)
- Extractor menu displays the real default output path (configured temporary folder and tool folder name) (#31)
- `CONTRIBUTING.md` describes the real gettext workflow (`xgettext`, `msgmerge`, `msgfmt`, `tests/tools/extract_messages.py`); Python 3.10+ stated everywhere; the unused `last_used` key removed from `config.json` and the docs (#24, #31)
- Dead code removed: `paths._extract_tool_prefix`, `engine.print_summary`, `engine._is_already_localized`, `config.UI_PATTERNS`, the flat-structure fallback of the launcher, `models.StringMember` and `models.ExtractedLine` (#31)

### Added
- Complete English catalog (`locale/en`), previously untranslated strings translated, real `ngettext` plural support (#29)
- Test suite on Lua fixtures, static analysis with `ruff` and CI workflow (#30)
- Version consistency and stale-reference tests (`tests/test_version.py`) (#31)

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
- Python 3.10+
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
