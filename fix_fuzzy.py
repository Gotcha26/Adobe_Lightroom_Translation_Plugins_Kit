#!/usr/bin/env python3
import re

po_file = r"d:\Gotcha\Documents\DIY\GitHub\Adobe_Lightroom_Translation_Plugins_Kit\locale\en\LC_MESSAGES\messages.po"

with open(po_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern: #, fuzzy\nmsgid "..."\nmsgstr ""
# Strategy: Use msgid as msgstr (English is often the source)
pattern = r'#, fuzzy\nmsgid "([^"]+)"\nmsgstr ""'

def replacer(match):
    msgid = match.group(1)
    # Remove #, fuzzy and keep msgid -> msgstr with translated value
    return f'msgid "{msgid}"\nmsgstr "{msgid}"'

# Apply replacement
new_content = re.sub(pattern, replacer, content)

with open(po_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Conversion terminée !")
