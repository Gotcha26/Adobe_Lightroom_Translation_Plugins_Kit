# Contributing to Adobe Lightroom Translation Plugins Kit

*🇫🇷 [Version française ci-dessous](#contribuer-au-projet)*

Thank you for your interest in contributing to this project! Every contribution is appreciated, whether it's a bug report, a feature suggestion, or a pull request.

---

## How to Contribute

### Report a Bug

1. Check if the bug has already been reported in [Issues](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit/issues)
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the problem
   - Expected behavior vs actual behavior
   - Your environment (OS, Python version)

### Suggest an Improvement

Open an issue with the `enhancement` label, describing:
- The problem you're trying to solve
- Your proposed solution
- Potential alternatives considered

### Submit Code (Pull Request)

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/my-feature`
3. **Make your changes** following the conventions below
4. **Test** your modifications
5. **Commit** with a clear message: `git commit -m "Add: description of feature"`
6. **Push** your branch: `git push origin feature/my-feature`
7. **Open a Pull Request** with a detailed description

---

## Coding Conventions

### Code Style

- **Language**: Python 3.10+
- **Encoding**: UTF-8
- **Indentation**: 4 spaces (no tabs)
- **Max line length**: 100 characters (flexible)
- **Comments**: In French 🇫🇷 (project consistency) or English

### Commit Messages

Use clear prefixes:
- `Add:` New feature
- `Fix:` Bug fix
- `Update:` Improvement to existing feature
- `Refactor:` Code restructuring without behavior change
- `Doc:` Documentation only
- `i18n:` Translation-related changes

### Project Structure

```
Adobe_Lightroom_Translation_Plugins_Kit/
├── LocalizationToolKit.py    # Main entry point
├── core/                     # Shared modules
├── tools/                    # Individual tools
│   ├── extractor/
│   ├── applicator/
│   ├── translator/
│   └── toolbox/
├── doc/                      # User documentation
├── tests/                    # Test suite (+ tests/tools/extract_messages.py)
└── locale/                   # Toolkit translations (messages.pot, .po/.mo)
```

---

## Contributing Translations

### For the Toolkit Itself

The toolkit uses GNU gettext. French is the source language (the `msgid`s);
`locale/en/LC_MESSAGES/messages.po` holds the English catalog. The GNU gettext
tools (`xgettext`, `msgmerge`, `msgfmt`) are required, there is no helper script.

1. After changing a string wrapped in `_()` / `ngettext()`, regenerate the template
   from the repository root:

   ```bash
   xgettext --language=Python --keyword=_ --keyword=ngettext:1,2 --from-code=UTF-8 \
            --package-name=LocalizationToolKit --package-version=<version> \
            -o locale/messages.pot LocalizationToolKit.py $(git ls-files 'core/*.py' 'tools/*.py')
   ```

2. Merge the template into each language catalog:

   ```bash
   msgmerge --update locale/en/LC_MESSAGES/messages.po locale/messages.pot
   ```

3. Translate the new or fuzzy entries in `locale/<lang>/LC_MESSAGES/messages.po`
4. Compile the binary catalog (the `-c` flag checks placeholders and format strings):

   ```bash
   cd locale/en/LC_MESSAGES && msgfmt -c -o messages.mo messages.po
   ```

5. Run `pytest`: `tests/test_i18n_catalog.py` fails if a string used in the code is
   missing from the `.po` or if a `msgstr` is empty. Without GNU gettext installed,
   `python tests/tools/extract_messages.py LocalizationToolKit.py core tools` lists
   the strings found in the code using only the standard library.
6. Test the interface in your language

### For Lightroom Plugins

Follow the documentation for your contributor level:
- [Simple Contributor](doc/en/trad/01_Simple_Contributor.md)
- [Resourceful Contributor](doc/en/trad/02_Resourceful_Contributor.md)
- [Professional Contributor](doc/en/trad/03_Professional_Contributor.md)

---

## Questions?

Feel free to open an issue for any question. There are no stupid questions!

---

---

# 🇫🇷 Contribuer au projet

Merci de votre intérêt pour ce projet ! Toute contribution est appréciée, qu'il s'agisse d'un rapport de bug, d'une suggestion d'amélioration ou d'une pull request.

---

## Comment contribuer

### Signaler un bug

1. Vérifiez que le bug n'a pas déjà été signalé dans les [Issues](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit/issues)
2. Sinon, créez une nouvelle issue avec :
   - Un titre clair et descriptif
   - Les étapes pour reproduire le problème
   - Le comportement attendu vs le comportement observé
   - Votre environnement (OS, version Python)

### Proposer une amélioration

Ouvrez une issue avec le label `enhancement`, décrivant :
- Le problème que vous cherchez à résoudre
- Votre solution proposée
- Les alternatives éventuellement envisagées

### Soumettre du code (Pull Request)

1. **Forkez** le dépôt
2. **Créez une branche** pour votre fonctionnalité : `git checkout -b feature/ma-fonctionnalite`
3. **Effectuez vos modifications** en respectant les conventions ci-dessous
4. **Testez** vos modifications
5. **Committez** avec un message clair : `git commit -m "Add: description de la fonctionnalité"`
6. **Pushez** votre branche : `git push origin feature/ma-fonctionnalite`
7. **Ouvrez une Pull Request** avec une description détaillée

---

## Conventions de code

### Style de code

- **Langage** : Python 3.10+
- **Encodage** : UTF-8
- **Indentation** : 4 espaces (pas de tabulations)
- **Longueur de ligne max** : 100 caractères (flexible)
- **Commentaires** : En français 🇫🇷 (cohérence du projet) ou en anglais

### Messages de commit

Utilisez des préfixes clairs :
- `Add:` Nouvelle fonctionnalité
- `Fix:` Correction de bug
- `Update:` Amélioration d'une fonctionnalité existante
- `Refactor:` Restructuration du code sans changement de comportement
- `Doc:` Documentation uniquement
- `i18n:` Changements liés aux traductions

### Structure du projet

```
Adobe_Lightroom_Translation_Plugins_Kit/
├── LocalizationToolKit.py    # Point d'entrée principal
├── core/                     # Modules partagés
├── tools/                    # Outils individuels
│   ├── extractor/
│   ├── applicator/
│   ├── translator/
│   └── toolbox/
├── doc/                      # Documentation utilisateur
├── tests/                    # Suite de tests (+ tests/tools/extract_messages.py)
└── locale/                   # Traductions du toolkit (messages.pot, .po/.mo)
```

---

## Contribuer aux traductions

### Pour le toolkit lui-même

Le toolkit utilise GNU gettext. Le français est la langue source (les `msgid`) ;
`locale/en/LC_MESSAGES/messages.po` contient le catalogue anglais. Les outils GNU
gettext (`xgettext`, `msgmerge`, `msgfmt`) sont nécessaires, il n'y a pas de script d'aide.

1. Après modification d'une chaîne passée à `_()` / `ngettext()`, régénérez le modèle
   depuis la racine du dépôt :

   ```bash
   xgettext --language=Python --keyword=_ --keyword=ngettext:1,2 --from-code=UTF-8 \
            --package-name=LocalizationToolKit --package-version=<version> \
            -o locale/messages.pot LocalizationToolKit.py $(git ls-files 'core/*.py' 'tools/*.py')
   ```

2. Fusionnez le modèle dans chaque catalogue de langue :

   ```bash
   msgmerge --update locale/en/LC_MESSAGES/messages.po locale/messages.pot
   ```

3. Traduisez les entrées nouvelles ou approximatives (fuzzy) de `locale/<lang>/LC_MESSAGES/messages.po`
4. Compilez le catalogue binaire (l'option `-c` vérifie les placeholders et formats) :

   ```bash
   cd locale/en/LC_MESSAGES && msgfmt -c -o messages.mo messages.po
   ```

5. Lancez `pytest` : `tests/test_i18n_catalog.py` échoue si une chaîne du code est absente
   du `.po` ou si un `msgstr` est vide. Sans GNU gettext,
   `python tests/tools/extract_messages.py LocalizationToolKit.py core tools` liste les
   chaînes trouvées dans le code avec la seule bibliothèque standard.
6. Testez l'interface dans votre langue

### Pour les plugins Lightroom

Suivez la documentation correspondant à votre niveau :
- [Contributeur simple](doc/fr/trad/01_Contributeur_simple.md)
- [Contributeur débrouillard](doc/fr/trad/02_Contributeur_debrouillard.md)
- [Contributeur pro](doc/fr/trad/03_Contributeur_pro.md)

---

## Des questions ?

N'hésitez pas à ouvrir une issue pour toute question. Il n'y a pas de questions bêtes !
