# Quel Workflow Choisir ?

## 🤔 Question rapide

Votre plugin est-il hébergé sur GitHub et vos traducteurs sont-ils à l'aise avec Git ?

- ✅ **OUI** → Utilisez le [Workflow GitHub](WORKFLOW_GITHUB.md) (recommandé)
- ❌ **NON** → Utilisez le [Workflow WebBridge](WORKFLOW_MISE_A_JOUR.md#workflow-2--webbridge-moderne--disponible)

---

## Comparaison des 3 workflows

| Critère | Workflow GitHub 🌟 | Workflow WebBridge | Workflow Classique |
|---------|-------------------|-------------------|-------------------|
| **Plugin sur GitHub** | ✅ Requis | ⚠️ Optionnel | ⚠️ Optionnel |
| **Traducteurs techniques** | ✅ Oui | ❌ Non requis | ✅ Oui |
| **Simplicité traducteur** | ✅ Édition GitHub | ✅ Interface web | ⚠️ Fichier .txt |
| **Simplicité développeur** | ✅✅ Très simple | ✅ Simple | ⚠️ Complexe |
| **Traçabilité** | ✅ Git log | ❌ Aucune | ❌ Aucune |
| **Review** | ✅ Pull Request | ❌ Manuelle | ❌ Manuelle |
| **Historique** | ✅ Git blame | ❌ Non | ❌ Non |
| **Outils externes** | ❌ Aucun | ⚠️ quicki18n.studio | ❌ Aucun |
| **Collaboration** | ✅ Excellente | ⚠️ Limitée | ⚠️ Difficile |
| **Validation auto** | ⚠️ Possible (CI) | ✅ Oui | ❌ Non |

---

## Workflow 1 : GitHub 🌟

### Quand l'utiliser ?

- ✅ Plugin hébergé sur GitHub (public ou privé)
- ✅ Traducteurs contributeurs open-source
- ✅ Besoin de traçabilité (qui a traduit quoi)
- ✅ Review des traductions avant intégration
- ✅ Plusieurs traducteurs collaborent

### Workflow typique

```
Développeur:
1. Extractor → TranslatedStrings_en.txt
2. Applicator → Code localisé
3. SYNC (optionnel) → Propager [NEW] dans tous les fichiers
4. Commit & Push

Traducteur:
5. Fork sur GitHub
6. Éditer TranslatedStrings_fr.txt (directement ou localement)
7. Commit & Pull Request

Développeur:
8. Review PR
9. Merge
10. Tester
```

### Avantages

- ✅ **Simple** : Workflow standard Git
- ✅ **Traçable** : Historique complet
- ✅ **Collaboratif** : PRs, reviews, comments
- ✅ **Transparent** : Tout le monde voit les contributions

### Inconvénients

- ⚠️ Requiert GitHub
- ⚠️ Traducteurs doivent connaître Git (niveau basique)

📖 **[Guide complet](WORKFLOW_GITHUB.md)**

---

## Workflow 2 : WebBridge

### Quand l'utiliser ?

- ✅ Traducteurs NON techniques (jamais utilisé Git)
- ✅ Traduction massive (200+ clés d'un coup)
- ✅ Besoin d'interface visuelle avec contexte
- ✅ Validation automatique des placeholders
- ✅ Plugin pas forcément sur GitHub

### Workflow typique

```
Développeur:
1. Extractor → TranslatedStrings_en.txt
2. WebBridge Export → translations.json
3. Envoyer JSON au traducteur (email, Dropbox...)

Traducteur:
4. Ouvrir quicki18n.studio dans navigateur
5. Importer translations.json
6. Traduire visuellement (contexte visible)
7. Exporter translations.json
8. Renvoyer au développeur

Développeur:
9. WebBridge Import → TranslatedStrings_xx.txt
10. Copier dans plugin
11. Tester
```

### Avantages

- ✅ **Interface intuitive** : Éditeur visuel moderne
- ✅ **Contexte visible** : fichier:ligne pour chaque clé
- ✅ **Validation automatique** : Placeholders vérifiés
- ✅ **Aucune installation** : Tout dans le navigateur

### Inconvénients

- ⚠️ Dépendance externe (quicki18n.studio)
- ⚠️ Pas d'historique Git
- ⚠️ Pas de review intégrée
- ⚠️ Étapes supplémentaires (export/import)

📖 **[Guide complet](WORKFLOW_MISE_A_JOUR.md#workflow-2--webbridge-moderne--disponible)**

---

## Workflow 3 : Classique

### Quand l'utiliser ?

- ✅ Traducteurs très techniques
- ✅ Workflow interne déjà établi
- ✅ Mises à jour complexes avec COMPARE/EXTRACT/INJECT
- ✅ Besoin de fichiers intermédiaires (TRANSLATE_xx.txt)

### Workflow typique

```
Développeur:
1. Extractor → nouveau TranslatedStrings_en.txt
2. COMPARE → Identifier changements
3. EXTRACT → Générer TRANSLATE_fr.txt (nouvelles clés)
4. Envoyer TRANSLATE_fr.txt au traducteur

Traducteur:
5. Éditer TRANSLATE_fr.txt (petit fichier)
6. Renvoyer au développeur

Développeur:
7. INJECT → Fusionner dans TranslatedStrings_fr.txt
8. SYNC → Synchroniser tous les fichiers
9. Copier dans plugin
10. Tester
```

### Avantages

- ✅ **Contrôle total** : Étapes manuelles
- ✅ **Fichiers intermédiaires** : TRANSLATE_xx.txt (petits)
- ✅ **Historique des changements** : COMPARE génère CHANGELOG

### Inconvénients

- ⚠️ **Complexe** : Beaucoup d'étapes
- ⚠️ **Fastidieux** : Beaucoup de commandes
- ⚠️ **Risque d'erreur** : Édition manuelle du format .txt
- ⚠️ **Pas de traçabilité** : Sauf si commit Git manuel

📖 **[Guide complet](WORKFLOW_MISE_A_JOUR.md#workflow-1--classique--disponible)**

---

## Cas d'usage réels

### Plugin PiwigoPublish (278 clés)

**Contexte** : Plugin open-source sur GitHub, traducteurs contributeurs.

**Workflow choisi** : **GitHub** 🌟

**Raison** :
- Traducteurs déjà sur GitHub pour contribuer au code
- Review facile via Pull Requests
- Historique Git complet
- Pas besoin d'outils externes

**Durée développeur** : 2 minutes par mise à jour

---

### Plugin commercial avec traducteur professionnel

**Contexte** : Plugin privé, traducteur payé qui n'utilise pas Git.

**Workflow choisi** : **WebBridge**

**Raison** :
- Traducteur non technique
- Interface visuelle professionnelle
- Validation automatique (moins d'erreurs)
- Contexte visible (qualité de traduction)

**Durée développeur** : 5 minutes par mise à jour

---

### Équipe interne avec workflow établi

**Contexte** : Entreprise avec processus de localisation défini.

**Workflow choisi** : **Classique**

**Raison** :
- Workflow déjà documenté en interne
- Intégration avec outils de gestion de traduction
- Besoin de fichiers intermédiaires pour validation
- Équipe habituée au format .txt

**Durée développeur** : 15 minutes par mise à jour

---

## Recommandation générale

### Pour la majorité des cas : Workflow GitHub 🌟

Si votre plugin est sur GitHub, **commencez par le Workflow GitHub**. C'est le plus simple et le plus naturel.

Vous pourrez toujours passer à WebBridge plus tard si vous trouvez un traducteur qui n'est vraiment pas à l'aise avec Git.

### Cas spécial : Première traduction complète (200+ clés)

Si vous cherchez quelqu'un pour traduire **toutes** les clés d'un coup (pas de traduction existante), WebBridge peut être plus confortable grâce à l'interface visuelle.

Mais même dans ce cas, un traducteur peut faire des PRs progressives sur GitHub (30 clés par session).

---

## Puis-je combiner les workflows ?

**Oui !** Voici des combinaisons courantes :

### GitHub + Corrections rapides

- **Workflow principal** : GitHub (PRs)
- **Corrections rapides** : Édition directe du .txt par le développeur

### GitHub + WebBridge pour nouveaux traducteurs

- **Traducteurs techniques** : GitHub (PRs)
- **Traducteurs non techniques** : WebBridge (export/import par développeur)

### WebBridge + GitHub pour historique

- **Traduction** : WebBridge (interface visuelle)
- **Commit** : Développeur commit le résultat dans Git

---

## Outils complémentaires

Quel que soit le workflow choisi, ces outils sont toujours utiles :

### TranslationManager SYNC

Propager rapidement les nouvelles clés dans tous les fichiers de langue.

**Quand** : Après Extractor, avant de committer.

### Extractor + Applicator

Toujours nécessaires pour :
- Initialisation du plugin (première fois)
- Extraction de nouvelles chaînes après modifications du code

---

## Conclusion

**Débutant** → [Workflow GitHub](WORKFLOW_GITHUB.md)

**Traducteur non technique** → [Workflow WebBridge](WORKFLOW_MISE_A_JOUR.md#workflow-2--webbridge-moderne--disponible)

**Workflow complexe établi** → [Workflow Classique](WORKFLOW_MISE_A_JOUR.md#workflow-1--classique--disponible)

**Besoin d'aide** → Posez une question sur [GitHub Issues](https://github.com/votre-repo/issues)

---

**Date de création** : 2026-01-31
**Version** : 1.0
