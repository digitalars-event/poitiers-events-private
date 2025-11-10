# scrapers/tap.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://www.tap-poitiers.com"


def scrape_cinema():
    url = f"{BASE_URL}/cinema/"
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    films = []

    for film in soup.select("article, .film-item, .list-item"):
        title_el = film.select_one("h2, h3, .title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        # Source
        a = film.select_one("a")
        source = None
        if a and a.get("href"):
            href = a["href"]
            source = href if href.startswith("http") else BASE_URL + href

        # Poster (sécurisé)
        poster = None
        img = film.select_one("img")
        if img and img.get("src"):
            src = img["src"]
            poster = src if src.startswith("http") else BASE_URL + src

        # Description
        desc = film.select_one("p, .description, .excerpt")
        description = desc.get_text(strip=True) if desc else None

        # Durée
        duration = None
        text = film.get_text(" ", strip=True)
        if "Durée" in text:
            try:
                duration = text.split("Durée")[-1].split("min")[0].strip() + " min"
            except Exception:
                duration = None

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
    url = f"{BASE_URL}/spectacle/"
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    spectacles = []

    for show in soup.select("article, .show-item, .list-item"):
        title_el = show.select_one("h2, h3, .title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        # Source
        a = show.select_one("a")
        source = None
        if a and a.get("href"):
            href = a["href"]
            source = href if href.startswith("http") else BASE_URL + href

        # Poster (sécurisé)
        poster = None
        img = show.select_one("img")
        if img and img.get("src"):
            src = img["src"]
            poster = src if src.startswith("http") else BASE_URL + src

        # Date
        date_el = show.select_one(".date, time")
        date_text = date_el.get_text(" ", strip=True) if date_el else "Date à venir"

        # Reservation
        reservation = None
        res_a = show.select_one("a[href*='billet'], a[href*='ticket'], a[href*='resa']")
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

    return {
        "cinema": cinema,
        "spectacle": spectacle
    }
