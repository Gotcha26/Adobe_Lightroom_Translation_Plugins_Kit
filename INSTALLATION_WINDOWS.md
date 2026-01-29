# 🪟 GUIDE INSTALLATION WINDOWS 11 - PAS À PAS VISUEL

**Pour débutants VSCode - Installation complète en 15 minutes**

---

## 📦 Ce que tu viens de télécharger

Tu as 6 fichiers organisés dans cette structure :

```
📁 (dossier téléchargé)/
├── 📄 README.md
├── 📄 GUIDE_SETTINGS_WORKSPACE.md
├── 📄 PROMPT_INITIAL_CLAUDE_CODE.md
├── 📄 INSTALLATION_WINDOWS.md          ← Tu lis ce fichier
├── 📁 .vscode/
│   └── 📄 settings.json                ← Configuration VSCode
├── 📁 .claude/
│   └── 📄 refactor-instructions.md     ← Instructions Claude Code
└── 📁 tests/
    └── 📄 test_paths.py                ← Tests unitaires
```

---

## 🎯 OBJECTIF

Copier ces fichiers dans ton projet GitHub pour que :
1. ✅ VSCode soit configuré automatiquement
2. ✅ Claude Code sache quoi faire
3. ✅ Tu aies les tests pour valider

---

## 📍 ÉTAPE 1 : Localiser ton projet GitHub

### Trouver le dossier du projet

**Méthode 1 - Via l'Explorateur Windows :**
1. Ouvrir l'Explorateur de fichiers (`Windows + E`)
2. Naviguer vers ton projet, exemple :
   ```
   D:\Gotcha\Documents\DIY\GitHub\Adobe_Lightroom_Translation_Plugins_Kit
   ```

**Méthode 2 - Via VSCode si déjà ouvert :**
1. Dans VSCode, menu **File → Open Folder**
2. Sélectionner ton dossier projet

**💡 Astuce** : Le dossier doit contenir :
- `LocalisationToolKit.py`
- Dossiers `1_Extractor/`, `2_Applicator/`, etc.

---

## 📍 ÉTAPE 2 : Copier les fichiers téléchargés

### Option A : Via l'Explorateur Windows (RECOMMANDÉ)

#### 1. Ouvrir deux fenêtres de l'Explorateur

**Fenêtre 1** - Dossier téléchargé :
```
C:\Users\TON_NOM\Downloads\claude_vscode_setup\
```

**Fenêtre 2** - Ton projet GitHub :
```
D:\Gotcha\Documents\DIY\GitHub\Adobe_Lightroom_Translation_Plugins_Kit\
```

#### 2. Copier TOUS les dossiers et fichiers

**🔴 IMPORTANT** : Copier les DOSSIERS, pas juste les fichiers dedans !

**Depuis le dossier téléchargé, sélectionner :**
- 📁 `.vscode` (dossier entier avec settings.json dedans)
- 📁 `.claude` (dossier entier avec refactor-instructions.md dedans)
- 📁 `tests` (dossier entier avec test_paths.py dedans)
- 📄 `README.md`
- 📄 `GUIDE_SETTINGS_WORKSPACE.md`
- 📄 `PROMPT_INITIAL_CLAUDE_CODE.md`
- 📄 `INSTALLATION_WINDOWS.md`

**Faire un clic droit → Copier**

**Dans le dossier du projet, faire un clic droit → Coller**

#### 3. Résultat attendu

Ton projet doit maintenant ressembler à ça :

```
📁 Adobe_Lightroom_Translation_Plugins_Kit/
├── 📁 .vscode/                    ← NOUVEAU
│   └── 📄 settings.json
├── 📁 .claude/                    ← NOUVEAU
│   └── 📄 refactor-instructions.md
├── 📁 tests/                      ← NOUVEAU
│   └── 📄 test_paths.py
├── 📄 README.md                   ← NOUVEAU ou mis à jour
├── 📄 GUIDE_SETTINGS_WORKSPACE.md ← NOUVEAU
├── 📄 PROMPT_INITIAL_CLAUDE_CODE.md ← NOUVEAU
├── 📄 INSTALLATION_WINDOWS.md     ← NOUVEAU
├── 📄 LocalisationToolKit.py      ← Déjà existant
├── 📁 1_Extractor/                ← Déjà existant
├── 📁 2_Applicator/               ← Déjà existant
└── ...
```

### Option B : Via PowerShell (pour les plus à l'aise)

```powershell
# Ouvrir PowerShell dans le dossier téléchargé
cd C:\Users\TON_NOM\Downloads\claude_vscode_setup

# Copier vers le projet
$destination = "D:\Gotcha\Documents\DIY\GitHub\Adobe_Lightroom_Translation_Plugins_Kit"

Copy-Item -Path ".vscode" -Destination $destination -Recurse -Force
Copy-Item -Path ".claude" -Destination $destination -Recurse -Force
Copy-Item -Path "tests" -Destination $destination -Recurse -Force
Copy-Item -Path "*.md" -Destination $destination
```

---

## 📍 ÉTAPE 3 : Afficher les dossiers cachés (IMPORTANT)

Windows cache les dossiers commençant par `.` (comme `.vscode` et `.claude`)

### Afficher les dossiers cachés

1. Ouvrir l'Explorateur Windows (`Windows + E`)
2. Aller dans le dossier du projet
3. Cliquer sur **Affichage** (en haut)
4. Cocher ☑️ **Éléments masqués**

Tu devrais maintenant voir `.vscode` et `.claude` en grisé.

**💡 Vérification** :
- Tu dois voir 3 dossiers avec un point : `.vscode`, `.claude`, `.git`

---

## 📍 ÉTAPE 4 : Ouvrir le projet dans VSCode

### Méthode 1 : Depuis VSCode

1. Ouvrir VSCode
2. Menu **File → Open Folder** (ou `Ctrl+K` puis `Ctrl+O`)
3. Naviguer vers ton projet
4. Sélectionner le dossier `Adobe_Lightroom_Translation_Plugins_Kit`
5. Cliquer **Sélectionner le dossier**

### Méthode 2 : Depuis l'Explorateur Windows

1. Naviguer vers le dossier du projet
2. Clic droit dans l'espace vide
3. Sélectionner **Ouvrir avec Code** (si disponible)

### Méthode 3 : Depuis PowerShell

```powershell
cd "D:\Gotcha\Documents\DIY\GitHub\Adobe_Lightroom_Translation_Plugins_Kit"
code .
```

**🔴 IMPORTANT** : VSCode doit être ouvert **À LA RACINE** du projet, pas dans un sous-dossier !

---

## 📍 ÉTAPE 5 : Vérifier que settings.json est bien détecté

### Vérification visuelle

Dans VSCode, tu devrais voir dans l'explorateur de fichiers (barre latérale gauche) :

```
📁 ADOBE_LIGHTROOM_TRANSLATION_PLUGINS_KIT
├── 📁 .vscode
│   └── 📄 settings.json        ← Doit être visible ici
├── 📁 .claude
├── 📁 tests
└── ...
```

**❌ Si tu ne vois pas `.vscode`** :
1. Dans VSCode, menu **File → Preferences → Settings** (ou `Ctrl+,`)
2. Chercher : `files.exclude`
3. Vérifier que `.vscode` n'est PAS dans la liste des exclusions

### Vérification configuration

1. Menu **File → Preferences → Settings** (ou `Ctrl+,`)
2. En haut, tu dois voir **2 onglets** :
   - 🔵 **User** (configuration globale)
   - 🟢 **Workspace** (configuration du projet) ← CELUI-CI !

3. Cliquer sur l'onglet **Workspace**
4. Chercher : `claude`

**✅ Si tu vois des paramètres comme** :
- `Claude: Model`
- `Claude: Max Tokens`
- `Claude: Temperature`

**→ settings.json est bien appliqué ! 🎉**

---

## 📍 ÉTAPE 6 : Installer le plugin Claude Code (si pas fait)

### Installation

1. Dans VSCode, cliquer sur l'icône **Extensions** dans la barre latérale gauche (ou `Ctrl+Shift+X`)
2. Dans la barre de recherche, taper : `Claude Code`
3. Cliquer sur **Install** sur l'extension "Claude Code" par Anthropic
4. Attendre la fin de l'installation (quelques secondes)

### Vérification

1. Une nouvelle icône **Claude** devrait apparaître dans la barre latérale gauche
2. Ou bien : `Ctrl+Shift+P` → taper "Claude" → tu dois voir des commandes comme :
   - `Claude: Open Chat`
   - `Claude: New Chat`

---

## 📍 ÉTAPE 7 : Créer la branche Git

**⚠️ IMPORTANT** : Avant de modifier le code, créer une branche séparée !

### Via VSCode (RECOMMANDÉ pour débutants)

1. En bas à gauche de VSCode, cliquer sur l'icône **Git** (branche)
2. Tu verras le nom de ta branche actuelle (probablement `main` ou `master`)
3. Cliquer sur ce nom
4. Dans le menu qui apparaît, sélectionner **Create new branch**
5. Entrer le nom : `refactor/i18n-kit-structure`
6. Appuyer sur **Entrée**

**✅ Vérification** : En bas à gauche, tu dois maintenant voir `refactor/i18n-kit-structure`

### Via PowerShell (alternative)

```powershell
cd "D:\Gotcha\Documents\DIY\GitHub\Adobe_Lightroom_Translation_Plugins_Kit"
git checkout -b refactor/i18n-kit-structure
```

---

## 📍 ÉTAPE 8 : Ouvrir Claude Code

### Lancer Claude Code

**Méthode 1** :
1. `Ctrl+Shift+P` (ouvre la palette de commandes)
2. Taper : `Claude: Open Chat`
3. Appuyer sur **Entrée**

**Méthode 2** :
- Cliquer sur l'icône **Claude** dans la barre latérale gauche

### Interface Claude Code

Tu devrais voir une fenêtre de chat avec :
- Une zone de texte en bas pour taper
- Un bouton "Send" ou icône ➤
- Éventuellement un message de bienvenue

---

## 📍 ÉTAPE 9 : Envoyer le prompt initial

### Copier le prompt

1. Dans VSCode, ouvrir le fichier : `PROMPT_INITIAL_CLAUDE_CODE.md`
2. Chercher la section avec le grand bloc de texte qui commence par :
   ```
   # CONTEXTE
   Je travaille sur Adobe_Lightroom_Translation_Plugins_Kit...
   ```
3. Sélectionner TOUT le texte de ce bloc (entre les ``` ```)
4. Copier (`Ctrl+C`)

### Coller dans Claude Code

1. Dans la fenêtre de chat Claude Code
2. Coller le texte (`Ctrl+V`)
3. Cliquer sur **Send** ou appuyer sur **Entrée**

### Ce qui va se passer

Claude Code va :
1. ✅ Lire automatiquement `.claude/refactor-instructions.md`
2. ✅ Analyser la structure du projet
3. ✅ Générer le code du module `common/paths.py`
4. ✅ Te donner les fichiers à créer

---

## 📍 ÉTAPE 10 : Créer les fichiers générés par Claude

### Créer le dossier common/

**Via VSCode** :
1. Dans l'explorateur de fichiers (barre latérale gauche)
2. Clic droit sur le nom du projet (tout en haut)
3. **New Folder**
4. Nommer : `common`

### Créer common/__init__.py

1. Clic droit sur le dossier `common`
2. **New File**
3. Nommer : `__init__.py`
4. Laisser le fichier vide (c'est normal)
5. Sauvegarder (`Ctrl+S`)

### Créer common/paths.py

1. Clic droit sur le dossier `common`
2. **New File**
3. Nommer : `paths.py`
4. **Copier le code que Claude Code t'a généré**
5. Coller dans le fichier
6. Sauvegarder (`Ctrl+S`)

---

## 📍 ÉTAPE 11 : Tester que ça fonctionne

### Tester le module paths.py

1. Dans VSCode, ouvrir le **Terminal intégré** :
   - Menu **Terminal → New Terminal** (ou `` Ctrl+` ``)

2. Taper cette commande :
   ```powershell
   python tests\test_paths.py
   ```

3. **Résultat attendu** :
   ```
   ================================================================================
   TESTS: common/paths.py
   ================================================================================
   
   TEST 1: get_i18n_kit_path
     ✓ Chemin correct: ...
   
   TEST 2: get_tool_output_path
     ✓ Dossier créé: ...
   
   ...
   
   RÉSULTATS: 8 réussis, 0 échoués
   ================================================================================
   ```

**✅ Si tous les tests passent** → Phase 1 terminée !

**❌ Si des tests échouent** :
1. Copier l'erreur
2. Retourner dans Claude Code
3. Coller l'erreur et demander : "Le test échoue avec cette erreur, peux-tu corriger ?"

---

## 📍 ÉTAPE 12 : Faire le premier commit

### Via VSCode (RECOMMANDÉ)

1. Cliquer sur l'icône **Source Control** dans la barre latérale gauche (icône de branche avec chiffre)
2. Tu devrais voir tous les nouveaux fichiers listés
3. Cliquer sur **+** à côté de "Changes" pour tout stager
4. En haut, dans la zone de texte "Message", taper :
   ```
   Phase 1: Create common/paths.py module
   ```
5. Cliquer sur **✓ Commit** (ou `Ctrl+Enter`)

### Via Terminal (alternative)

```powershell
git add .
git commit -m "Phase 1: Create common/paths.py module"
```

---

## ✅ CHECKLIST FINALE

### Configuration
- [ ] Fichiers copiés dans le projet
- [ ] `.vscode/settings.json` présent
- [ ] `.claude/refactor-instructions.md` présent
- [ ] `tests/test_paths.py` présent
- [ ] VSCode ouvert **à la racine** du projet
- [ ] Onglet "Workspace" visible dans Settings

### Git
- [ ] Branche `refactor/i18n-kit-structure` créée
- [ ] Branche active affichée en bas à gauche de VSCode

### Claude Code
- [ ] Plugin Claude Code installé
- [ ] Chat Claude ouvert
- [ ] Prompt initial envoyé
- [ ] Claude Code a répondu avec le code

### Tests
- [ ] Dossier `common/` créé
- [ ] Fichier `common/__init__.py` créé (vide)
- [ ] Fichier `common/paths.py` créé avec code de Claude
- [ ] Tests passent : `python tests\test_paths.py`
- [ ] Premier commit effectué

---

## 🆘 DÉPANNAGE FRÉQUENT

### "Je ne vois pas .vscode dans l'Explorateur Windows"
**Solution** : Activer "Éléments masqués" (Étape 3)

### "VSCode ne détecte pas settings.json"
**Solution** :
1. Vérifier que VSCode est ouvert **à la racine**
2. Menu **File → Reopen Folder**
3. Sélectionner de nouveau le dossier racine

### "Claude Code ne trouve pas refactor-instructions.md"
**Solution** :
1. Dans VSCode, vérifier que `.claude/refactor-instructions.md` existe
2. Menu **File → Preferences → Settings**
3. Chercher `claude.contextFiles`
4. Vérifier que `.claude/refactor-instructions.md` est dans la liste

### "Tests échouent avec 'ModuleNotFoundError: common'"
**Solution** :
```powershell
# Dans le terminal VSCode, vérifier que tu es à la racine
cd D:\Gotcha\Documents\DIY\GitHub\Adobe_Lightroom_Translation_Plugins_Kit

# Relancer les tests
python tests\test_paths.py
```

### "Git : fatal: not a git repository"
**Solution** :
```powershell
# Vérifier que tu es dans le bon dossier
cd D:\Gotcha\Documents\DIY\GitHub\Adobe_Lightroom_Translation_Plugins_Kit

# Vérifier que .git existe
dir .git
```

---

## 🎉 BRAVO !

Si tu es arrivé jusqu'ici et que tous les tests passent, tu as **réussi la Phase 1** !

**Prochaines étapes** :
1. ✅ Phase 1 terminée (module common/paths.py)
2. ➡️ **Phase 2** : Demander à Claude Code de refactoriser Extractor
3. **Phase 3** : Refactoriser Applicator
4. **Phase 4** : Refactoriser TranslationManager
5. **Phase 5** : Refactoriser Tools
6. **Phase 6** : Mettre à jour LocalisationToolKit.py

**Pour Phase 2**, retourner dans Claude Code et envoyer :
```
Phase 1 validée ✓
common/paths.py fonctionne correctement.

Passe maintenant à la Phase 2 : Refactoriser Extractor

Actions :
1. Modifier 1_Extractor/Extractor_main.py
2. Import common.paths
3. Remplacer logique output_dir par get_tool_output_path(plugin_path, "Extractor")
4. Mettre à jour Extractor_menu.py si nécessaire

Montre-moi les modifications ligne par ligne avec before/after.
```

**Bon courage pour la suite ! 🚀**
