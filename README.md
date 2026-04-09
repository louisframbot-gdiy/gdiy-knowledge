# GDIY Knowledge

Base de connaissances du podcast Génération Do It Yourself.

**Site live :** https://louisframbot-gdiy.github.io/gdiy-knowledge

---

## Stack

- **Obsidian** — éditeur de notes (vault = dossier `content/`)
- **Quartz v4** — générateur de site statique
- **GitHub Actions** — build + déploiement automatique à chaque push
- **GitHub Pages** — hébergement du site

## Structure du vault

```
content/
├── index.md              ← Page d'accueil (Génération Do It Yourself)
├── Épisodes/             ← Une note par épisode (ep-528.md, etc.)
├── Invités/              ← Une note par invité (kenneth-schlenker.md, etc.)
├── Livres/               ← Une note par livre recommandé
├── Sujets/               ← Pages thématiques transversales
└── Newsletter/           ← Contenu newsletter (exclu du site public)
```

## Pipeline

```
Modifier une note dans Obsidian
    → autopush.py détecte (toutes les 10s, push après 30s d'inactivité)
    → commit + push sur main
    → GitHub Actions build Quartz (~1 min)
    → Site mis à jour sur GitHub Pages
```

## Lancer autopush

```bash
cd ~/Downloads/gdiy-knowledge
python3 autopush.py
```

## Tags

Chaque note utilise des tags dans le frontmatter YAML :

- `épisodes` — pages épisodes
- `invités` — pages invités
- `livres` — pages livres
- `sujets` — pages sujets
- Tags thématiques : `entrepreneuriat`, `technologie`, `société`, `management`, etc.

## Règles wikilinks

`[[nom-de-la-note]]` uniquement — sans chemin, sans alias.  
Ne jamais créer un wikilink vers une note qui n'existe pas encore.
