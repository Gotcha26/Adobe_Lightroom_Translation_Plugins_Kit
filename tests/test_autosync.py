"""Non-régression AUTOSYNC (#11) : les noms de fichiers ne doivent plus être corrompus."""

import os

from tools.translator.autosync import run_autosync


def test_autosync_runs_on_fixture(plugin_dir, isolated_config):
    results = run_autosync(plugin_dir)

    assert results["errors"] == []
    assert os.path.isfile(results["extractor"]["en_file"])

    corrupted = [
        name
        for _root, _dirs, files in os.walk(plugin_dir)
        for name in files
        if name.startswith("_(")
    ]
    assert corrupted == []
