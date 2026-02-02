# Guide Traducteur : Contributeur simple

Vous souhaitez traduire un plugin Lightroom dans votre langue ? Ce guide est fait pour vous. **Aucune compétence technique requise**, juste la maîtrise de votre langue cible.

---

## 📋 Situation type

Le développeur vous a envoyé un fichier `TranslatedStrings_fr.txt` (ou votre langue) à traduire. Le fichier existe déjà, il contient des clés en anglais que vous devez traduire.

---

## 🛠️ Ce dont vous avez besoin

### Un éditeur de texte simple

| Éditeur | Plateforme | Recommandation |
|---------|------------|----------------|
| [VS Code](https://code.visualstudio.com/) | Windows, Mac, Linux | Recommandé (gratuit) |
| [Notepad++](https://notepad-plus-plus.org/) | Windows | Très bien |
| [Sublime Text](https://www.sublimetext.com/) | Windows, Mac, Linux | Très bien |

**À éviter absolument :**
- Microsoft Word
- Google Docs
- LibreOffice Writer

Ces logiciels ajoutent du formatage caché qui corrompt le fichier.

### Vérifications importantes

- **Encodage UTF-8** : Pour les accents et caractères spéciaux
- **Pas de formatage** : Texte brut uniquement

---

## 🎯 Comprendre le format

Chaque ligne du fichier ressemble à ceci :

```
"$$$/MonPlugin/Menu/File=File"
```

**Anatomie :**
```
"$$$/MonPlugin/Menu/File=File"
 └─────────CLÉ─────────┘ └VALEUR┘
        NE PAS TOUCHER    À TRADUIRE
```

**Règle d'or** : Traduisez **uniquement** ce qui est après le `=`

---

## 📝 Le processus de traduction

### Étape 1 : Ouvrir le fichier

1. Ouvrez votre éditeur de texte
2. Ouvrez le fichier `TranslatedStrings_fr.txt`
3. Vérifiez l'encodage (UTF-8) en bas de la fenêtre

### Étape 2 : Traduire ligne par ligne

**Avant :**
```
"$$$/MonPlugin/Menu/File=File"
"$$$/MonPlugin/Menu/Edit=Edit"
"$$$/MonPlugin/Menu/View=View"
"$$$/MonPlugin/Dialog/OK=OK"
"$$$/MonPlugin/Dialog/Cancel=Cancel"
```

**Après (français) :**
```
"$$$/MonPlugin/Menu/File=Fichier"
"$$$/MonPlugin/Menu/Edit=Édition"
"$$$/MonPlugin/Menu/View=Affichage"
"$$$/MonPlugin/Dialog/OK=Valider"
"$$$/MonPlugin/Dialog/Cancel=Annuler"
```

### Étape 3 : Gérer les placeholders

Certaines chaînes contiennent des **codes spéciaux** à ne **jamais traduire** :

| Code | Signification | Exemple |
|------|---------------|---------|
| `%s` | Texte variable | `"Uploaded %s"` → `"Téléversé %s"` |
| `%d` | Nombre | `"Found %d photos"` → `"Trouvé %d photos"` |
| `\n` | Retour à la ligne | Garder tel quel |
| `\t` | Tabulation | Garder tel quel |

**Exemple :**
```
AVANT  : "$$$/Plugin/Status/Count=%d items selected"
APRÈS  : "$$$/Plugin/Status/Count=%d éléments sélectionnés"
                                   ↑
                            Garder le %d !
```

### Étape 4 : Sauvegarder et vérifier

1. Sauvegardez le fichier (Ctrl+S)
2. Vérifiez que l'encodage est toujours UTF-8
3. Relisez quelques lignes pour vérifier la cohérence

---

## ✅ Checklist avant envoi

- [ ] Toutes les lignes sont traduites
- [ ] Les clés (avant le `=`) n'ont pas été modifiées
- [ ] Les placeholders (`%s`, `%d`, `\n`) sont intacts
- [ ] L'encodage est UTF-8
- [ ] Pas de lignes supprimées

---

## 💡 Conseils pratiques

### Soyez cohérent

Utilisez toujours le même mot pour le même concept :

```
GLOSSAIRE PERSONNEL
───────────────────────────────────
File        → Fichier
Edit        → Édition
View        → Affichage
Settings    → Paramètres
OK          → Valider
Cancel      → Annuler
Save        → Enregistrer
Delete      → Supprimer
Export      → Exporter
Import      → Importer
```

### Pensez à l'interface

Le texte traduit apparaîtra dans des menus, boutons, dialogues. Vérifiez que :
- Le texte n'est pas trop long
- Le sens est clair dans le contexte d'un logiciel photo

### Outils utiles

| Outil | Usage |
|-------|-------|
| [DeepL](https://www.deepl.com/) | Traduction de référence (meilleure qualité) |
| [Reverso Context](https://context.reverso.net/) | Voir les termes en contexte |
| [Google Translate](https://translate.google.com/) | Traduction rapide |

---

## 📤 Renvoyer le fichier

Une fois terminé, renvoyez le fichier au développeur par :
- Email
- Pull Request GitHub (si vous savez faire)
- Tout autre moyen convenu

**Email type :**
```
Objet : Traduction MonPlugin - Français terminée

Bonjour,

Vous trouverez ci-joint le fichier TranslatedStrings_fr.txt
que j'ai traduit entièrement.

- Toutes les clés sont traduites
- Encodage UTF-8 vérifié
- Placeholders préservés

Cordialement,
[Votre nom]
```

---

## ❓ Questions fréquentes

### Dois-je tout traduire d'un coup ?

**Non.** Lightroom affiche l'anglais par défaut pour les clés non traduites. Vous pouvez traduire progressivement et renvoyer des versions partielles.

### Comment tester mes traductions ?

1. Placez le fichier traduit dans le dossier du plugin
2. Changez la langue de votre système
3. Relancez Lightroom complètement
4. Vérifiez l'affichage

### Je ne comprends pas le contexte d'une chaîne

Demandez au développeur ! Il peut vous fournir des captures d'écran ou des explications sur où et comment la chaîne apparaît.

---

## 🔗 Ressources

- [Guide contributeur débrouillard](02_Contributeur_debrouillard.md) — Si le fichier n'existe pas encore
- [Guide contributeur professionnel](03_Contributeur_pro.md) — Outils et workflows avancés

---

|  |  |
|--|--|
| **Document** | Guide Traducteur - Contributeur simple |
| **Version** | 1.0 |
| **Date** | 2026-02-02 |
| **Projet** | https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit |
