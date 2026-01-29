# 🤖 PROMPT INITIAL POUR CLAUDE CODE

**Copier-coller ce prompt dans Claude Code pour démarrer la refactorisation**

---

```
# CONTEXTE
Je travaille sur Adobe_Lightroom_Translation_Plugins_Kit, un ensemble d'outils Python pour gérer la localisation de plugins Adobe Lightroom Classic. Le projet nécessite une refactorisation majeure de la structure de sortie des fichiers.

# OBJECTIF
Implémenter une nouvelle architecture où tous les outils écrivent leurs sorties dans :
<plugin_lightroom>/__i18n_kit__/<Outil>/<timestamp_YYYYMMDD_HHMMSS>/

# CONTRAINTES STRICTES
1. SDK Adobe Lightroom respecté (format LOC "$$$/Key=Default")
2. Scripts indépendants (chaque outil doit fonctionner standalone)
3. Compatibilité Windows/Linux (utiliser os.path.normpath)
4. Backups .bak systématiques avant modification
5. Timestamps cohérents : format YYYYMMDD_HHMMSS (15 caractères)
6. AUCUN fichier ne doit être créé dans le repo Adobe_Lightroom_Translation_Plugins_Kit

# FICHIERS DE RÉFÉRENCE
Avant de commencer, lis ces fichiers pour comprendre le contexte :
1. .claude/refactor-instructions.md (instructions complètes)
2. README.md (vue d'ensemble du projet)
3. LocalisationToolKit.py (orchestrateur actuel)

# TÂCHE IMMÉDIATE
Phase 1 : Créer le module commun de gestion des chemins

Actions :
1. Créer dossier common/ à la racine
2. Créer common/__init__.py (vide)
3. Créer common/paths.py avec les fonctions :
   - get_i18n_kit_path(plugin_path) → str
   - get_tool_output_path(plugin_path, tool_name, create=True) → str
   - find_latest_tool_output(plugin_path, tool_name) → str | None
   - normalize_path(path) → str

4. Créer tests/test_paths.py pour valider le module

Code à générer pour common/paths.py :
- Fonction get_i18n_kit_path : retourne <plugin>/__i18n_kit__
- Fonction get_tool_output_path : crée <plugin>/__i18n_kit__/<tool>/<timestamp>/
- Fonction find_latest_tool_output : trouve dernier dossier timestamp d'un outil
- Fonction normalize_path : normalise chemins Windows/Linux

# FORMAT DE RÉPONSE ATTENDU
1. Montre-moi le contenu complet de common/paths.py
2. Montre-moi le contenu complet de tests/test_paths.py
3. Explique comment tester manuellement (commandes bash)
4. Liste les prochaines étapes (Phase 2)

# QUESTIONS À POSER
Si tu as besoin de clarifications sur :
- Structure actuelle des outils (Extractor, Applicator, etc.)
- Format des fichiers de sortie
- Workflows entre outils
- Tout autre point flou

Demande-moi avant de coder.

# DÉBUT
Commence par lire .claude/refactor-instructions.md et confirme que tu comprends l'architecture cible.
```

---

## 📋 Checklist avant d'envoyer le prompt

- [ ] Claude Code installé dans VSCode
- [ ] Fichier `.claude/refactor-instructions.md` créé
- [ ] Fichier `.vscode/settings.json` configuré
- [ ] VSCode ouvert **à la racine** du dépôt
- [ ] Branche Git créée : `git checkout -b refactor/i18n-kit-structure`
- [ ] Git status propre (pas de modifications non commitées)

---

## 🎯 Workflow avec Claude Code

### 1. Ouvrir Claude Code
- `Ctrl+Shift+P` (ou `Cmd+Shift+P` sur Mac)
- Taper : "Claude: Open Chat"
- Ou cliquer sur l'icône Claude dans la barre latérale

### 2. Envoyer le prompt initial
- Copier-coller le prompt ci-dessus
- Claude va lire `.claude/refactor-instructions.md` automatiquement

### 3. Valider chaque étape
Après chaque réponse de Claude :
```bash
# Créer les fichiers générés
# Tester le code

# Commit si OK
git add common/
git commit -m "Phase 1: Create common/paths.py module"
```

### 4. Passer à la phase suivante
Prompt pour Phase 2 :
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

---

## 💡 Prompts utiles pendant la refactorisation

### Demander une révision
```
Révise le code que tu viens de générer pour :
1. Vérifier compatibilité Windows (chemins avec backslash)
2. Vérifier gestion erreurs (try/except)
3. Vérifier que timestamps sont bien format YYYYMMDD_HHMMSS
```

### Demander des tests
```
Génère un test unitaire pour la fonction get_tool_output_path qui vérifie :
1. Création du dossier avec timestamp
2. Format timestamp correct (15 caractères)
3. Structure __i18n_kit__/<tool>/<timestamp>
```

### Demander une comparaison
```
Compare l'ancien comportement de Extractor_main.py (avant refacto) avec le nouveau.
Montre-moi :
1. Ancien chemin de sortie
2. Nouveau chemin de sortie
3. Ce qui reste identique
4. Ce qui change
```

### Signaler un problème
```
Problème détecté : les backups .bak sont créés dans le mauvais dossier.

Comportement actuel : backups dans <plugin>/
Comportement attendu : backups dans <plugin>/__i18n_kit__/Applicator/<timestamp>/backups/

Corrige Applicator_main.py ligne 150-160.
```

---

## 🐛 Gestion des erreurs

### Claude ne trouve pas les fichiers
```
Claude, utilise la commande "view" pour lire ces fichiers :
- .claude/refactor-instructions.md
- LocalisationToolKit.py
- 1_Extractor/Extractor_main.py
```

### Claude génère du code incorrect
```
Le code généré ne fonctionne pas. Erreur :
[copier-coller l'erreur]

Analyse l'erreur et propose une correction.
```

### Claude oublie le contexte
```
Rappel du contexte :
- Projet : Adobe_Lightroom_Translation_Plugins_Kit
- Objectif : Nouvelle structure __i18n_kit__
- Phase actuelle : [numéro de phase]
- Dernier commit : [hash]

Lis .claude/refactor-instructions.md pour te remettre en contexte.
```

---

## 📊 Suivi de progression

### Template de commit
```bash
# Phase 1
git commit -m "Phase 1: Create common/paths.py module"

# Phase 2
git commit -m "Phase 2: Refactor Extractor to use __i18n_kit__"

# Phase 3
git commit -m "Phase 3: Refactor Applicator to use __i18n_kit__"

# etc.
```

### Checklist de progression
```
[ ] Phase 1: common/paths.py créé et testé
[ ] Phase 2: Extractor refactorisé
[ ] Phase 3: Applicator refactorisé
[ ] Phase 4: TranslationManager refactorisé
[ ] Phase 5: Tools refactorisé
[ ] Phase 6: LocalisationToolKit.py mis à jour
[ ] Tests complets workflow
[ ] Documentation mise à jour
[ ] Merge dans main
```

---

## 🎓 Bonnes pratiques

### 1. Un commit = Une phase
Ne pas mélanger plusieurs phases dans un commit.

### 2. Tester avant de commit
```bash
# Après chaque phase
python tests/test_paths.py
python 1_Extractor/Extractor_main.py --plugin-path ./test_plugin
```

### 3. Garder les anciennes versions
```bash
# Créer tag avant refacto
git tag pre-refactor-i18n-kit
```

### 4. Documenter les changements
Mettre à jour CHANGELOG.md après chaque phase majeure.

---

## 🚀 Après la refactorisation

### Tests finaux
```bash
# Workflow complet
python LocalisationToolKit.py
# 1. Extractor
# 2. Applicator
# 3. TranslationManager

# Vérifier structure
tree <plugin>/__i18n_kit__/
```

### Merge dans main
```bash
git checkout main
git merge refactor/i18n-kit-structure
git push origin main
git push origin --tags
```

### Documentation
Mettre à jour README.md avec nouvelle structure.
