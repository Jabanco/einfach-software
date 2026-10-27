#!/usr/bin/env python3
"""Baut die Website aus src/page.html.

Schrift und Fotos werden als data:-URIs eingebettet, damit die Seite nichts
von fremden Servern nachlädt (keine Google Fonts, kein CDN).

Ergebnis:
  docs/                       die öffentliche Website (GitHub Pages liest diesen Ordner)
    index.html                vollständige Seite
    datenschutz/ impressum/   kurze Adressen für E-Mails, leiten auf den passenden
    agb/ abmelden/            Abschnitt der Startseite weiter
  dist/einfach-software.html  Inhalt ohne <html>-Gerüst (für den Artifact-Link)

Fotos: assets/max.jpg, assets/sebastian.jpg, assets/jarek.jpg (auch .png/.webp).
Fehlt ein Foto, erscheinen die Initialen.
"""
import base64
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
DIST = ROOT / "dist"
PAGES = ROOT / "docs"

INITIALS = {"max": "MC", "sebastian": "SW", "jarek": "JE"}
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}

# Kurze Adresse -> Anker auf der Startseite. /datenschutz zeigt den Hinweis für
# angeschriebene Betriebe, denn genau den verlinken wir in unseren E-Mails.
SHORT_LINKS = {
    "datenschutz": "interessenten",
    "impressum": "impressum",
    "agb": "agb",
    "abmelden": "abmelden",
}

REDIRECT = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Einfach Software</title>
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=../#{anchor}">
<script>location.replace("../#{anchor}");</script>
</head>
<body><p><a href="../#{anchor}">Weiter zu Einfach Software</a></p></body>
</html>
"""


def b64(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def photo(key: str):
    for ext, mime in MIME.items():
        path = ASSETS / f"{key}{ext}"
        if path.exists():
            return f"data:{mime};base64,{b64(path)}"
    return None


def avatar(match: re.Match) -> str:
    key, size = match.group(1), match.group(2)
    src = photo(key)
    if src:
        return f'<img class="avatar avatar--{size}" src="{src}" alt="" width="320" height="320" decoding="async">'
    return f'<span class="avatar avatar--{size} avatar--mono" aria-hidden="true">{INITIALS[key]}</span>'


def main() -> None:
    page = (ROOT / "src" / "page.html").read_text(encoding="utf-8")
    page = page.replace("{{FONT_ARCHIVO}}", b64(ASSETS / "archivo-latin-wdth-normal.woff2"))
    page = re.sub(r"<!--avatar:(\w+):(\w+)-->", avatar, page)

    DIST.mkdir(exist_ok=True)
    (DIST / "einfach-software.html").write_text(page, encoding="utf-8")

    # Öffentliche Seite: vollständiges Dokument mit Sprache und Viewport.
    head_end = page.index("</style>") + len("</style>")
    head, body = page[:head_end], page[head_end:]
    full = (
        '<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f"{head}\n</head>\n<body>{body}</body>\n</html>\n"
    )
    PAGES.mkdir(exist_ok=True)
    (PAGES / "index.html").write_text(full, encoding="utf-8")
    (PAGES / ".nojekyll").write_text("", encoding="utf-8")
    for slug, anchor in SHORT_LINKS.items():
        (PAGES / slug).mkdir(exist_ok=True)
        (PAGES / slug / "index.html").write_text(REDIRECT.format(anchor=anchor), encoding="utf-8")

    missing = [k for k in INITIALS if not photo(k)]
    print(f"docs/index.html {len(full) // 1024} KB, dist/einfach-software.html {len(page) // 1024} KB")
    print("Kurze Adressen:", ", ".join(f"/{s}" for s in SHORT_LINKS))
    print("Initialen statt Foto für:", ", ".join(missing) if missing else "niemanden")


if __name__ == "__main__":
    main()
