# scrapers/tap.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

BASE_URL = "https://www.tap-poitiers.com"

def scrape_cinema():
    url = f"{BASE_URL}/cinema/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    films = []

    for film in soup.select("article, .film-item, .list-item"):
        title_el = film.select_one("h2, h3, .title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        a = film.select_one("a")
        source = a["href"] if a and a["href"].startswith("http") else BASE_URL + a["href"] if a else None
        img = film.select_one("img")
        poster = BASE_URL + img["src"] if img and img["src"].startswith("/") else img["src"] if img else None
        desc = film.select_one("p, .description, .excerpt")
        description = desc.get_text(strip=True) if desc else None

        meta = film.get_text(" ", strip=True)
        duration = None
        if "Durée" in meta:
            try:
                duration = meta.split("Durée")[-1].split("min")[0].strip() + " min"
            except:
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
    url = f"{BASE_URL}/spectacle/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    spectacles = []

    for show in soup.select("article, .show-item, .list-item"):
        title_el = show.select_one("h2, h3, .title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        a = show.select_one("a")
        source = a["href"] if a and a["href"].startswith("http") else BASE_URL + a["href"] if a else None
        img = show.select_one("img")
        poster = BASE_URL + img["src"] if img and img["src"].startswith("/") else img["src"] if img else None
        date_el = show.select_one(".date, time")
        date_text = date_el.get_text(" ", strip=True) if date_el else "Date à venir"

        reservation = None
        res_a = show.select_one("a[href*='billet'], a[href*='ticket'], a[href*='resa']")
        if res_a:
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
    """Combine cinéma + spectacle"""
    return {
        "cinema": scrape_cinema(),
        "spectacle": scrape_spectacles()
    }
