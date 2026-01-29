# 📦 PACKAGE DE CONFIGURATION CLAUDE CODE

Ce package contient tous les fichiers nécessaires pour configurer VSCode et Claude Code pour la refactorisation du projet Adobe_Lightroom_Translation_Plugins_Kit.

---

## 📂 Structure du package

```
claude_vscode_setup/
├── .claude/
│   └── refactor-instructions.md    ← Instructions détaillées pour Claude Code
├── .vscode/
│   └── settings.json               ← Configuration VSCode workspace
├── tests/
│   └── test_paths.py               ← Tests unitaires pour common/paths.py
├── GUIDE_SETTINGS_WORKSPACE.md     ← Guide d'utilisation settings.json
├── PROMPT_INITIAL_CLAUDE_CODE.md   ← Prompt de démarrage pour Claude Code
└── README.md                       ← Ce fichier
```

---

## 🚀 INSTALLATION RAPIDE

### Étape 1: Prérequis
```bash
# Installer VSCode (si pas déjà fait)
# Télécharger depuis: https://code.visualstudio.com/

# Installer plugin Claude Code dans VSCode
# 1. Ouvrir VSCode
# 2. Ctrl+Shift+X (Extensions)
# 3. Chercher "Claude Code"
# 4. Installer
```

### Étape 2: Copier les fichiers
```bash
# Naviguer vers le repo
cd /chemin/vers/Adobe_Lightroom_Translation_Plugins_Kit

# Copier les fichiers de configuration
cp -r /tmp/claude_vscode_setup/.claude ./
cp -r /tmp/claude_vscode_setup/.vscode ./
cp -r /tmp/claude_vscode_setup/tests ./

# Vérifier que les fichiers sont bien copiés
ls -la .claude/
ls -la .vscode/
ls -la tests/
```

### Étape 3: Ouvrir le projet
```bash
# Ouvrir VSCode à la racine du projet
code .
```

### Étape 4: Créer branche Git
```bash
# Créer branche dédiée pour refactorisation
git checkout -b refactor/i18n-kit-structure

# Vérifier status propre
git status
```

### Étape 5: Lancer Claude Code
1. Dans VSCode : `Ctrl+Shift+P`
2. Taper : "Claude: Open Chat"
3. Copier-coller le contenu de `PROMPT_INITIAL_CLAUDE_CODE.md`

---

## 📚 DOCUMENTATION

### 1. `.claude/refactor-instructions.md`
**Rôle** : Instructions complètes pour la refactorisation  
**Contenu** :
- Règles strictes de structure `__i18n_kit__`
- Plan de refactorisation par phases
- Exemples de code
- Checklist de progression

**Usage** : Claude Code lit ce fichier automatiquement (configuré dans `settings.json`)

---

### 2. `.vscode/settings.json`
**Rôle** : Configuration VSCode spécifique au projet  
**Contenu** :
- Configuration Claude Code (modèle, tokens, température)
- Configuration Python (linting, formatage)
- Exclusions de fichiers (`__pycache__`, `__i18n_kit__`)
- Configuration Git

**Usage** : Appliqué automatiquement quand le projet est ouvert dans VSCode

**Voir** : `GUIDE_SETTINGS_WORKSPACE.md` pour guide détaillé

---

### 3. `GUIDE_SETTINGS_WORKSPACE.md`
**Rôle** : Guide complet sur settings.json workspace  
**Contenu** :
- Différence User Settings vs Workspace Settings
- Où placer le fichier
- Installation étape par étape
- Configuration détaillée de chaque section
- Tests de validation
- Personnalisation
- Dépannage

**Usage** : Lire si première utilisation de workspace settings

---

### 4. `PROMPT_INITIAL_CLAUDE_CODE.md`
**Rôle** : Prompt de démarrage pour Claude Code  
**Contenu** :
- Contexte du projet
- Objectif de la refactorisation
- Contraintes strictes
- Tâche immédiate (Phase 1)
- Format de réponse attendu
- Checklist avant envoi
- Workflow avec Claude Code
- Prompts utiles pendant la refacto
- Gestion des erreurs

**Usage** : Copier-coller dans Claude Code pour démarrer

---

### 5. `tests/test_paths.py`
**Rôle** : Tests unitaires pour valider `common/paths.py`  
**Contenu** :
- 8 tests couvrant toutes les fonctions
- Tests de création de dossiers
- Tests de détection du dernier dossier
- Tests de normalisation de chemins
- Test de workflow complet

**Usage** :
```bash
# Exécuter les tests
python tests/test_paths.py

# Ou avec pytest (si installé)
pytest tests/test_paths.py -v
```

---

## 🎯 WORKFLOW COMPLET

### Phase 0: Préparation (AVANT Claude Code)
```bash
# 1. Copier fichiers de configuration
cp -r /tmp/claude_vscode_setup/{.claude,.vscode,tests} ./

# 2. Créer branche
git checkout -b refactor/i18n-kit-structure

# 3. Ouvrir VSCode
code .

# 4. Vérifier configuration
# Ouvrir Settings (Ctrl+,) → "Workspace" doit être visible
```

### Phase 1: Lancer Claude Code
```bash
# 1. Ouvrir Claude Code (Ctrl+Shift+P → "Claude: Open Chat")

# 2. Copier-coller PROMPT_INITIAL_CLAUDE_CODE.md

# 3. Claude génère common/paths.py

# 4. Tester
python tests/test_paths.py

# 5. Commit
git add common/ tests/
git commit -m "Phase 1: Create common/paths.py module"
```

### Phase 2-6: Refactorisation par outil
Répéter pour chaque outil :
```
1. Demander à Claude de refactoriser l'outil
2. Tester manuellement
3. Commit si OK
4. Passer au suivant
```

### Phase finale: Validation
```bash
# Test workflow complet
python LocalisationToolKit.py
# 1. Extractor
# 2. Applicator
# 3. TranslationManager

# Vérifier structure
tree <plugin>/__i18n_kit__/

# Merge dans main
git checkout main
git merge refactor/i18n-kit-structure
git push
```

---

## ⚙️ CONFIGURATION RECOMMANDÉE

### VSCode Extensions (optionnelles mais utiles)
```bash
# Python
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance

# Git
code --install-extension eamodio.gitlens

# Markdown
code --install-extension yzhang.markdown-all-in-one
```

### Python Packages
```bash
# Formatage
pip install black

# Linting
pip install pylint flake8

# Tests (optionnel)
pip install pytest
```

---

## 🐛 DÉPANNAGE

### Problème : "Claude Code ne trouve pas les instructions"
**Solution** :
```bash
# Vérifier que .claude/ existe à la racine
ls -la .claude/

# Vérifier contenu de settings.json
cat .vscode/settings.json | grep contextFiles
```

### Problème : "Settings.json ne s'applique pas"
**Solution** :
```bash
# Vérifier que VSCode est ouvert à la racine
pwd
# Devrait être : /chemin/vers/Adobe_Lightroom_Translation_Plugins_Kit

# Redémarrer VSCode
# Ctrl+Shift+P → "Developer: Reload Window"
```

### Problème : "Tests échouent"
**Solution** :
```bash
# Vérifier que common/ existe
ls -la common/

# Vérifier imports Python
python -c "from common.paths import get_i18n_kit_path; print('OK')"
```

### Problème : "Black not found"
**Solution** :
```bash
pip install black

# Ou désactiver formatage auto dans settings.json
# "editor.formatOnSave": false
```

---

## 📋 CHECKLIST FINALE

### Avant de commencer
- [ ] VSCode installé
- [ ] Plugin Claude Code installé
- [ ] Fichiers copiés (`.claude/`, `.vscode/`, `tests/`)
- [ ] VSCode ouvert **à la racine** du projet
- [ ] Branche Git créée : `refactor/i18n-kit-structure`
- [ ] Git status propre

### Configuration validée
- [ ] Settings.json visible dans VSCode Settings (Workspace)
- [ ] Python formatage fonctionne (test ligne longue)
- [ ] Claude Code voit `.claude/refactor-instructions.md`
- [ ] Recherche exclut `__i18n_kit__` et `__pycache__`

### Prêt à démarrer
- [ ] Prompt initial copié depuis `PROMPT_INITIAL_CLAUDE_CODE.md`
- [ ] Claude Code ouvert et prêt
- [ ] Instructions de refactorisation lues
- [ ] Tests `test_paths.py` prêts à être exécutés

---

## 🎓 CONSEILS

1. **Un commit = Une phase** : Ne pas mélanger plusieurs phases
2. **Tester avant commit** : Toujours valider manuellement
3. **Garder les anciennes versions** : Créer tags Git
4. **Documenter** : Mettre à jour CHANGELOG.md après chaque phase
5. **Demander à Claude** : En cas de doute, reformuler la question

---

## 📞 RESSOURCES

- **VSCode Workspace Settings** : https://code.visualstudio.com/docs/getstarted/settings#_workspace-settings
- **Claude Code** : https://marketplace.visualstudio.com/items?itemName=Anthropic.claude-code
- **Python Black** : https://black.readthedocs.io/
- **Git Branching** : https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging

---

## ✅ PRÊT À COMMENCER

Si toutes les étapes ci-dessus sont validées, tu es prêt à démarrer la refactorisation avec Claude Code !

**Prochaine étape** : Ouvrir Claude Code et envoyer le prompt initial.

Bon courage ! 🚀
