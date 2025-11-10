# scrapers/tap.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

BASE_URL = "https://www.tap-poitiers.com"


def scrape_cinema():
    """Scrape la liste des films TAP Cinéma + détail pour durée et description"""
    url = f"{BASE_URL}/cinema/"
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    films = []

    for film in soup.select("article"):
        title_el = film.select_one("h2, h3, .title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        # Source (fiche du film)
        a = film.select_one("a")
        source = None
        if a and a.get("href"):
            href = a["href"]
            source = href if href.startswith("http") else BASE_URL + href

        # Poster
        poster = None
        img = film.select_one("img")
        if img and img.get("src"):
            src = img["src"]
            poster = src if src.startswith("http") else BASE_URL + src

        # --- Aller dans la fiche du film pour extraire durée et description ---
        duration = None
        description = None
        if source:
            try:
                detail_res = requests.get(source, timeout=10)
                if detail_res.ok:
                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")

                    # Durée (ex : "Durée : 1h47")
                    dur_el = detail_soup.find(text=re.compile(r"Durée\s*:?"))
                    if dur_el:
                        match = re.search(r"(\d+h\d+|\d+h|\d+\s?min)", dur_el)
                        if match:
                            duration = match.group(1).replace(" ", "") + " min" if "min" not in match.group(1) else match.group(1)

                    # Description / synopsis
                    # souvent dans .entry-content p ou .article-content p
                    desc_el = detail_soup.select_one(".entry-content p, .article-content p")
                    if desc_el:
                        description = desc_el.get_text(strip=True)
            except Exception:
                pass

        films.append({
            "title": title,
            "duration": duration,
            "description": description,
            "poster": poster,
            "genres": None,
            "certificate": None,
            "release": None,
            "cinema": "TAP Cinéma Poitiers",
            "source": source,
            "scraped_at": datetime.utcnow().isoformat()
        })

    return films


def scrape_spectacles():
    """Scrape la page des spectacles TAP"""
    url = f"{BASE_URL}/spectacle/"
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    spectacles = []

    # Chaque spectacle est dans un conteneur .col-item
    for block in soup.select(".col-item"):
        # 🎭 Image (dans div.grid-block__picture)
        poster = None
        bg_div = block.select_one(".grid-block__picture[style*='background-image']")
        if bg_div:
            style = bg_div.get("style", "")
            match = re.search(r'url\((?:&quot;|["\']?)(.*?)(?:&quot;|["\']?)\)', style)
            if match:
                src = match.group(1)
                poster = src if src.startswith("http") else BASE_URL + src

        # 🎟️ Article lié
        article = block.select_one("article")
        if not article:
            continue

        # Titre + lien source
        title_el = article.select_one("h2 a, h3 a, .grid-block__title a")
        title = title_el.get_text(strip=True) if title_el else "Sans titre"
        href = title_el["href"] if title_el and title_el.get("href") else None
        source = href if href and href.startswith("http") else BASE_URL + href if href else None

        # 🗓️ Date
        date_el = article.select_one("time, .grid-block__date")
        date_text = date_el.get_text(" ", strip=True) if date_el else "Date à venir"

        # 🔗 Réservation
        reservation = None
        res_a = article.select_one("a[href*='billet'], a[href*='ticket'], a[href*='resa']")
        if res_a and res_a.get("href"):
            reservation = res_a["href"]

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

    return spectacles

def scrape_tap():
    """Combine cinéma + spectacle dans une seule structure"""
    try:
        cinema = scrape_cinema()
    except Exception as e:
        print(f"⚠️  Erreur cinéma TAP : {e}")
        cinema = []

    try:
        spectacle = scrape_spectacles()
    except Exception as e:
        print(f"⚠️  Erreur spectacle TAP : {e}")
        spectacle = []

    return {"cinema": cinema, "spectacle": spectacle}
