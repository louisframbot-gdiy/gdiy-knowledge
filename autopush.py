#!/usr/bin/env python3
"""
GDIY Knowledge — Auto Push
Surveille le dossier content/ et push automatiquement sur GitHub dès qu'un fichier change.
Usage : python3 autopush.py
"""

import time
import subprocess
import os
from pathlib import Path

REPO_DIR = Path(__file__).parent

def git(cmd):
    result = subprocess.run(
        ["git"] + cmd,
        cwd=REPO_DIR,
        capture_output=True,
        text=True
    )
    return result.stdout.strip(), result.returncode

def has_changes():
    stdout, _ = git(["status", "--porcelain"])
    return bool(stdout.strip())

def push_changes():
    print(f"[autopush] Changements détectés → commit + push...")
    git(["add", "-A"])
    git(["commit", "-m", "auto: mise à jour notes"])
    stdout, code = git(["push", "origin", "main"])
    if code == 0:
        print(f"[autopush] Push réussi. Le site se met à jour dans ~1 minute.")
    else:
        print(f"[autopush] Erreur push : {stdout}")

def main():
    print(f"[autopush] Surveillance de {REPO_DIR}/content")
    print(f"[autopush] Toute modification → push automatique sur GitHub")
    print(f"[autopush] Ctrl+C pour arrêter\n")

    pending = False
    pending_since = None

    while True:
        time.sleep(10)

        if has_changes():
            if not pending:
                pending = True
                pending_since = time.time()
                print(f"[autopush] Modification détectée, attente 30s avant push...")

            if time.time() - pending_since >= 30:
                push_changes()
                pending = False
                pending_since = None
        else:
            pending = False
            pending_since = None

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[autopush] Arrêté.")
