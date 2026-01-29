# Index - Extractor Refactorisé

## 📋 Fichiers fournis

### Point d'entrée
- **`Extractor_main.py`** (4.6 KB)
  - Orchestre l'extraction complète
  - Parse les arguments CLI
  - Appelle les générateurs de fichiers

### Modules spécialisés

#### 🔧 Configuration & Constantes
- **`Extractor_config.py`** (4.7 KB)
  - Patterns regex pour l'analyse
  - Listes d'exclusion et règles métier
  - Constantes partagées

#### 📦 Modèles de données
- **`Extractor_models.py`** (3.9 KB)
  - `StringMember` - Membre de chaîne concaténée
  - `ExtractedLine` - Ligne UI avec membres
  - `ExtractedString` - Chaîne extraite + métadonnées
  - `ExtractionStats` - Statistiques globales

#### 🔨 Utilitaires
- **`Extractor_utils.py`** (6.1 KB)
  - `extract_spacing()` - Gestion des espaces
  - `extract_suffix()` - Extraction des suffixes
  - `is_technical_string()` - Filtrage technique
  - `generate_loc_key()` - Génération des clés LOC
  - Autres utilitaires de traitement texte

#### ⚙️ Moteur d'extraction
- **`Extractor_engine.py`** (11 KB)
  - `LocalizableStringExtractor` - Classe principale
  - `extract_from_file()` - Analyse un fichier Lua
  - `extract_all()` - Traite tous les fichiers
  - Gestion des clés LOC existantes

#### 📄 Génération de fichiers
- **`Extractor_output.py`** (8.9 KB)
  - `OutputGenerator` - Crée les fichiers de sortie
  - `generate_plugin_strings()` - TranslatedStrings_xx.txt
  - `generate_spacing_metadata()` - spacing_metadata.json
  - `generate_replacements_json()` - replacements.json

#### 📊 Génération de rapports
- **`Extractor_report.py`** (11 KB)
  - `ReportGenerator` - Crée les rapports
  - `generate_report()` - Rapport détaillé complet
  - Affichage avec émojis et contexte

### Documentation
- **`ARCHITECTURE.md`** - Vue d'ensemble complète
- **`INDEX.md`** (ce fichier)

---

## 🚀 Installation & Utilisation

### 1. Placer les fichiers
Tous les fichiers doivent être dans le **même répertoire**:

```
./
├── Extractor_main.py          ← Point d'entrée
├── Extractor_config.py        ← Constantes
├── Extractor_models.py        ← Classes de données
├── Extractor_utils.py         ← Utilitaires
├── Extractor_engine.py        ← Moteur d'extraction
├── Extractor_output.py        ← Génération fichiers
├── Extractor_report.py        ← Génération rapports
└── Applicator_main.py         ← (inchangé)
```

### 2. Lancer l'extraction
```bash
python Extractor_main.py --plugin-path ./piwigoPublish.lrplugin
```

### 3. Fichiers générés
```
TranslatedStrings_en.txt       → Clés LOC pour traduction
spacing_metadata.json          → Métadonnées d'espaces/suffixes
replacements.json              → Instructions de remplacement
extraction_report_*.txt        → Rapport détaillé
```

---

## 📊 Comparaison avant/après

| Aspect | Avant | Après |
|--------|-------|-------|
| Nombre de fichiers | 1 (1167 lignes) | 7 (taille totale: ~50 KB) |
| Lignes principales | 1167 | ~200 (Extractor_main.py) |
| Maintenabilité | ❌ Difficile | ✅ Excellente |
| Testabilité | ❌ Compliquée | ✅ Simple |
| Réutilisabilité | ❌ Impossible | ✅ Modules importables |
| Évolutions futures | ❌ Risquées | ✅ Sûres |

---

## 🔄 Compatibilité

### ✅ Compatible avec Applicator_main.py
- Les fichiers de sortie sont **identiques**
- Aucune modification requise

### ✅ 100% rétrocompatible
- Mêmes patterns d'extraction
- Mêmes règles de filtrage
- Mêmes clés LOC générées

---

## 📝 Modifications futures

Grâce à la modularité:

| Besoin | Fichier à modifier |
|--------|-------------------|
| Ajouter un pattern UI | `Extractor_config.py` |
| Modifier génération de clés | `Extractor_utils.py` |
| Changer le format de sortie | `Extractor_output.py` |
| Améliorer le rapport | `Extractor_report.py` |
| Ajouter des règles de filtrage | `Extractor_engine.py` |

---

## 🐛 Débogage

### Pour tester une fonction
```python
from Extractor_utils import extract_spacing
text, leading, trailing = extract_spacing("  Hello  ")
print(f"Leading: {leading}, Trailing: {trailing}")  # 2, 2
```

### Pour tester l'extraction
```python
from Extractor_engine import LocalizableStringExtractor
extractor = LocalizableStringExtractor("./plugin")
extractor.extract_all()
print(f"Trouvé {extractor.stats.total_strings} chaînes")
```

---

## 📞 Support

Si besoin de modifications ou d'ajouts:

1. Identifier le module concerné (voir tableau ci-dessus)
2. Modifier le fichier spécifique
3. Tester avec `Extractor_main.py --plugin-path ./test`
4. Vérifier les fichiers de sortie

---

## ✨ Caractéristiques principales

✅ **Extraction complète** des chaînes UI  
✅ **Gestion des espaces** de formatage  
✅ **Détection des suffixes** communs  
✅ **Chaînes concaténées** analysées  
✅ **Clés LOC existantes** préservées  
✅ **Rapports détaillés** pour audit  
✅ **Code réutilisable** et testable  
✅ **Documentation** exhaustive  

---

**Version**: 5.0 (Refactorisée)  
**Date**: 2026-01-27  
**Auteur**: Claude (Anthropic) pour Julien Moreau
