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
- Backups made without a session now go to `<plugin>/<temp_dir>/backups/`; a `<plugin>/backups/` folder left by earlier versions is no longer used and can be deleted (#36)
- Configuration menu: when `config.local.json` is unreadable (or cannot be written), the error was followed by a green success message ("Plugin configured…"). `ConfigManager.set()` now reports whether the value was saved, and the menu then says the value applies to the current session only (#35)
- INJECT/SYNC "backups created" messages now give the number of `.bak` files actually created by that operation and the folder really used, relative to the plugin (#36)
- Extractor: non-simple Lua escapes (`\ddd`, `\xXX`, `\u{...}`, `\z`) were kept as-is when unescaped, then their `\` was doubled when re-escaped, so `"Caf\195\169"` became `LOC "…=Caf\\195\\169"`. Decimal byte escapes forming valid UTF-8 are now decoded to real text (`Café`); any other sequence comes back verbatim, and a string that keeps such a sequence is left hard-coded instead of being extracted (#34)
- Extractor: `\xXX` and `\u{...}` escapes are not decoded. Lightroom runs Lua 5.1, where they are unknown escapes (`"\x41"` displays `x41`), so decoding them would change the default text of the `LOC`; a string holding them is left hard-coded (#34)
- Applicator (and the Extractor's `replaced_line` preview and multi-line line lookup) searched `"original_text"` with a raw `find`, which could match inside another literal ending with `\"X\""` or across two literals. The search now only matches whole literals of the line (#34)
- Extractor: a line holding both a log call and a UI label (`log:info("x"); title = "Export"`) was skipped entirely. Only the arguments of the log call are now ignored and the rest of the line is analysed; a log call is no longer detected inside a string (`title = "See log(s)"`). `replacements.json` members carry the literal's `column`, so the Applicator replaces the UI literal even when the log call holds the same text (#34)
- Extractor: a log call taking a table (`log:info{ title = "x" }`) was not recognised as a log call, so its literals were extracted; its argument, up to the matching `}`, is now ignored like a parenthesised one (#34)
- Extractor: the line closing a block comment (`]]`, `]==]`) was skipped entirely, as was a line starting with a block comment closed on the same line (`--[[ x ]] title = "X"`). The code after the closing delimiter is now analysed; strings in a comment that follows the code on the same line (`-- …` or `--[[ …`) are no longer extracted (#34)
- Extractor: a block comment opened and closed in the middle of a line (`f{ title = "A" --[[c]], tooltip = "Export file" }`, `title = --[[ old ]] "Export"`) no longer ends the code of the line: it is skipped and the code after it is analysed; only a block comment still open at the end of the line, or a line comment, ends it (#34)
- Extractor report mixed the escaped form (searched text, original) and the real text (base, value). It now shows a single form, the real text with control characters made visible (`\n`, `\t`); only the key=value section and the Lua code shown as such (line, replacement) stay escaped (#34)
- AUTOSYNC: the dry-run report no longer gets overwritten by the real run's report; they are now written side by side in the session as `application_report_dry_run.txt` and `application_report.txt` (#37)
- AUTOSYNC: declining the confirmation (or closed stdin) now removes the sessions created by that run (Extractor, Applicator, Translator, including the `_original_TranslatedStrings_xx.txt` copy) and lists what was cleaned; sessions that existed before are never touched (#37)
- `process_plugin_directory(..., silent=True)` printed messages when `extraction_dir` was auto-detected or invalid; it now prints nothing and records those errors in `report.errors` (#37)
- AUTOSYNC tests now cover the accepted-confirmation path (Lua modified, both reports present) (#37)
- Launcher: `--yes` / `--dry-run` were silently ignored by commands that do not support them. Each command now declares the options it handles (`extract`: `--yes`; `apply`: `--dry-run`, `--yes`; `autosync`: `--yes`; others: none) and any other option is refused with an error and exit code 2 (#37)
- Applicator menu: re-selecting the current extraction folder was treated as a cancellation and skipped the `replacements.json` check; it is now validated and confirmed like any other selection (#37)
- Translator EXTRACT menu: cancelling the folder selection is now reported (message and pause) before going back to the menu (#37)
- `clear_screen` is now only run on a terminal everywhere (launcher, Extractor, Applicator, Translator menus), through a single `core.cli.clear_screen` also used by the Toolbox (#37)
- COMPARE no longer hard-codes "EN": the CHANGELOG title, value lines, menu texts and docstrings use the configured reference language code (#37)
- INJECT: `parse_translate_file` detected the target line with a hard-coded `→` and `split`, so a reference value starting with `→` (`[EN]  → Next`) was read as a translation. The target line is now recognised from `[XX] →` at the start of the line, using `TRANSLATE_ARROW` (#39)
- `ngettext` fallback for the source language (French) now uses the French rule (singular for 0 and 1, plural for n > 1) instead of `n == 1` (#39)

### Added
- Tests for SYNC from the menu, the `inject` CLI (`from_ref`), existing markers surviving INJECT, `parse_translate_file` guards (target equal to the reference, `[XX] →` without trailing space), malformed `.i18n_kit.json`, INJECT backup content, `isolated_config` covering `ConfigManager`, and the `is_technical_string("error\n")` behaviour (#39)

### Changed
- `--default-plugin` and `--plugin-path` argparse definitions shared by the Extractor, Applicator and Translator moved to `core.cli` (same names, help and defaults) (#37)
- Embedded help pages (`tools/*/__doc__`) now use the current module names and `python -m tools.<tool>.main` commands, present the update file as `UPDATE_<ref>.json`, document the Applicator `--yes` option, its two reports and the fallback backup folder, and no longer contain broken relative links; `[1.1.0]` gains an Upgrade note on the `Colon` key suffix (#38)

---

## [1.1.0] - 2026-11-08

> **Upgrade note:** `replacements.json` files produced by an Extractor older than 1.1.0
> must be regenerated. Escape handling changed (escaped quotes, block comments), so
> positions and texts recorded by earlier versions no longer match.
>
> **Upgrade note (`Colon` key suffix):** `generate_loc_key` now appends a `Colon` suffix to the
> key of any string ending with `:` (as it already does with `Ellipsis` for `...` and `Question`
> for `?`). `"Name:"` now gets `$$$/<Category>/NameColon` instead of sharing `$$$/<Category>/Name`
> with `"Name"` (whichever came second got a numeric `2`). Re-extracting a plugin extracted with
> an older version therefore changes these keys, and the translations recorded under the old
> keys in `TranslatedStrings_xx.txt` become orphaned. To upgrade: re-extract with the Extractor,
> then run COMPARE (old reference file vs new one) and
> SYNC for each language: the old keys appear as removed and the `...Colon` keys as added, and
> the added ones must be translated again (the old value can be copied over).

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
