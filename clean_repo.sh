#!/bin/bash
# clean_repo.sh — Nettoie et réorganise le repo gdiy-knowledge
# Usage : bash clean_repo.sh
# À exécuter depuis la racine de gdiy-knowledge/

set -e

REPO="$(pwd)"
CONTENT="$REPO/content"

echo "=== GDIY Knowledge — Migration du repo ==="
echo "Repo : $REPO"
echo ""

# 1. Créer les nouveaux dossiers dans content/
echo "→ Création des dossiers..."
mkdir -p "$CONTENT/Épisodes"
mkdir -p "$CONTENT/Invités"
mkdir -p "$CONTENT/Livres"
mkdir -p "$CONTENT/Sujets"
mkdir -p "$CONTENT/Newsletter"

# 2. Déplacer les épisodes vers content/Épisodes/
echo "→ Migration des épisodes..."
if [ -d "$CONTENT/episodes" ]; then
  mv "$CONTENT/episodes/"*.md "$CONTENT/Épisodes/" 2>/dev/null || true
  rmdir "$CONTENT/episodes" 2>/dev/null || true
fi

# 3. Déplacer les invités vers content/Invités/
echo "→ Migration des invités..."
if [ -d "$CONTENT/guests" ]; then
  mv "$CONTENT/guests/"*.md "$CONTENT/Invités/" 2>/dev/null || true
  rmdir "$CONTENT/guests" 2>/dev/null || true
fi

# 4. Déplacer les livres vers content/Livres/
echo "→ Migration des livres..."
if [ -d "$CONTENT/books" ]; then
  mv "$CONTENT/books/"*.md "$CONTENT/Livres/" 2>/dev/null || true
  rmdir "$CONTENT/books" 2>/dev/null || true
fi
# Aussi les livres à la racine du repo (ancien emplacement)
if [ -d "$REPO/books" ]; then
  mv "$REPO/books/"*.md "$CONTENT/Livres/" 2>/dev/null || true
  rmdir "$REPO/books" 2>/dev/null || true
fi

# 5. Déplacer les sujets
echo "→ Migration des sujets..."
if [ -d "$CONTENT/topics" ]; then
  mv "$CONTENT/topics/"*.md "$CONTENT/Sujets/" 2>/dev/null || true
  rmdir "$CONTENT/topics" 2>/dev/null || true
fi

# 6. Déplacer les anciens guests/ à la racine du repo
if [ -d "$REPO/guests" ]; then
  mv "$REPO/guests/"*.md "$CONTENT/Invités/" 2>/dev/null || true
  rmdir "$REPO/guests" 2>/dev/null || true
fi

# 7. Supprimer les fichiers orphelins à la racine de content/
# (fichiers .md éparpillés qui ne sont pas index.md)
echo "→ Nettoyage des fichiers orphelins à la racine de content/..."
find "$CONTENT" -maxdepth 1 -name "*.md" ! -name "index.md" -delete

# 8. Supprimer les anciens dossiers inutiles
rm -rf "$REPO/output" 2>/dev/null || true
rm -rf "$REPO/docs" 2>/dev/null || true
rm -rf "$REPO/admin" 2>/dev/null || true

# 9. Copier le nouveau quartz.config.ts et index.md
# (à faire manuellement — voir instructions ci-dessous)

echo ""
echo "=== Migration terminée ==="
echo ""
echo "Prochaines étapes manuelles :"
echo "1. Remplacer quartz.config.ts par la version fournie"
echo "2. Remplacer content/index.md par la version fournie"
echo "3. Vérifier le résultat dans Obsidian"
echo "4. Lancer autopush.py pour déclencher le déploiement"
