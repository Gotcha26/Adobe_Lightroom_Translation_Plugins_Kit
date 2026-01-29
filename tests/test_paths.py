#!/usr/bin/env python3
"""
test_paths.py

Tests unitaires pour le module common/paths.py

Usage:
    python tests/test_paths.py
    pytest tests/test_paths.py  (si pytest installé)
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Ajouter le parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.paths import (
    get_i18n_kit_path,
    get_tool_output_path,
    find_latest_tool_output,
    normalize_path
)


def test_get_i18n_kit_path():
    """Test que get_i18n_kit_path retourne le bon chemin."""
    print("TEST 1: get_i18n_kit_path")
    
    plugin_path = "/home/user/plugin.lrplugin"
    result = get_i18n_kit_path(plugin_path)
    expected = os.path.join(plugin_path, "__i18n_kit__")
    
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"  [OK] Chemin correct: {result}")


def test_get_tool_output_path():
    """Test création de dossier avec timestamp."""
    print("\nTEST 2: get_tool_output_path")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_path = os.path.join(tmpdir, "test_plugin.lrplugin")
        os.makedirs(plugin_path)
        
        # Créer dossier de sortie
        output_path = get_tool_output_path(plugin_path, "Extractor", create=True)
        
        # Vérifier structure
        assert os.path.exists(output_path), "Dossier non créé"
        assert "__i18n_kit__" in output_path, "__i18n_kit__ manquant"
        assert "Extractor" in output_path, "Nom outil manquant"
        
        # Vérifier format timestamp (YYYYMMDD_HHMMSS = 15 caractères)
        timestamp = os.path.basename(output_path)
        assert len(timestamp) == 15, f"Timestamp incorrect: {timestamp}"
        assert timestamp[8] == "_", "Format timestamp incorrect (pas de underscore)"
        
        print(f"  [OK] Dossier créé: {output_path}")
        print(f"  [OK] Timestamp valide: {timestamp}")


def test_get_tool_output_path_no_create():
    """Test sans création de dossier."""
    print("\nTEST 3: get_tool_output_path (no create)")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_path = os.path.join(tmpdir, "test_plugin.lrplugin")
        
        # Ne pas créer le dossier
        output_path = get_tool_output_path(plugin_path, "Applicator", create=False)
        
        # Vérifier que le dossier N'existe PAS
        assert not os.path.exists(output_path), "Dossier créé alors que create=False"
        
        print(f"  [OK] Chemin généré sans création: {output_path}")


def test_find_latest_tool_output():
    """Test détection du dossier le plus récent."""
    print("\nTEST 4: find_latest_tool_output")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_path = os.path.join(tmpdir, "test_plugin.lrplugin")
        tool_dir = os.path.join(plugin_path, "__i18n_kit__", "Extractor")
        os.makedirs(tool_dir)
        
        # Créer plusieurs dossiers avec timestamps différents
        timestamps = [
            "20260128_120000",
            "20260128_130000",
            "20260129_140000",  # Le plus récent
            "20260127_110000"
        ]
        
        for ts in timestamps:
            os.makedirs(os.path.join(tool_dir, ts))
        
        # Chercher le plus récent
        latest = find_latest_tool_output(plugin_path, "Extractor")
        
        assert latest is not None, "Aucun dossier trouvé"
        assert "20260129_140000" in latest, f"Mauvais dossier: {latest}"
        
        print(f"  [OK] Dernier dossier trouvé: {os.path.basename(latest)}")


def test_find_latest_tool_output_empty():
    """Test quand aucun dossier n'existe."""
    print("\nTEST 5: find_latest_tool_output (empty)")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_path = os.path.join(tmpdir, "test_plugin.lrplugin")
        
        # Chercher dans un dossier vide
        latest = find_latest_tool_output(plugin_path, "Extractor")
        
        assert latest is None, "Devrait retourner None si vide"
        
        print(f"  [OK] Retourne None correctement")


def test_normalize_path_windows():
    """Test normalisation chemins Windows."""
    print("\nTEST 6: normalize_path (Windows)")
    
    # Simuler chemin Windows (même sur Linux pour le test)
    raw_path = "C:\\Users\\Test\\plugin.lrplugin"
    normalized = normalize_path(raw_path)
    
    # Vérifier qu'il n'y a pas de mix / et \
    assert "\\" in normalized or "/" in normalized, "Chemin non normalisé"
    
    print(f"  [OK] Chemin normalisé: {normalized}")


def test_normalize_path_linux():
    """Test normalisation chemins Linux."""
    print("\nTEST 7: normalize_path (Linux)")
    
    raw_path = "/home/user/plugin.lrplugin"
    normalized = normalize_path(raw_path)
    
    assert os.path.isabs(normalized), "Chemin pas absolu"
    
    print(f"  [OK] Chemin normalisé: {normalized}")


def test_full_workflow():
    """Test workflow complet: créer puis trouver."""
    print("\nTEST 8: Workflow complet")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_path = os.path.join(tmpdir, "test_plugin.lrplugin")
        os.makedirs(plugin_path)
        
        # 1. Créer sortie Extractor
        extractor_out = get_tool_output_path(plugin_path, "Extractor", create=True)
        
        # 2. Créer fichier fictif
        test_file = os.path.join(extractor_out, "TranslatedStrings_en.txt")
        with open(test_file, 'w') as f:
            f.write("Test")
        
        # 3. Chercher dernière extraction
        latest = find_latest_tool_output(plugin_path, "Extractor")
        
        assert latest == extractor_out, "Chemin différent"
        assert os.path.exists(os.path.join(latest, "TranslatedStrings_en.txt"))
        
        print(f"  [OK] Workflow complet validé")
        print(f"    Créé: {extractor_out}")
        print(f"    Trouvé: {latest}")


def run_all_tests():
    """Exécute tous les tests."""
    print("=" * 80)
    print("TESTS: common/paths.py")
    print("=" * 80)
    
    tests = [
        test_get_i18n_kit_path,
        test_get_tool_output_path,
        test_get_tool_output_path_no_create,
        test_find_latest_tool_output,
        test_find_latest_tool_output_empty,
        test_normalize_path_windows,
        test_normalize_path_linux,
        test_full_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] ÉCHEC: {e}")
            failed += 1
        except Exception as e:
            print(f"  [FAIL] ERREUR: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"RÉSULTATS: {passed} réussis, {failed} échoués")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
