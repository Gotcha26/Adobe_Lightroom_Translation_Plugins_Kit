# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed
- `ConfigManager` no longer overwrites an unreadable `config.local.json` (invalid JSON, non-object root, encoding or I/O error): the change is kept in memory, an error names the file, and the file on disk is left untouched (#35)
- Toolbox (restore backup, delete temp dir) recognised Applicator sessions by substring: any folder whose name contained "applicator" was listed as a session. Sessions are now matched on the exact names created by `core.paths` (`2_Applicator`/`Applicator` then `YYYYMMDD_HHMMSS`), through a single `find_session_dirs` (#36)
- Fallback backups (no session, no plugin path) went to `backups/` next to the target file, i.e. at the plugin root for `TranslatedStrings_xx.txt`; they now go under `<temp_dir>/backups`. Applicator no longer drops `.bak` files next to the source file either (#36)
- INJECT/SYNC "backups created" messages now give the number of `.bak` files actually created by that operation and the folder really used, relative to the plugin (#36)
- Extractor: non-simple Lua escapes (`\ddd`, `\xXX`, `\u{...}`, `\z`) were kept as-is when unescaped, then their `\` was doubled when re-escaped, so `"Caf\195\169"` became `LOC "…=Caf\\195\\169"`. Byte escapes forming valid UTF-8 and valid `\u{...}` are now decoded to real text (`Café`); any other sequence comes back verbatim, and a string that keeps such a sequence is left hard-coded instead of being extracted (#34)
- Applicator (and the Extractor's `replaced_line` preview and multi-line line lookup) searched `"original_text"` with a raw `find`, which could match inside another literal ending with `\"X\""` or across two literals. The search now only matches whole literals of the line (#34)
- Extractor: a line holding both a log call and a UI label (`log:info("x"); title = "Export"`) was skipped entirely. Only the arguments of the log call are now ignored and the rest of the line is analysed; a log call is no longer detected inside a string (`title = "See log(s)"`). `replacements.json` members carry the literal's `column`, so the Applicator replaces the UI literal even when the log call holds the same text (#34)
- Extractor: the line closing a block comment (`]]`, `]==]`) was skipped entirely, as was a line starting with a block comment closed on the same line (`--[[ x ]] title = "X"`). The code after the closing delimiter is now analysed; strings in a comment that follows the code on the same line (`-- …` or `--[[ …`) are no longer extracted (#34)
- Extractor report mixed the escaped form (searched text, original) and the real text (base, value). It now shows a single form, the real text with control characters made visible (`\n`, `\t`); only the key=value section and the Lua code shown as such (line, replacement) stay escaped (#34)

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
- `ConfigManager` wrote settings into the versioned `config.json`: they now always go to `config.local.json` (created if absent); personal path and Piwigo prefix removed from the defaults (#18)
- COMPARE ignored the configured reference language (`UPDATE_en.json` / `TranslatedStrings_en.txt` were hard-coded) (#19)
- Surgical update of TranslatedStrings: "removed" keys were kept, regexes were not escaped, sections were inconsistent (#20)
- `TRANSLATE_xx.txt` format: translatable markers and parser are no longer hard-coded to `[EN]` / `[EN APRÈS]`, so INJECT works with any UI language or reference language; a raw `"` typed in a translation is escaped instead of producing an unreadable line (#21)
- Extractor: escaped quotes `\"` were split incorrectly and `--[[ ]]` block comments were not ignored (#22)
- Language detection no longer relies on the deprecated `locale.getdefaultlocale()` and no longer silently falls back to EN (#23)
- `pyproject.toml` declared Python >= 3.7 while the code requires 3.10; the non-functional pip entry point was removed (#24)
- Wrong and contradictory references in help texts, docstrings, `epilog`s and the generated `CHANGELOG.txt` (`Translator_main.py`, `common.paths`...), contradictory version numbers, and missing i18n scripts in `CONTRIBUTING.md` (#31)
- Robustness: plugin-relative paths computed with `relpath` (case-insensitive on Windows) instead of `str.replace`, exact tool-folder matching merging old and prefixed folders, git repository detected at any depth above the plugin, non-UTF-8 `.lua` files reported by the Applicator instead of aborting the run, invalid config JSON reported, a single shared color instance honouring a failed `SetConsoleMode`, no ANSI animation or screen clearing outside a terminal, `"Export:"` and `"Export"` no longer share a LOC key, SYNC markers re-read through fixed prefixes, and `LocalizationToolKit.py --help` (#32)

### Changed
- AUTOSYNC uses the configured prefix instead of `$$$/Piwigo`, asks for confirmation before the real Applicator run, creates a single backup session whose `.bak` files keep the original content, and names the offending files when the Applicator fails (#25)
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
