# Tools - Technical Documentation

**Version 1.0 | January 2026**

## Overview

The Tools folder contains two practical utilities for managing temporary files and restoring backups. These tools are simple but essential for maintaining a clean and secure working environment.

## Project Architecture

```
9_Tools/
├── Delete_temp_dir.py       ← Deleting the temporary folder
├── Restore_backup.py        ← Restoring backups
└── __doc/
    └── README.md            ← This file
```

These two scripts are independent and can be used directly in CLI or via `LocalisationToolKit.py`.

## Delete_temp_dir.py - Cleaning the Temporary Folder

### Description

This tool deletes the `__i18n_tmp__` temporary folder (or the configured name) from a Lightroom plugin. This folder contains all the outputs from the tools (extractions, backups, reports).

### When to use it?

- To free up disk space
- After completing a full localization cycle
- To clean up old executions that are no longer needed
- Before versioning the plugin (the temporary folder should not be in Git)

### How does it work?

```
Lightroom Plugin
    │
    └── __i18n_tmp__/
        ├── 1_Extractor/
        │   ├── 20260120_100000/    (5 files, 120 KB)
        │   └── 20260129_143022/    (5 files, 135 KB)
        ├── 2_Applicator/
        │   └── 20260129_143530/    (15 backups, 2.3 MB)
        └── 3_TranslationManager/
            └── 20260129_144000/    (8 files, 45 KB)

        TOTAL: 33 files, 2.6 MB

        ▼

    DELETION (after triple confirmation)

        ▼

    __i18n_tmp__/ deleted
```

### Usage

**Interactive mode:**
```bash
python 9_Tools/Delete_temp_dir.py
```

The tool displays:
1. The temporary folder path
2. The detailed content (number of files and size per subfolder)
3. The total size
4. A triple confirmation for safety

**Example output:**

```
==================================================
     DELETING THE TEMPORARY FOLDER
==================================================

Plugin path: ./myPlugin.lrplugin

Temporary folder: __i18n_tmp__
Full path       : ./myPlugin.lrplugin/__i18n_tmp__

==================================================
       TEMPORARY FOLDER CONTENT
==================================================

  Extractor                 :   10 files, 255.0 KB
  Applicator                :   15 files, 2.3 MB
  TranslationManager        :    8 files, 45.0 KB

--------------------------------------------------
TOTAL: 33 files, 2.6 MB
--------------------------------------------------

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!! WARNING - IRREVERSIBLE OPERATION !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This operation will PERMANENTLY DELETE:
  ./myPlugin.lrplugin/__i18n_tmp__

You will lose:
  - All previous extractions
  - All backup files (.bak)
  - All tool outputs

Step 1/3: Initial confirmation
Do you really want to delete this folder? [y/N]: y

Step 2/3: Security confirmation
Type 'DELETE' to confirm: DELETE

Step 3/3: Last chance
Final confirmation - Are you ABSOLUTELY sure? [y/N]: y

Deleting ./myPlugin.lrplugin/__i18n_tmp__...
✓ Temporary folder successfully deleted!
```

### Security

The script includes several levels of protection:

1. **Path validation**: Checks that the plugin exists
2. **Detailed display**: Shows exactly what will be deleted
3. **Triple confirmation**:
   - Initial confirmation (y/N)
   - Password ("DELETE")
   - Last chance (y/N)
4. **Error handling**: Detects insufficient permissions

### Error Cases

**Permission error:**
```
✗ Permission denied: [WinError 32] The process cannot access the file...
  Close all programs using these files.
```

**Solution:** Close all editors, file explorers, or programs accessing the temporary folder.

### Recommendations

- **Don't delete** if you need the backups to restore files
- **Don't delete** if you want to compare two extractions with TranslationManager
- **Delete regularly** to avoid accumulation of temporary files
- **Add to .gitignore**: `__i18n_tmp__/` to avoid versioning this folder

## Restore_backup.py - Restoring Backups

### Description

This tool restores a plugin's `.lua` files from their `.bak` backups created by Applicator. Useful for undoing modifications in case of error or unwanted results.

### When to use it?

- After an application that produced incorrect results
- To return to the state before localization
- To test different versions (apply → test → restore → modify → reapply)
- In case of error in replacements

### How does it work?

```
Lightroom Plugin                  Applicator Backups
    │                                 │
    ├── MyDialog.lua (modified)       ├── MyDialog.lua.bak (original)
    ├── Settings.lua (modified)       ├── Settings.lua.bak (original)
    └── Upload.lua (modified)         └── Upload.lua.bak (original)

                    │
                    ▼
              RESTORATION
                    │
                    ▼

    ├── MyDialog.lua (restored)
    ├── Settings.lua (restored)
    └── Upload.lua (restored)
```

### Usage

**Interactive mode:**
```bash
python 9_Tools/Restore_backup.py
```

**CLI mode with auto-detection:**
```bash
python 9_Tools/Restore_backup.py /path/to/plugin.lrplugin
```

**Dry-run mode (simulation):**
```bash
python 9_Tools/Restore_backup.py --dry-run /path/to/plugin.lrplugin
```

### Example Output

**Automatic detection:**

```
============================================================
  RESTORING .bak FILES (v2.0)
============================================================

Plugin directory to restore:
  Examples: ./piwigoPublish.lrplugin
            C:\Lightroom\plugin

Path: ./myPlugin.lrplugin

[OK] Directory: ./myPlugin.lrplugin

[OK] 2 Applicator session(s) found in __i18n_tmp__/

Applicator sessions with available backups:
------------------------------------------------------------
  1. 2026-01-29 14:35:30 (12 file(s))
  2. 2026-01-27 09:12:34 (12 file(s))
  0. Cancel

Choose a session (0 to cancel): 1

[OK] Session selected: 2026-01-29 14:35:30

Simulation mode (dry-run)? [Y/n]: n

[OK] Real mode - Files will be modified

============================================================
SEARCHING FOR .bak FILES
============================================================
Plugin: ./myPlugin.lrplugin
Source: ./myPlugin.lrplugin/__i18n_tmp__/2_Applicator/20260129_143530/backups

Files found: 12

  [OK] MyDialog.lua
  [OK] Settings.lua
  [OK] Upload.lua
  [OK] Export.lua
  ...

Restore these 12 file(s)? [y/N]: y

============================================================
RESTORATION
============================================================

  [OK] MyDialog.lua
  [OK] Settings.lua
  [OK] Upload.lua
  [OK] Export.lua
  ...

Delete the .bak files? [y/N]: n

============================================================
SUMMARY
============================================================
Files restored: 12

Done!
```

### Backup Structure

Restore_backup supports two structures:

**1. __i18n_tmp__ structure (recommended, since v2.0):**

```
myPlugin.lrplugin/
├── MyDialog.lua              ← File to restore
├── Settings.lua
└── __i18n_tmp__/
    └── Applicator/
        ├── 20260129_143530/
        │   └── backups/
        │       ├── MyDialog.lua.bak    ← Source
        │       └── Settings.lua.bak
        └── 20260127_091234/
            └── backups/
                └── ...
```

**2. Legacy structure (old):**

```
myPlugin.lrplugin/
├── MyDialog.lua              ← File to restore
├── MyDialog.lua.bak          ← Source (side by side)
├── Settings.lua
└── Settings.lua.bak
```

The tool automatically detects the available structure.

### Dry-run Mode

Dry-run mode (simulation) allows you to preview actions without modifying files.

```bash
python Restore_backup.py --dry-run ./plugin.lrplugin
```

Output:
```
============================================================
RESTORATION (SIMULATION)
============================================================

  [SIMULATION] MyDialog.lua
  [SIMULATION] Settings.lua
  [SIMULATION] Upload.lua
  ...

============================================================
SUMMARY
============================================================
Files that would be restored: 12

!!! SIMULATION MODE - No files modified

Done!
```

### Managing Multiple Sessions

If multiple Applicator sessions exist, the tool allows you to choose which one to restore:

```
Applicator sessions with available backups:
------------------------------------------------------------
  1. 2026-01-29 14:35:30 (12 file(s))  ← Most recent
  2. 2026-01-28 10:20:15 (12 file(s))
  3. 2026-01-27 09:12:34 (11 file(s))
  0. Cancel
```

**In CLI mode**, the most recent session is automatically selected.

### Deleting Backups

After restoration, the tool offers to delete the `.bak` files:

```
Delete the .bak files? [y/N]: y

Deleting .bak files:
  [OK] Deleted: MyDialog.lua.bak
  [OK] Deleted: Settings.lua.bak
  ...

[OK] 12 .bak file(s) deleted
```

**Recommendation:** Keep the backups as long as you're not sure of the result. You can always delete them later with `Delete_temp_dir.py`.

### Advanced Use Cases

**Restore a specific session:**

1. List available sessions:
```bash
ls myPlugin.lrplugin/__i18n_tmp__/2_Applicator/
```

2. Note the timestamp of the desired session

3. In interactive mode, choose this session from the menu

**Restore after multiple applications:**

If you have applied Applicator several times, the backups from each session are preserved:

```
Applicator/
├── 20260127_091234/    ← First application
│   └── backups/
├── 20260129_143530/    ← Second application (with modifications)
│   └── backups/
└── 20260130_101500/    ← Third application
    └── backups/
```

To return to the state before the second application, restore the session `20260127_091234`.

**Selectively restore:**

To restore only certain files:

1. Manually copy the desired `.bak` files:
```bash
cp myPlugin.lrplugin/__i18n_tmp__/2_Applicator/<timestamp>/backups/MyDialog.lua.bak \
   myPlugin.lrplugin/MyDialog.lua
```

2. Or delete the unwanted `.bak` files before running the script

### Integration with Git

If your plugin is versioned with Git, an alternative to Restore_backup is:

```bash
# View modifications
git diff

# Restore all files
git checkout HEAD -- myPlugin.lrplugin/*.lua

# Restore a specific file
git checkout HEAD -- myPlugin.lrplugin/MyDialog.lua
```

**Advantage of Restore_backup:** Restores from local backups, even if you have already committed the modifications in Git.

## General FAQ

### Should I delete __i18n_tmp__ before each new execution?

No, the temporary folder can contain multiple timestamped executions. Each tool creates a new dated subfolder. Delete only when disk space becomes an issue.

### Are backups created automatically?

Yes, Applicator automatically creates `.bak` backups of all modified files (unless you use `--no-backup`).

### Can I restore after deleting __i18n_tmp__?

No, the backups are in `__i18n_tmp__/2_Applicator/`. If you delete them, you can no longer restore them with this tool. Use Git or your own backups.

### Do the tools work on Linux/Mac?

Yes, both scripts are cross-platform compatible (Windows, Linux, macOS).

### How to automate cleanup?

You can create a cron script or scheduled task:

```bash
#!/bin/bash
# cleanup_old_backups.sh

PLUGIN_PATH="./myPlugin.lrplugin"
I18N_DIR="$PLUGIN_PATH/__i18n_tmp__"

# Delete folders older than 30 days
find "$I18N_DIR" -type d -mtime +30 -exec rm -rf {} \;
```

**Warning:** Test your script thoroughly before automating it.

### Can I restore manually without the script?

Yes, simply copy the `.bak` files:

```bash
# __i18n_tmp__ structure
cp myPlugin/__i18n_tmp__/2_Applicator/<timestamp>/backups/*.bak myPlugin/

# Then rename to remove .bak
for f in myPlugin/*.lua.bak; do mv "$f" "${f%.bak}"; done
```

## Troubleshooting

### Delete_temp_dir.py - Permission error

**Symptom:**
```
✗ Permission denied: [Errno 13] Permission denied
```

**Solutions:**
1. Close all programs accessing the folder (editors, explorers)
2. Restart the terminal as administrator (Windows)
3. Check folder permissions with `ls -la` (Linux/Mac)

### Restore_backup.py - No backup found

**Symptom:**
```
No .bak files found.
Nothing to restore.
```

**Possible causes:**
1. Applicator has never been executed on this plugin
2. Applicator was launched with `--no-backup`
3. The `__i18n_tmp__` folder was deleted
4. The `.bak` files were manually deleted

**Solutions:**
1. Check that the plugin path is correct
2. Check for the presence of `__i18n_tmp__/2_Applicator/`
3. Use Git to restore: `git checkout HEAD -- *.lua`

### Restore_backup.py - Files partially restored

**Symptom:**
```
  [OK] MyDialog.lua
  [FAIL] Settings.lua - Error: Permission denied
  [OK] Upload.lua
```

**Solutions:**
1. Close the problematic file if it's open in an editor
2. Check file permissions
3. Restart the script for the failed files

### File name encoding

If file names contain special or accented characters, ensure your terminal supports UTF-8.

**Windows:**
```cmd
chcp 65001
```

**Linux/Mac:**
```bash
export LANG=en_US.UTF-8
```

## Performance

These two tools are very fast as they perform simple file system operations.

**Typical times:**

- **Delete_temp_dir.py**: 1-2 seconds (depends on folder size)
- **Restore_backup.py**: < 1 second for 10-20 files

## Integration in a Workflow

### Complete workflow with cleanup

```bash
#!/bin/bash
# complete_workflow.sh

PLUGIN="./myPlugin.lrplugin"

# 1. Extraction
python 1_Extractor/Extractor_main.py --plugin-path "$PLUGIN"

# 2. Application (with confirmation)
python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN" --dry-run
read -p "Apply? [y/N] " response
if [[ $response =~ ^[Yy]$ ]]; then
  python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN"
fi

# 3. Test in Lightroom
echo "Test in Lightroom, then press Enter..."
read

# 4. If OK, clean up
read -p "Delete temporary files? [y/N] " response
if [[ $response =~ ^[Yy]$ ]]; then
  python 9_Tools/Delete_temp_dir.py
fi
```

### Workflow with automatic restoration

```bash
#!/bin/bash
# safe_apply.sh

PLUGIN="./myPlugin.lrplugin"

# Backup before application
BACKUP_DIR="/tmp/plugin_backup_$(date +%s)"
cp -r "$PLUGIN" "$BACKUP_DIR"

# Apply
python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN"

# Test
echo "Test in Lightroom."
read -p "Result OK? [y/N] " response

if [[ ! $response =~ ^[Yy]$ ]]; then
  echo "Restoring backups..."
  python 9_Tools/Restore_backup.py "$PLUGIN"
  echo "Or full restoration from external backup:"
  echo "  rm -rf $PLUGIN && cp -r $BACKUP_DIR $PLUGIN"
fi
```

## Contributions

To improve the tools, you can:
- Add an option to delete only sessions older than X days
- Improve error handling for specific cases
- Add batch mode to process multiple plugins
- Create a graphical interface

Feel free to propose your modifications!

## Additional Resources

- **Python shutil**: [shutil Documentation](https://docs.python.org/3/library/shutil.html) (file copy/deletion)
- **Python os.path**: [os.path Documentation](https://docs.python.org/3/library/os.path.html)
- **File handling**: [Real Python - Working With Files](https://realpython.com/working-with-files-in-python/)

---

**Developed by Julien MOREAU with the help of Claude (Anthropic)**

For any questions or issues, consult the main README or open an issue on the GitHub repository.
