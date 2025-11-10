# scrapers/tap.py (remplace uniquement scrape_spectacles)
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re, html
from urllib.parse import urljoin

BASE_URL = "https://www.tap-poitiers.com"

def _extract_bg_url(style_value: str) -> str | None:
    """Extrait l'URL depuis un style background-image, gère &quot; et quotes."""
    if not style_value:
        return None
    # Déséchapper les entités HTML (&quot;)
    style_value = html.unescape(style_value)
    # Cherche url(...) — capture tout ce qu'il y a entre les parenthèses
    m = re.search(r'url\(([^)]+)\)', style_value, flags=re.I)
    if not m:
        return None
    raw = m.group(1).strip().strip('\'"')
    return urljoin(BASE_URL, raw)

def _fallback_detail_image(detail_url: str) -> str | None:
    """Va sur la page détail pour récupérer og:image (fallback propre)."""
    try:
        r = requests.get(detail_url, timeout=10)
        if not r.ok:
            return None
        s = BeautifulSoup(r.text, "html.parser")
        og = s.select_one('meta[property="og:image"]')
        if og and og.get("content"):
            return urljoin(BASE_URL, og["content"])
        # 2e fallback: première image de contenu
        img = s.select_one(".entry-content img, article img")
        if img and img.get("src"):
            return urljoin(BASE_URL, img["src"])
    except Exception:
        pass
    return None

def _is_placeholder(url: str | None) -> bool:
    if not url:
        return True
    return "themes/tap/images/template/default-image" in url

def scrape_spectacles():
    """Scrape la page des spectacles TAP avec extraction des images en CSS + fallback og:image + pagination."""
    spectacles = []
    next_url = f"{BASE_URL}/spectacle/"

    # On suit le bouton "Voir plus" (data-next) tant qu'il existe
    while next_url:
        r = requests.get(next_url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        for block in soup.select(".grid-list .col-item"):
            # Image principale dans .grid-block__picture[style]
            poster = None
            pic = block.select_one(".grid-block__picture")
            if pic and pic.get("style"):
                poster = _extract_bg_url(pic.get("style"))

            # Titre + lien source
            article = block.select_one("article")
            if not article:
                continue

            title_el = article.select_one(".grid-block__title a, h2 a, h3 a")
            title = title_el.get_text(strip=True) if title_el else "Sans titre"
            href = title_el.get("href") if title_el else None
            source = urljoin(BASE_URL, href) if href else None

            # Date
            date_el = article.select_one("time.grid-block__date, .grid-block__date, time")
            date_text = date_el.get_text(" ", strip=True) if date_el else "Date à venir"

            # Reservation
            reservation = None
            res_a = article.select_one("a[href*='billet'], a[href*='ticket'], a[href*='resa']")
            if res_a and res_a.get("href"):
                reservation = urljoin(BASE_URL, res_a["href"])

            # Fallback si placeholder ou pas d'image
            if _is_placeholder(poster) and source:
                poster = _fallback_detail_image(source)

            spectacles.append({
                "title": title,
                "date": date_text,
                "release": None,
                "poster": poster,
                "cinema": "TAP Poitiers",
                "source": source,
                "reservation": reservation,
                "scraped_at": datetime.utcnow().isoformat()
            })

        # Pagination: bouton "Voir plus" avec data-next
        more_btn = soup.select_one(".load-more .bt-more[data-next]")
        next_url = more_btn.get("data-next") if more_btn else None

    return spectacles
