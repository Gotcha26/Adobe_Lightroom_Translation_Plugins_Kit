# TranslationManager v4.2

**Gestionnaire de traductions multilingues pour plugins Adobe Lightroom Classic**

---

## 📁 Structure

```
TranslationManager/
├── TranslationManager.py   # Script principal (menu + CLI)
├── TM_common.py            # Fonctions communes (parser, utils)
├── TM_compare.py           # Commande COMPARE
├── TM_extract.py           # Commande EXTRACT
├── TM_inject.py            # Commande INJECT
└── TM_sync.py              # Commande SYNC
```

---

## 📋 Commandes

| Commande | Description |
|----------|-------------|
| `compare` | Compare 2 versions EN → `UPDATE_en.json` + `CHANGELOG.txt` |
| `extract` | Génère mini fichiers `TRANSLATE_xx.txt` pour traduction |
| `inject` | Réinjecte les traductions (**EN par défaut si vide**) |
| `sync` | Finalise les fichiers de langue |

---

## 🔄 Workflow

```
  Code LUA modifié
        │
        ▼
  Extractor → TranslatedStrings_en.txt (nouveau)
        │
        ▼
  1. COMPARE ─────────────────────────────────────┐
     → UPDATE_en.json + CHANGELOG.txt             │
        │                                         │
        ▼                                         │
  2. EXTRACT (optionnel)                          │
     → TRANSLATE_xx.txt                           │
        │                                         │
        ▼                                         │
  3. INJECT (optionnel)                           │
     → Valeurs EN par défaut si non traduit       │
        │                                         │
        ▼                                         │
  4. SYNC ◄───────────────────────────────────────┘
     → Fichiers finaux avec [NEW] et [NEEDS_REVIEW]
```

**Note** : EXTRACT et INJECT sont optionnels. Vous pouvez aller directement de COMPARE à SYNC.

---

## 🚀 Usage

### Mode interactif

```bash
python TranslationManager.py
```

### Mode CLI

```bash
# 1. Comparer
python TranslationManager.py compare --old ./ancien.txt --new ./nouveau.txt

# 2. Extraire (optionnel)
python TranslationManager.py extract --update ./20260128_143000 --locales ./Locales

# 3. Injecter (optionnel) - valeurs EN par défaut si non traduit
python TranslationManager.py inject --translate-dir ./20260128_143000 --locales ./Locales

# 4. Synchroniser
python TranslationManager.py sync --update ./20260128_143000 --locales ./Locales
```

---

## 📁 Format des fichiers

### TRANSLATE_xx.txt

```
[KEY] $$$/Piwigo/NewFeature
[EN]  New Feature
[FR] → Nouvelle fonctionnalité    ← Si vide, utilise la valeur EN

[KEY] $$$/Piwigo/Settings/Host
[EN AVANT]  Server
[EN APRÈS]  Piwigo Server
[FR ACTUEL] Serveur
[FR] →                            ← Vide = "Piwigo Server" (EN)
```

### TranslatedStrings_xx.txt (entête enrichi)

```lua
-- =============================================================================
-- Plugin Localization - FR
-- Generated: 2026-01-28 22:55:32
-- Total keys: 155
-- New keys: 3
-- Changed keys: 1
-- Source: SYNC
-- =============================================================================

-- Piwigo
-- ## NEW ## À traduire
"$$$/Piwigo/NewFeature=New Feature"

-- ## NEEDS_REVIEW ## Texte EN modifié
"$$$/Piwigo/Settings/Host=Serveur Piwigo"
```

---

## ❓ FAQ

### Q: Que se passe-t-il si je laisse → vide dans TRANSLATE ?

La valeur EN est utilisée par défaut. Le fichier reste complet.

### Q: Puis-je utiliser INJECT plusieurs fois ?

Oui. Chaque INJECT fusionne les nouvelles traductions avec l'existant.

### Q: Que signifient les marqueurs [NEW] et [NEEDS_REVIEW] ?

- `[NEW]` : Clé ajoutée, valeur EN par défaut, à traduire
- `[NEEDS_REVIEW]` : Le texte EN a changé, vérifier si la traduction est toujours correcte

---

**Version 4.2** - Janvier 2026  
*Développé par Claude (Anthropic) pour Julien Moreau*
