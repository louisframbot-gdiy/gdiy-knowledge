#!/usr/bin/env python3
"""
fix_yaml.py — Corrige les guillemets imbriqués dans les frontmatter YAML
Usage : python3 fix_yaml.py
À exécuter depuis la racine de gdiy-knowledge/
"""
import os, re
from pathlib import Path

CONTENT = Path("content")
fixed_count = 0

def fix_content(text):
    if not text.startswith('---'):
        return text, False
    end = text.find('---', 3)
    if end == -1:
        return text, False
    
    frontmatter = text[3:end]
    body = text[end:]
    fixed_lines = []
    changed = False
    
    for line in frontmatter.split('\n'):
        # Pattern : key: "valeur avec "guillemets" imbriqués"
        match = re.match(r'^(\s*[^:]+:\s*)"(.*)"(\s*)$', line)
        if match and '"' in match.group(2):
            inner = match.group(2).replace('"', "'")
            fixed_lines.append(f'{match.group(1)}"{inner}"{match.group(3)}')
            changed = True
        else:
            fixed_lines.append(line)
    
    if changed:
        return '---' + '\n'.join(fixed_lines) + body, True
    return text, False

for md_file in CONTENT.rglob("*.md"):
    try:
        content = md_file.read_text(encoding='utf-8')
        fixed, changed = fix_content(content)
        if changed:
            md_file.write_text(fixed, encoding='utf-8')
            print(f"Corrigé : {md_file}")
            fixed_count += 1
    except Exception as e:
        print(f"Erreur sur {md_file}: {e}")

print(f"\n{fixed_count} fichier(s) corrigé(s).")
