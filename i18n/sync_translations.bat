@echo off
REM sync_translations.bat - Lance la synchronisation i18n sur Windows
REM
REM Utilisation:
REM   Double-clic sur ce fichier
REM   Ou en ligne de commande:
REM     sync_translations.bat
REM     sync_translations.bat en     (pour l'anglais uniquement)
REM     sync_translations.bat fr     (pour le français uniquement)

setlocal enabledelayedexpansion

REM Aller au répertoire du projet
cd /d "%~dp0.."

echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                 SYNCHRONISATION DES TRADUCTIONS (i18n)                     ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

if "%1"=="" (
    echo [i] Mode: Toutes les langues
) else (
    echo [i] Mode: Langue specifique (%1)
)
echo.

REM Étape 1: Extraction
echo ────────────────────────────────────────────────────────────────────────────
echo ÉTAPE 1/3: EXTRACTION DES CHAÎNES
echo ────────────────────────────────────────────────────────────────────────────
python i18n/extract_strings.py
if errorlevel 1 (
    echo.
    echo [X] Extraction échouée
    pause
    exit /b 1
)
echo.

REM Étape 2: Mise à jour
echo ────────────────────────────────────────────────────────────────────────────
echo ÉTAPE 2/3: MISE À JOUR DES TRADUCTIONS
echo ────────────────────────────────────────────────────────────────────────────
if "%1"=="" (
    python i18n/update_po.py
) else (
    python i18n/update_po.py %1
)
if errorlevel 1 (
    echo.
    echo [X] Mise à jour échouée
    pause
    exit /b 1
)
echo.

REM Étape 3: Compilation
echo ────────────────────────────────────────────────────────────────────────────
echo ÉTAPE 3/3: COMPILATION DES TRADUCTIONS
echo ────────────────────────────────────────────────────────────────────────────
if "%1"=="" (
    python i18n/compile_po.py
) else (
    python i18n/compile_po.py %1
)
if errorlevel 1 (
    echo.
    echo [X] Compilation échouée
    pause
    exit /b 1
)
echo.

echo ════════════════════════════════════════════════════════════════════════════
echo ✓ SYNCHRONISATION TERMINÉE AVEC SUCCÈS
echo ════════════════════════════════════════════════════════════════════════════
echo.
pause
