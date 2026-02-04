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

- **Language**: Python 3.7+
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
├── i18n/                     # Toolkit translation management
└── locale/                   # Toolkit translations (.po/.mo)
```

---

## Contributing Translations

### For the Toolkit Itself

1. Edit files in `locale/<lang>/LC_MESSAGES/messages.po`
2. Run `python i18n/compile_po.py` to generate `.mo` files
3. Test the interface in your language

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

- **Langage** : Python 3.7+
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
├── i18n/                     # Gestion des traductions du toolkit
└── locale/                   # Traductions du toolkit (.po/.mo)
```

---

## Contribuer aux traductions

### Pour le toolkit lui-même

1. Éditez les fichiers dans `locale/<lang>/LC_MESSAGES/messages.po`
2. Lancez `python i18n/compile_po.py` pour générer les fichiers `.mo`
3. Testez l'interface dans votre langue

### Pour les plugins Lightroom

Suivez la documentation correspondant à votre niveau :
- [Contributeur simple](doc/fr/trad/01_Contributeur_simple.md)
- [Contributeur débrouillard](doc/fr/trad/02_Contributeur_debrouillard.md)
- [Contributeur pro](doc/fr/trad/03_Contributeur_pro.md)

---

## Des questions ?

N'hésitez pas à ouvrir une issue pour toute question. Il n'y a pas de questions bêtes !
