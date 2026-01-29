# 📘 GUIDE: Utilisation settings.json (workspace)

## 🎯 C'est quoi un settings.json workspace ?

VSCode a **2 niveaux** de configuration :

1. **GLOBAL** (User Settings) → S'applique à **tous** les projets
   - Chemin : `~/.config/Code/User/settings.json` (Linux/Mac)
   - Chemin : `%APPDATA%\Code\User\settings.json` (Windows)

2. **WORKSPACE** (Workspace Settings) → S'applique **uniquement** au projet actuel
   - Chemin : `<projet>/.vscode/settings.json` ✅ **C'est celui-ci !**

---

## 📂 Où placer le fichier ?

```
Adobe_Lightroom_Translation_Plugins_Kit/   ← Racine du dépôt GitHub
├── .vscode/
│   └── settings.json                      ← ICI !
├── .claude/
│   └── refactor-instructions.md
├── common/
│   ├── __init__.py
│   └── paths.py
├── 1_Extractor/
├── 2_Applicator/
├── 3_TranslationManager/
├── LocalisationToolKit.py
└── README.md
```

---

## 🚀 Installation étape par étape

### Étape 1: Ouvrir le projet dans VSCode

```bash
# Naviguer vers le repo
cd /chemin/vers/Adobe_Lightroom_Translation_Plugins_Kit

# Ouvrir VSCode dans ce dossier
code .
```

**Important** : VSCode doit être ouvert **à la racine du dépôt**, pas dans un sous-dossier !

---

### Étape 2: Créer le dossier .vscode

**Option A - Via VSCode** :
1. Clic droit dans l'explorateur de fichiers (barre latérale gauche)
2. "New Folder"
3. Nommer : `.vscode`

**Option B - Via terminal** :
```bash
mkdir .vscode
```

---

### Étape 3: Créer settings.json

**Option A - Via VSCode** :
1. Clic droit sur `.vscode/`
2. "New File"
3. Nommer : `settings.json`
4. Copier-coller le contenu du fichier fourni

**Option B - Via terminal** :
```bash
# Copier le fichier fourni
cp /tmp/claude_vscode_setup/.vscode/settings.json .vscode/settings.json
```

---

### Étape 4: Vérifier que c'est bien appliqué

1. Ouvrir un fichier Python (ex: `LocalisationToolKit.py`)
2. Menu : **File → Preferences → Settings** (ou `Ctrl+,`)
3. En haut à droite, cliquer sur l'icône `{}` (Open Settings JSON)
4. Vous devriez voir : **Workspace Settings** et **User Settings**

**Vérification** :
```json
// Si vous voyez ceci en haut, c'est OK :
// Workspace Settings: Adobe_Lightroom_Translation_Plugins_Kit
```

---

## 🔧 Configuration détaillée

### Section 1: Claude Code

```json
"claude.model": "claude-sonnet-4-20250514",
```
- **Modèle IA** utilisé par Claude Code
- `sonnet-4` = Rapide et efficace pour le code
- Alternative : `opus-4` (plus puissant mais plus lent)

```json
"claude.maxTokens": 8000,
```
- **Longueur maximale** des réponses
- 8000 = Peut générer ~6000 lignes de code
- Augmenter si besoin de fichiers très longs

```json
"claude.temperature": 0.3,
```
- **Créativité** du modèle (0.0 à 1.0)
- 0.0 = Déterministe, répète toujours la même chose
- 0.3 = **Recommandé pour code** (précis mais adaptable)
- 1.0 = Créatif (risque d'inventer des APIs)

```json
"claude.contextFiles": [
  ".claude/refactor-instructions.md",
  "README.md",
  "common/paths.py"
],
```
- **Fichiers toujours inclus** dans le contexte de Claude
- Claude les lira automatiquement avant de répondre
- Utile pour garder les instructions de refactorisation visibles

---

### Section 2: Python

```json
"python.linting.enabled": true,
"python.linting.pylintEnabled": true,
```
- Active le **linter** Python (détection d'erreurs)
- Souligne les problèmes en rouge/jaune

```json
"python.formatting.provider": "black",
"python.formatting.blackArgs": ["--line-length=88"],
```
- Utilise **Black** pour formater le code automatiquement
- 88 caractères max par ligne (standard Python)

```json
"[python]": {
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  }
}
```
- **Formatage automatique** lors de la sauvegarde (`Ctrl+S`)
- Organise les imports automatiquement

---

### Section 3: Exclusions de fichiers

```json
"files.watcherExclude": {
  "**/__pycache__": true,
  "**/*.pyc": true,
  "**/__i18n_kit__": true
}
```
- **Ne surveille PAS** ces dossiers/fichiers
- Améliore les performances VSCode
- `__i18n_kit__` contient les sorties (pas besoin de watch)

```json
"search.exclude": {
  "**/__i18n_kit__": true
}
```
- **Exclut de la recherche** (`Ctrl+Shift+F`)
- Évite de trouver du texte dans les sorties générées

---

### Section 4: Git

```json
"git.enableSmartCommit": true,
"git.autofetch": true,
```
- Commits intelligents (détecte les fichiers à stager)
- Récupère automatiquement les changements distants

---

## 🧪 Tester la configuration

### Test 1: Python formatage
1. Ouvrir `LocalisationToolKit.py`
2. Ajouter une ligne très longue (>88 caractères)
3. Sauvegarder (`Ctrl+S`)
4. **Résultat attendu** : La ligne est coupée automatiquement

### Test 2: Claude Code contexte
1. Ouvrir Claude Code (`Ctrl+Shift+P` → "Claude: Open Chat")
2. Taper : "Lis les instructions de refactorisation"
3. **Résultat attendu** : Claude cite `.claude/refactor-instructions.md`

### Test 3: Exclusions
1. Ouvrir recherche (`Ctrl+Shift+F`)
2. Chercher : `TranslatedStrings`
3. **Résultat attendu** : Ne trouve PAS les fichiers dans `__i18n_kit__`

---

## ⚙️ Personnalisation

### Changer le modèle Claude

```json
// Pour plus de puissance (mais plus lent)
"claude.model": "claude-opus-4-20250514",

// Pour plus de vitesse (mais moins précis)
"claude.model": "claude-haiku-4-20250514",
```

### Désactiver formatage auto

```json
"[python]": {
  "editor.formatOnSave": false  // ← Changer ici
}
```

### Ajouter fichiers au contexte Claude

```json
"claude.contextFiles": [
  ".claude/refactor-instructions.md",
  "README.md",
  "common/paths.py",
  "1_Extractor/Extractor_main.py"  // ← Ajouter ici
],
```

---

## 🐛 Dépannage

### "Claude Code ne trouve pas les instructions"
**Cause** : Mauvais chemin dans `contextFiles`  
**Solution** :
```json
// Vérifier que le chemin existe
"claude.contextFiles": [
  ".claude/refactor-instructions.md"  // ← Relatif à la racine
],
```

### "Black not found"
**Cause** : Black pas installé  
**Solution** :
```bash
pip install black
```

### "Settings.json ne s'applique pas"
**Cause** : Fichier dans mauvais dossier  
**Solution** : Vérifier que le chemin est bien :
```
<racine_projet>/.vscode/settings.json
```

### "Workspace Settings vs User Settings conflit"
**Priorité** : Workspace > User  
**Solution** : Workspace settings **écrase** User settings

---

## 📋 Checklist finale

- [ ] VSCode ouvert **à la racine du dépôt**
- [ ] Dossier `.vscode/` créé à la racine
- [ ] Fichier `.vscode/settings.json` créé
- [ ] Contenu copié depuis le fichier fourni
- [ ] Python formatage fonctionne (test ligne longue)
- [ ] Claude Code voit les `contextFiles`
- [ ] Recherche exclut `__i18n_kit__`

---

## 🚀 Prochaines étapes

1. ✅ Installer plugin VSCode "Claude Code" (si pas déjà fait)
2. ✅ Créer dossier `.claude/` et `refactor-instructions.md`
3. ✅ Créer branche Git : `git checkout -b refactor/i18n-kit-structure`
4. ✅ Ouvrir Claude Code et commencer la refactorisation

---

## 📚 Ressources

- [VSCode Workspace Settings](https://code.visualstudio.com/docs/getstarted/settings#_workspace-settings)
- [Claude Code Documentation](https://marketplace.visualstudio.com/items?itemName=Anthropic.claude-code)
- [Python Black Formatter](https://black.readthedocs.io/)
