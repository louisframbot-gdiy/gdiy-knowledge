#!/usr/bin/env python3
"""
GDIY — Script de transformation des épisodes
=============================================
Ce script transforme les fichiers .md existants vers le nouveau template GDIY.
Il extrait automatiquement :
- Les livres mentionnés
- Les épisodes cités
- Les personnes mentionnées
Et génère :
- Les pages épisodes reformatées
- Les pages invités (squelette)
- Les pages livres (squelette)

Usage :
  python3 transform_episodes.py --input ./content --output ./output
"""

import os
import re
import yaml
import argparse
from pathlib import Path


# ─── LIENS PODCASTS GDIY ──────────────────────────────────────────────────────

PODCAST_LINKS_HTML = """
<div style="display:flex;gap:10px;flex-wrap:wrap;margin:28px 0;align-items:center;">

  <a href="https://podcasts.apple.com/fr/podcast/g%C3%A9n%C3%A9ration-do-it-yourself/id1209142994" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;background:#872EC4;color:white;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 4.5a7.5 7.5 0 110 15 7.5 7.5 0 010-15zm0 2.25a5.25 5.25 0 100 10.5 5.25 5.25 0 000-10.5zm0 2.5a.75.75 0 110 1.5.75.75 0 010-1.5zm-.375 2.5h.75v4.5h-.75V11.75z"/></svg>
    Apple Podcasts
  </a>

  <a href="https://open.spotify.com/show/6jCObFeQTf0VARXdMv9iE4" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;background:#1DB954;color:white;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>
    Spotify
  </a>

  <a href="https://music.youtube.com/playlist?list=PLWT7hkKacBMKEQlMyOMt6qSzKHTGguP9I" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;background:#FF0000;color:white;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M23.495 6.205a3.007 3.007 0 00-2.088-2.088c-1.87-.501-9.396-.501-9.396-.501s-7.507-.01-9.396.501A3.007 3.007 0 00.527 6.205a31.247 31.247 0 00-.522 5.805 31.247 31.247 0 00.522 5.783 3.007 3.007 0 002.088 2.088c1.868.502 9.396.502 9.396.502s7.506 0 9.396-.502a3.007 3.007 0 002.088-2.088 31.247 31.247 0 00.5-5.783 31.247 31.247 0 00-.5-5.805zM9.609 15.601V8.408l6.264 3.602z"/></svg>
    YouTube
  </a>

  <a href="https://www.deezer.com/fr/show/53644" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;background:#A238FF;color:white;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M18.944 17.332h4.053v-1.33h-4.053zm0-4.05h4.053v-1.33h-4.053zm0-2.658h4.053V9.294h-4.053zm0-2.66h4.053V6.634h-4.053zM0 17.332h4.053v-1.33H0zm6.32 0h4.053v-1.33H6.32zm6.32 0h4.054v-1.33H12.64zm0-2.658h4.054v-1.33H12.64zm0-2.66h4.054V9.294H12.64zm0-2.66h4.054V6.634H12.64zM6.32 14.674h4.053v-1.33H6.32zm0-2.66h4.053v-1.33H6.32z"/></svg>
    Deezer
  </a>

  <a href="https://music.amazon.fr/podcasts/29c130f8-57f3-4645-bc5a-e1f9b4bbf131/g%C3%A9n%C3%A9ration-do-it-yourself" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:8px;background:#FF9900;color:white;padding:10px 18px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M13.958 10.09c0 1.232.029 2.256-.591 3.351-.502.891-1.301 1.438-2.186 1.438-1.214 0-1.922-.924-1.922-2.292 0-2.692 2.415-3.182 4.7-3.182v.685zm3.186 7.705c-.209.189-.512.201-.745.074-1.047-.872-1.234-1.276-1.814-2.106-1.734 1.769-2.962 2.299-5.209 2.299-2.66 0-4.731-1.641-4.731-4.925 0-2.565 1.391-4.309 3.37-5.164 1.715-.754 4.11-.891 5.942-1.095V6.41c0-.753.06-1.642-.384-2.294-.385-.579-1.124-.82-1.775-.82-1.205 0-2.277.618-2.54 1.897-.054.285-.261.567-.548.582l-3.061-.333c-.259-.056-.548-.266-.472-.66C5.57 2.219 8.521 1.2 11.17 1.2c1.355 0 3.124.36 4.193 1.387 1.355 1.266 1.224 2.954 1.224 4.793v4.343c0 1.306.541 1.879 1.051 2.585.178.252.217.553-.009.74l-2.485 2.747z"/></svg>
    Amazon Music
  </a>

</div>
"""

BREVO_FORM_HTML = """
<div style="background:#f8f8f8;border-radius:12px;padding:32px;margin:40px 0;">
  <p style="font-weight:700;font-size:20px;margin:0 0 6px 0;text-align:center;">Reçois le résumé complet + la mind map</p>
  <p style="color:#666;margin:0 0 24px 0;text-align:center;font-size:15px;">Abonne-toi à la newsletter GDIY — chaque épisode décrypté, chaque semaine.</p>
  <div style="text-align:center;">
    <form method="POST" action="https://9b2b3a90.sibforms.com/serve/MUIFAOokNmmE0BiSxcKiKGPkw_Oy1XNLZ-YepiLT2rrpmm9MqcKHmjuSGqFR78KqsfaK6wMfaLPfDFGbFp-s4rypSamn0m7XcvSnhvUvqNoIpDbkrTJke8SF4wJwXQUeNwfk8ZUS_ClFB4AlRM2Ms27UeZ4I_EZeLg8e6ODy9JSPheJydLoljPIijHfRKigCAtCznEKMzLD3aP99" data-type="subscription" style="display:inline-flex;gap:8px;flex-wrap:wrap;justify-content:center;">
      <input type="email" name="EMAIL" placeholder="Ton adresse email" required style="padding:12px 16px;border:1px solid #ddd;border-radius:6px;font-size:15px;min-width:260px;" />
      <input type="text" name="email_address_check" value="" style="display:none;">
      <input type="hidden" name="locale" value="fr">
      <button type="submit" style="background:#00ffad;color:#000;font-weight:700;padding:12px 24px;border:none;border-radius:6px;font-size:15px;cursor:pointer;">S'inscrire</button>
    </form>
  </div>
</div>
"""


# ─── EXTRACTEURS ──────────────────────────────────────────────────────────────

def slugify(text):
    """Convertit un texte en slug URL."""
    import unicodedata
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def clean_body(body_text):
    """Supprime l'ancien header (image, titre, métadonnées) du corps du fichier."""
    # Cas 1 : section ## Présentation explicite → prendre tout ce qui suit
    if '## Présentation' in body_text:
        parts = body_text.split('## Présentation', 1)
        text = parts[1].strip()
        # Supprimer la note de bas de page automatique
        text = re.sub(r'\*Note générée.*$', '', text, flags=re.MULTILINE)
        return text.strip()

    # Cas 2 : pas de section Présentation → supprimer le bloc header ligne par ligne
    lines = body_text.split('\n')
    cleaned = []
    skip = True
    for line in lines:
        if skip:
            # Patterns à ignorer : image, titres, métadonnées
            if re.match(r'^!\[', line): continue
            if re.match(r'^#{1,4}\s', line): continue
            if re.match(r'^\*\*', line) and ('**' in line[2:20]): continue
            if re.match(r'^\[', line) and ('](http' in line or '[[' in line): continue
            if line.strip() in ('---', ''): continue
            # Premier vrai paragraphe
            if len(line.strip()) > 40:
                skip = False
                cleaned.append(line)
        else:
            cleaned.append(line)
    return '\n'.join(cleaned)


def extract_books(body_text):
    """
    Extrait les livres mentionnés.
    Dans les fichiers existants, les livres apparaissent souvent en lignes "# Titre — auteur"
    ou "# Titre de truc de machin"
    """
    books = []
    # Pattern: lignes commençant par # mais pas ## (sections), souvent titres de livres
    lines = body_text.split('\n')
    in_books_section = False

    for line in lines:
        line = line.strip()
        # Détecter sections livres
        if re.search(r'(livres?|books?|conseille|recommande)', line, re.IGNORECASE):
            in_books_section = True

        # Lignes qui commencent par "# " (niveau 1 dans corps = souvent livre)
        if re.match(r'^# ', line) and not line.startswith('## '):
            title = line[2:].strip()
            # Exclure les titres d'épisodes GDIY (pattern "#NNN Prénom")
            if not re.match(r'^\d+', title):
                books.append(title)

    return books


def extract_mentioned_episodes(body_text):
    """Extrait les numéros d'épisodes cités dans le texte."""
    # Patterns: #92, EP 92, épisode 92, #92 Nom
    patterns = [
        r'#(\d{2,3})\s+\w',   # #92 Jean-David
        r'\bEP\.?\s*(\d{2,3})\b',
        r'épisode\s+(\d{2,3})',
    ]
    episodes = set()
    for pattern in patterns:
        matches = re.findall(pattern, body_text, re.IGNORECASE)
        episodes.update(matches)
    return sorted(list(episodes), key=int)


def extract_people(body_text):
    """Extrait les noms de personnes mentionnées (heuristique simple)."""
    # Noms en gras ou avec majuscules consécutives
    # Pattern: Prénom Nom (deux mots avec majuscules)
    pattern = r'\b([A-ZÉÀÂÙÎÊ][a-zéàâùîê]+\s+[A-ZÉÀÂÙÎÊ][A-ZÉÀÂÙÎÊ][a-zéàâùîê]*)\b'
    matches = re.findall(pattern, body_text)
    # Dédupliquer et filtrer les faux positifs communs
    exclude = {'Le Bon', 'La Grenouillère', 'Do It', 'It Yourself', 'Marketing Mania'}
    people = list(set(m for m in matches if m not in exclude))
    return people[:10]  # Max 10


def detect_episode_type(frontmatter, body_text):
    """Détecte si l'épisode est solo ou interview."""
    guest = frontmatter.get('guest', '')
    # Si le guest ressemble à un titre d'épisode plutôt qu'à un nom de personne
    solo_keywords = ['bilan', 'objectifs', 'routines', 'barre plus haut', 'débrief',
                     'best of', 'compilation', 'seul', 'solo']
    if any(kw in guest.lower() for kw in solo_keywords):
        return 'solo'
    if any(kw in body_text.lower()[:500] for kw in ['mon invité', 'cette semaine', 'je reçois']):
        return 'interview'
    # Par défaut interview si un guest_slug est présent et semble être un nom
    if frontmatter.get('guest_slug') and '-' in frontmatter.get('guest_slug', ''):
        parts = frontmatter['guest_slug'].split('-')
        if len(parts) >= 2:
            return 'interview'
    return 'interview'


# ─── GÉNÉRATEURS DE PAGES ─────────────────────────────────────────────────────

def generate_episode_page(frontmatter, body_text, books, mentioned_eps, ep_type):
    """Génère la page épisode au nouveau format."""

    guest = frontmatter.get('guest', '')
    guest_slug = frontmatter.get('guest_slug', slugify(guest))
    ep_num = frontmatter.get('episode_number', '')
    subtitle = frontmatter.get('subtitle', '')
    cover = frontmatter.get('cover', '')
    duration = frontmatter.get('duration', '')
    date = frontmatter.get('date', '')
    linkedin = frontmatter.get('linkedin', '')
    year = str(date)[:4] if date else '2020'

    # Nettoyer le corps et extraire la présentation
    clean = clean_body(body_text)
    clean = re.sub(r'\*Note générée.*$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'\n{3,}', '\n\n', clean).strip()
    presentation = clean

    # Construire les tags
    tags = [ep_type, year]
    if guest_slug and ep_type == 'interview':
        tags.insert(0, guest_slug)

    # Recommandations (livres)
    reco_section = ''
    if books:
        reco_lines = '\n'.join(f'- {b}' for b in books)
        reco_section = f"""
---

## Recommandations

{reco_lines}
"""

    # Épisodes mentionnés
    eps_section = ''
    if mentioned_eps:
        eps_links = ' · '.join(f'[EP {n}](/content/ep-{n})' for n in mentioned_eps)
        eps_section = f'\n**Épisodes mentionnés :** {eps_links}\n'

    # LinkedIn
    linkedin_line = ''
    if linkedin:
        linkedin_line = f'\n[LinkedIn de {guest}]({linkedin})\n'

    # Nouveau frontmatter
    new_tags = tags

    new_fm = f"""---
title: "EP {ep_num} — {guest}"
guest: "{guest}"
guest_slug: "{guest_slug}"
role: "{subtitle}"
episode: "{ep_num}"
cover: "{cover}"
podcast_url: "{frontmatter.get('podcast_url', '')}"
duration: "{duration}"
date: "{date}"
tags: {new_tags}
episode_type: "{ep_type}"
draft: false
---"""

    # Corps de la page
    guest_link = f'[[guests/{guest_slug}|{guest}]]' if ep_type == 'interview' else guest

    body = f"""
<img src="{cover}" alt="{guest}" style="width:100%;height:480px;object-fit:cover;object-position:center top;border-radius:12px;margin-bottom:8px;" />

# EP {ep_num} — {guest}

**{subtitle}**
{linkedin_line}
---
{PODCAST_LINKS_HTML}
---

{presentation}

---
{BREVO_FORM_HTML}
{reco_section}
{eps_section}
"""

    return new_fm + '\n' + body.strip()


def generate_guest_page(guest, guest_slug, subtitle, episodes_with_guest, linkedin=''):
    """Génère une page invité (squelette à compléter)."""

    ep_links = '\n'.join(
        f'- [[{ep["file"]}|EP {ep["number"]} — {ep["title"]}]]'
        for ep in episodes_with_guest
    )

    linkedin_line = f'- [LinkedIn]({linkedin})' if linkedin else ''

    return f"""---
title: "{guest}"
type: guest
slug: "{guest_slug}"
role: "{subtitle}"
tags: [invité, {guest_slug}]
draft: false
---

# {guest}

**{subtitle}**

{linkedin_line}

---

## À propos

<!-- TODO: Biographie complète à rédiger via Claude avec le transcript de l'épisode -->
<!-- Parcours, entreprise, vision, réalisations notables -->

*Biographie à compléter.*

---

## Épisodes GDIY

{ep_links}

---

## Liens

{linkedin_line}
"""


def generate_book_page(book_title, episodes_where_mentioned):
    """Génère une page livre."""
    slug = slugify(book_title)

    # Essayer de séparer titre et auteur (pattern "Titre de Auteur" ou "Titre — Auteur")
    author = ''
    title = book_title
    if ' — ' in book_title:
        parts = book_title.split(' — ')
        title = parts[0].strip()
        author = parts[1].strip() if len(parts) > 1 else ''
    elif ' de ' in book_title:
        parts = book_title.split(' de ', 1)
        title = parts[0].strip()
        author = parts[1].strip() if len(parts) > 1 else ''

    ep_refs = '\n'.join(f'- [[{ep}]]' for ep in episodes_where_mentioned)

    return f"""---
title: "{title}"
author: "{author}"
type: book
slug: "{slug}"
tags: [livre, ressource]
draft: false
---

# {title}

**Auteur :** {author if author else 'À compléter'}

---

## Résumé

<!-- TODO: Résumé à générer via Claude -->

*Résumé à compléter.*

---

## Mentionné dans GDIY

{ep_refs}
"""


# ─── TRAITEMENT PRINCIPAL ─────────────────────────────────────────────────────

def parse_md_file(filepath):
    """Parse un fichier .md et retourne (frontmatter_dict, body_text)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extraire le frontmatter YAML
    fm_match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not fm_match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError:
        frontmatter = {}

    body = fm_match.group(2)
    return frontmatter or {}, body


def process_all_episodes(input_dir, output_dir):
    """Traite tous les fichiers épisodes et génère les nouvelles pages."""

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Créer les dossiers de sortie
    (output_path / 'content').mkdir(parents=True, exist_ok=True)
    (output_path / 'guests').mkdir(parents=True, exist_ok=True)
    (output_path / 'books').mkdir(parents=True, exist_ok=True)

    # Dictionnaires pour agréger les données
    all_guests = {}   # guest_slug -> {guest, subtitle, episodes, linkedin}
    all_books = {}    # book_slug -> {title, episodes}

    # Récupérer tous les fichiers épisodes
    md_files = sorted(input_path.glob('**/*.md'))
    print(f"Fichiers trouvés : {len(md_files)}")

    for md_file in md_files:
        print(f"  Traitement : {md_file.name}")

        frontmatter, body = parse_md_file(md_file)
        if not frontmatter:
            print(f"    → Frontmatter vide, ignoré")
            continue

        # Extraire les données
        books = extract_books(body)
        mentioned_eps = extract_mentioned_episodes(body)
        ep_type = detect_episode_type(frontmatter, body)

        # Générer la nouvelle page épisode
        new_content = generate_episode_page(frontmatter, body, books, mentioned_eps, ep_type)

        out_file = output_path / 'content' / md_file.name
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"    → Épisode généré : {out_file.name}")

        # Agréger les données invités
        guest = frontmatter.get('guest', '')
        guest_slug = frontmatter.get('guest_slug', slugify(guest))
        subtitle = frontmatter.get('subtitle', '')
        ep_num = frontmatter.get('episode_number', '')
        linkedin = frontmatter.get('linkedin', '')

        if guest and ep_type == 'interview' and guest_slug:
            if guest_slug not in all_guests:
                all_guests[guest_slug] = {
                    'guest': guest,
                    'subtitle': subtitle,
                    'linkedin': linkedin,
                    'episodes': []
                }
            all_guests[guest_slug]['episodes'].append({
                'file': f'content/{md_file.stem}',
                'number': ep_num,
                'title': guest
            })

        # Agréger les données livres
        for book in books:
            book_slug = slugify(book)
            if book_slug not in all_books:
                all_books[book_slug] = {'title': book, 'episodes': []}
            all_books[book_slug]['episodes'].append(f'content/{md_file.stem}')

    # Générer les pages invités
    print(f"\nGénération des pages invités ({len(all_guests)})...")
    for guest_slug, data in all_guests.items():
        content = generate_guest_page(
            data['guest'], guest_slug, data['subtitle'],
            data['episodes'], data.get('linkedin', '')
        )
        out_file = output_path / 'guests' / f"{guest_slug}.md"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  → {out_file.name}")

    # Générer les pages livres
    print(f"\nGénération des pages livres ({len(all_books)})...")
    for book_slug, data in all_books.items():
        if not book_slug or len(book_slug) < 3:
            continue
        content = generate_book_page(data['title'], data['episodes'])
        out_file = output_path / 'books' / f"{book_slug}.md"
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  → {out_file.name}")

    print(f"\n✓ Terminé.")
    print(f"  Épisodes transformés : {len(list((output_path / 'content').glob('*.md')))}")
    print(f"  Pages invités créées : {len(all_guests)}")
    print(f"  Pages livres créées  : {len(all_books)}")
    print(f"\nÉtapes suivantes :")
    print(f"  1. Vérifier quelques fichiers dans {output_path}/content/")
    print(f"  2. Copier les dossiers content/, guests/, books/ dans ton repo GitHub")
    print(f"  3. Compléter les biographies invités via Claude (voir PROMPT_GUEST_BIO.md)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Transforme les épisodes GDIY vers le nouveau template')
    parser.add_argument('--input', default='./content', help='Dossier source des .md (défaut: ./content)')
    parser.add_argument('--output', default='./output', help='Dossier de sortie (défaut: ./output)')
    args = parser.parse_args()

    process_all_episodes(args.input, args.output)
