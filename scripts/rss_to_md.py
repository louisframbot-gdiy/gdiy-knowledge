#!/usr/bin/env python3
"""
GDIY RSS → Quartz .md generator (v2 — full structured extraction)
Usage: python rss_to_md.py <xml_file>
"""

import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

# ── Paths
SCRIPT_DIR   = Path(__file__).parent
PROJECT_DIR  = SCRIPT_DIR.parent
CONTENT_DIR  = PROJECT_DIR / "content"
EPISODES_DIR = CONTENT_DIR / "episodes"
GUESTS_DIR   = CONTENT_DIR / "guests"
TOPICS_DIR   = CONTENT_DIR / "topics"
BOOKS_DIR    = CONTENT_DIR / "books"

NS = {
    "itunes":  "http://www.itunes.com/dtds/podcast-1.0.dtd",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

# ─────────────────────────────────────────
# HTML → plain text
# ─────────────────────────────────────────
class HTMLToText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._current_li = None
        self._in_li = False

    def handle_starttag(self, tag, attrs):
        if tag in ("p", "br"):
            self.parts.append("\n")
        elif tag == "li":
            self._in_li = True
            self.parts.append("\n- ")
        elif tag in ("ul", "ol"):
            self.parts.append("\n")
        elif tag == "strong" or tag == "b":
            self.parts.append("**")

    def handle_endtag(self, tag):
        if tag in ("strong", "b"):
            self.parts.append("**")
        elif tag == "li":
            self._in_li = False
        elif tag in ("p",):
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        text = "".join(self.parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

def html_to_text(html: str) -> str:
    if not html:
        return ""
    parser = HTMLToText()
    parser.feed(html)
    return parser.get_text()

def html_to_md_links(html: str) -> list[dict]:
    """Extract list items as {text, url} from HTML <ul><li><a href...>"""
    items = []
    for m in re.finditer(r'<li[^>]*>.*?<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL):
        url  = m.group(1).strip()
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if text:
            items.append({"text": text, "url": url})
    # Also catch bare <li> without links
    for m in re.finditer(r'<li[^>]*>((?:(?!<li).)*?)</li>', html, re.DOTALL):
        content = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if content and not any(i["text"] == content for i in items):
            items.append({"text": content, "url": ""})
    return items

# ─────────────────────────────────────────
# Slugify
# ─────────────────────────────────────────
def yaml_str(value: str) -> str:
    """Safely escape a string for YAML double-quoted values."""
    if not value:
        return ""
    # Replace double quotes with typographic quote to avoid YAML breakage
    return value.replace('"', '\\"').replace("\n", " ").strip()

def slugify(text: str) -> str:
    text = text.lower().strip()
    for src, dst in [("àáâãäå","a"),("èéêë","e"),("ìíîï","i"),
                     ("òóôõö","o"),("ùúûü","u"),("ýÿ","y"),("ñ","n"),("ç","c")]:
        for c in src:
            text = text.replace(c, dst)
    text = re.sub(r"[^a-z0-9\s\-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

# ─────────────────────────────────────────
# Title parsing
# ─────────────────────────────────────────
def parse_title(raw: str):
    """
    '#532 - Dominique Schelcher - Coopérative U - Description'
    → ep_num=532, guest='Dominique Schelcher', subtitle='Coopérative U - Description'
    Also handles: 'VO', 'VF', 'BONUS', 'BEST OF' prefixes
    """
    raw = raw.strip()
    # Match #NNN - ...
    m = re.match(r"#(\d+)\s*[-–]\s*(.*)", raw)
    if not m:
        return None, None, raw, raw

    ep_num = int(m.group(1))
    rest   = m.group(2).strip()

    # Check for VO/VF/BONUS prefix before guest name
    prefix = ""
    pm = re.match(r"^(VO|VF|BEST OF|BONUS)\s*[-–]\s*(.*)", rest, re.IGNORECASE)
    if pm:
        prefix = pm.group(1).upper()
        rest   = pm.group(2).strip()

    # Split on " - ": first part = guest, rest = subtitle
    parts = re.split(r"\s*[-–]\s*", rest, maxsplit=1)
    guest    = parts[0].strip() if parts else ""
    subtitle = parts[1].strip() if len(parts) > 1 else ""

    # Clean title = guest + subtitle (or just subtitle if no guest)
    clean_title = f"{guest} — {subtitle}" if subtitle else guest
    if prefix:
        clean_title = f"[{prefix}] {clean_title}"

    return ep_num, guest, subtitle, clean_title

# ─────────────────────────────────────────
# Description sectioning
# ─────────────────────────────────────────
SECTION_MARKERS = {
    "timeline":       r"<strong[^>]*>\s*TIMELINE\s*:?\s*</strong>",
    "books":          r"<strong[^>]*>\s*Les\s+recommandations\s+de\s+lecture\s*:?\s*</strong>",
    "related":        r"<strong[^>]*>\s*Les\s+anciens\s+épisodes\s+de\s+GDIY\s+mentionnés\s*:?\s*</strong>",
    "mentions":       r"<strong[^>]*>\s*Nous\s+avons\s+parlé\s+de\s*:?\s*</strong>",
    "sponsors":       r"Un\s+grand\s+MERCI\s+à\s+nos\s+sponsors",
}

def split_sections(html: str) -> dict:
    """Split description HTML into named sections."""
    positions = {}
    for key, pattern in SECTION_MARKERS.items():
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            positions[key] = m.start()

    # Sort by position
    ordered = sorted(positions.items(), key=lambda x: x[1])

    sections = {}
    for i, (key, start) in enumerate(ordered):
        end = ordered[i+1][1] if i+1 < len(ordered) else len(html)
        sections[key] = html[start:end]

    # Pitch = everything before first section marker
    first_pos = ordered[0][1] if ordered else len(html)
    sections["pitch"] = html[:first_pos]

    return sections

def extract_timeline(html: str) -> list[dict]:
    """Extract timestamps from TIMELINE section."""
    entries = []
    for m in re.finditer(r"(\d{2}:\d{2}:\d{2})\s*:?\s*([^\n<]+)", html):
        ts   = m.group(1)
        desc = m.group(2).strip().rstrip("</li>").strip()
        if desc:
            entries.append({"ts": ts, "title": desc})
    return entries

def extract_books(html: str) -> list[dict]:
    """Extract books with Amazon links."""
    books = []
    # Pattern: <li><a href="https://amzn.to/...">Title, par Author</a></li>
    for m in re.finditer(r'href=["\']([^"\']*(?:amzn\.to|amazon)[^"\']*)["\'][^>]*>(.*?)</a>', html, re.DOTALL):
        url  = m.group(1).strip()
        text = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if not text:
            continue
        # Try to split "Title, par Author" or "Title par Author"
        parts = re.split(r",?\s+par\s+", text, maxsplit=1, flags=re.IGNORECASE)
        title  = parts[0].strip()
        author = parts[1].strip() if len(parts) > 1 else ""
        books.append({"title": title, "author": author, "url": url})
    # Fallback: plain li items
    if not books:
        for item in html_to_md_links(html):
            parts = re.split(r",?\s+par\s+", item["text"], maxsplit=1, flags=re.IGNORECASE)
            books.append({
                "title":  parts[0].strip(),
                "author": parts[1].strip() if len(parts) > 1 else "",
                "url":    item["url"],
            })
    return books

def extract_related_episodes(html: str) -> list[dict]:
    """Extract related GDIY episode numbers and titles."""
    episodes = []
    for m in re.finditer(r"#(\d+)[^>]*[-–][^>]*?(?:href=[\"'][^\"']+[\"'][^>]*>)?([^<\n]+)", html):
        num   = int(m.group(1))
        title = m.group(2).strip().lstrip("-–").strip()
        if title and num not in [e["num"] for e in episodes]:
            episodes.append({"num": num, "title": title})
    return episodes[:10]

def extract_guest_linkedin(html: str) -> str:
    """Find LinkedIn URL for guest."""
    m = re.search(r'href=["\'](https://www\.linkedin\.com/in/[^"\']+)["\']', html)
    return m.group(1) if m else ""

def extract_pitch(html: str) -> str:
    """Clean up the pitch section."""
    # Remove promo lines (formation, sponsors...)
    text = html_to_text(html)
    lines = text.split("\n")
    clean = []
    skip_patterns = [
        r"offre de lancement", r"formation GDIY", r"Hébergé par Audiomeans",
        r"grand MERCI", r"squarespace", r"qonto", r"brevo", r"etoro",
        r"payfit", r"club med", r"cuure", r"Vous souhaitez sponsoriser",
        r"Contactez mon label", r"orsomedia",
    ]
    for line in lines:
        if any(re.search(p, line, re.IGNORECASE) for p in skip_patterns):
            continue
        clean.append(line)
    return "\n".join(clean).strip()

# ─────────────────────────────────────────
# Date parsing
# ─────────────────────────────────────────
def parse_date(raw: str) -> str:
    for fmt in ["%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"]:
        try:
            return datetime.strptime(raw[:31].strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            pass
    return raw[:10] if raw else ""

# ─────────────────────────────────────────
# Parse RSS
# ─────────────────────────────────────────
def parse_rss(xml_path: str) -> list[dict]:
    print(f"Parsing {xml_path} ...")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    items = root.findall("./channel/item")
    print(f"  {len(items)} items trouvés")

    episodes = []
    skipped  = 0

    for item in items:
        raw_title = item.findtext("title", "").strip()
        ep_num, guest, subtitle, clean_title = parse_title(raw_title)

        # Skip non-numbered items (trailers, annonces)
        if ep_num is None:
            skipped += 1
            continue

        # Description (CDATA)
        desc_html = item.findtext("description", "")
        if not desc_html:
            ce = item.find(f"{{{NS['content']}}}encoded")
            desc_html = ce.text if ce is not None and ce.text else ""

        # Section splitting
        secs    = split_sections(desc_html)
        pitch   = extract_pitch(secs.get("pitch", ""))
        timeline = extract_timeline(secs.get("timeline", ""))
        books   = extract_books(secs.get("books", ""))
        related = extract_related_episodes(secs.get("related", ""))
        mentions = html_to_md_links(secs.get("mentions", ""))
        linkedin = extract_guest_linkedin(desc_html)

        # Metadata
        pub_date  = parse_date(item.findtext("pubDate", ""))
        duration  = item.findtext(f"{{{NS['itunes']}}}duration", "")
        img_el    = item.find(f"{{{NS['itunes']}}}image")
        image_url = img_el.get("href", "") if img_el is not None else ""
        enc_el    = item.find("enclosure")
        audio_url = enc_el.get("url", "") if enc_el is not None else ""
        link      = item.findtext("link", "").strip()

        # Build podcast URL (prefer gdiy.fr link)
        podcast_url = link or audio_url

        episodes.append({
            "ep_num":    ep_num,
            "guest":     guest,
            "subtitle":  subtitle,
            "title":     clean_title,
            "raw_title": raw_title,
            "pub_date":  pub_date,
            "duration":  duration,
            "image_url": image_url,
            "audio_url": audio_url,
            "podcast_url": podcast_url,
            "linkedin":  linkedin,
            "pitch":     pitch,
            "timeline":  timeline,
            "books":     books,
            "related":   related,
            "mentions":  mentions,
        })

    episodes.sort(key=lambda x: x["ep_num"], reverse=True)
    print(f"  Épisodes valides : {len(episodes)} | Ignorés : {skipped}")
    return episodes

# ─────────────────────────────────────────
# .md generators
# ─────────────────────────────────────────
def episode_to_md(ep: dict) -> str:
    num          = ep["ep_num"]
    guest        = ep["guest"]
    subtitle     = ep["subtitle"]
    title        = ep["title"]
    date         = ep["pub_date"]
    image_url    = ep["image_url"]
    podcast_url  = ep["podcast_url"]
    duration     = ep["duration"]
    linkedin     = ep["linkedin"]
    pitch        = ep["pitch"]
    timeline     = ep["timeline"]
    books        = ep["books"]
    related      = ep["related"]
    mentions     = ep["mentions"]
    slug_guest   = slugify(guest) if guest else ""

    # ── YAML frontmatter
    lines = ["---"]
    ep_title_yaml = yaml_str(f"#{num} — {guest}{(' — ' + subtitle) if subtitle else ''}")
    lines.append(f'title: "{ep_title_yaml}"')
    lines.append(f"episode_number: {num}")
    lines.append(f'date: "{date}"')
    if guest:
        lines.append(f'guest: "{yaml_str(guest)}"')
        lines.append(f'guest_slug: "{slug_guest}"')
    if subtitle:
        lines.append(f'subtitle: "{yaml_str(subtitle)}"')
    if image_url:
        lines.append(f'cover: "{image_url}"')
    if podcast_url:
        lines.append(f'podcast_url: "{podcast_url}"')
    if duration:
        lines.append(f'duration: "{duration}"')
    if linkedin:
        lines.append(f'linkedin: "{linkedin}"')
    # Tags: episode + year
    year = date[:4] if date else "?"
    lines.append(f'tags: ["episode", "{year}"]')
    lines.append("draft: false")
    lines.append("---")
    lines.append("")

    # ── Cover image
    if image_url:
        lines.append(f'![{guest or title}]({image_url})')
        lines.append("")

    # ── Title
    lines.append(f"# #{num} — {guest}")
    if subtitle:
        lines.append(f"### {subtitle}")
    lines.append("")

    # ── Meta pills
    meta = []
    if guest and slug_guest:
        meta.append(f"**Invité :** [[guests/{slug_guest}|{guest}]]")
    meta.append(f"**Date :** {date}")
    if duration:
        meta.append(f"**Durée :** {duration}")
    if podcast_url:
        meta.append(f"**[Écouter l'épisode]({podcast_url})**")
    if linkedin:
        meta.append(f"[LinkedIn de {guest}]({linkedin})")
    for m_item in meta:
        lines.append(m_item + "  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Pitch
    if pitch:
        lines.append("## Présentation")
        lines.append("")
        lines.append(pitch)
        lines.append("")

    # ── Timeline
    if timeline:
        lines.append("## Timeline")
        lines.append("")
        for entry in timeline:
            lines.append(f"- `{entry['ts']}` {entry['title']}")
        lines.append("")

    # ── Books
    if books:
        lines.append("## Livres recommandés")
        lines.append("")
        for b in books:
            author_str = f" — *{b['author']}*" if b["author"] else ""
            link_str   = f" ([Amazon]({b['url']}))" if b["url"] else ""
            slug_b     = slugify(b["title"])
            lines.append(f"- [[books/{slug_b}|{b['title']}]]{author_str}{link_str}")
        lines.append("")

    # ── References / mentions
    if mentions:
        lines.append("## Références et mentions")
        lines.append("")
        for ref in mentions:
            if ref["url"]:
                lines.append(f"- [{ref['text']}]({ref['url']})")
            else:
                lines.append(f"- {ref['text']}")
        lines.append("")

    # ── Related episodes
    if related:
        lines.append("## Épisodes mentionnés")
        lines.append("")
        for rel in related:
            lines.append(f"- [[episodes/ep-{rel['num']}|#{rel['num']} — {rel['title']}]]")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Note générée automatiquement depuis le flux RSS GDIY.*")
    lines.append("")

    return "\n".join(lines)


def guest_to_md(name: str, episodes: list[dict], linkedin: str = "") -> str:
    slug = slugify(name)
    lines = ["---"]
    lines.append(f'title: "{yaml_str(name)}"')
    lines.append(f'tags: ["guest"]')
    if linkedin:
        lines.append(f'linkedin: "{linkedin}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# {name}")
    lines.append("")
    if linkedin:
        lines.append(f"[LinkedIn]({linkedin})")
        lines.append("")
    lines.append(f"**{len(episodes)} épisode(s)**")
    lines.append("")
    lines.append("## Épisodes")
    lines.append("")
    for ep in sorted(episodes, key=lambda x: x["ep_num"], reverse=True):
        num = ep["ep_num"]
        lines.append(f"- [[episodes/ep-{num}|#{num} — {ep['title']}]]")
    lines.append("")
    return "\n".join(lines)


def book_to_md(title: str, author: str, url: str, episodes: list[dict]) -> str:
    slug = slugify(title)
    lines = ["---"]
    lines.append(f'title: "{yaml_str(title)}"')
    if author:
        lines.append(f'author: "{yaml_str(author)}"')
    if url:
        lines.append(f'amazon_url: "{url}"')
    lines.append(f'tags: ["book"]')
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    if author:
        lines.append(f"*par {author}*")
    lines.append("")
    if url:
        lines.append(f"[Voir sur Amazon]({url})")
        lines.append("")
    lines.append(f"Mentionné dans **{len(episodes)} épisode(s)**.")
    lines.append("")
    lines.append("## Épisodes qui recommandent ce livre")
    lines.append("")
    for ep in sorted(episodes, key=lambda x: x["ep_num"], reverse=True):
        num = ep["ep_num"]
        lines.append(f"- [[episodes/ep-{num}|#{num} — {ep['title']}]]")
    lines.append("")
    return "\n".join(lines)

# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def main():
    xml_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not xml_path or not Path(xml_path).exists():
        print("Usage: python rss_to_md.py <rss_file.xml>")
        sys.exit(1)

    episodes = parse_rss(xml_path)

    # Create directories
    for d in [EPISODES_DIR, GUESTS_DIR, BOOKS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # ── Episode .md files
    print(f"\nGénération des épisodes...")
    ep_count = 0
    for ep in episodes:
        fname = EPISODES_DIR / f"ep-{ep['ep_num']}.md"
        fname.write_text(episode_to_md(ep), encoding="utf-8")
        ep_count += 1
    print(f"  {ep_count} épisodes générés")

    # ── Guest pages
    print("Génération des pages invités...")
    guests_map: dict[str, dict] = {}  # name → {episodes, linkedin}
    for ep in episodes:
        g = ep["guest"]
        if not g:
            continue
        if g not in guests_map:
            guests_map[g] = {"episodes": [], "linkedin": ep["linkedin"]}
        guests_map[g]["episodes"].append(ep)

    for name, data in guests_map.items():
        slug = slugify(name)
        fname = GUESTS_DIR / f"{slug}.md"
        fname.write_text(
            guest_to_md(name, data["episodes"], data["linkedin"]),
            encoding="utf-8"
        )
    print(f"  {len(guests_map)} invités générés")

    # ── Book pages
    print("Génération des pages livres...")
    books_map: dict[str, dict] = {}  # slug → {title, author, url, episodes}
    for ep in episodes:
        for b in ep["books"]:
            slug_b = slugify(b["title"])
            if not slug_b:
                continue
            if slug_b not in books_map:
                books_map[slug_b] = {
                    "title": b["title"],
                    "author": b["author"],
                    "url": b["url"],
                    "episodes": [],
                }
            books_map[slug_b]["episodes"].append(ep)

    for slug_b, data in books_map.items():
        fname = BOOKS_DIR / f"{slug_b}.md"
        fname.write_text(
            book_to_md(data["title"], data["author"], data["url"], data["episodes"]),
            encoding="utf-8"
        )
    print(f"  {len(books_map)} livres générés")

    # ── Stats
    total_books    = sum(len(ep["books"]) for ep in episodes)
    total_timeline = sum(len(ep["timeline"]) for ep in episodes)
    total_related  = sum(len(ep["related"]) for ep in episodes)
    total_mentions = sum(len(ep["mentions"]) for ep in episodes)

    print(f"\n=== STATS ===")
    print(f"  Épisodes  : {ep_count}")
    print(f"  Invités   : {len(guests_map)}")
    print(f"  Livres    : {len(books_map)} (uniques) / {total_books} (total citations)")
    print(f"  Chapitres timeline : {total_timeline}")
    print(f"  Épisodes liés : {total_related}")
    print(f"  Références : {total_mentions}")

    # Save JSON for debugging
    json_path = SCRIPT_DIR / "episodes_raw.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)
    print(f"\nJSON brut : {json_path}")
    print("Terminé.")

if __name__ == "__main__":
    main()
