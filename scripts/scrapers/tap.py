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
    # Chaque film est généralement dans une div avec une classe liée aux actualités cinéma
    for film in soup.select("article.film, article.post, .list-item, .film-item"):
        title_el = film.select_one("h2, h3, .title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        # Lien vers la fiche détaillée
        a = film.select_one("a")
        source = a["href"] if a and a["href"].startswith("http") else BASE_URL + a["href"] if a else None

        # Affiche
        img = film.select_one("img")
        poster = img["src"] if img else None
        if poster and poster.startswith("/"):
            poster = BASE_URL + poster

        # Description
        desc = film.select_one("p, .description, .excerpt")
        description = desc.get_text(strip=True) if desc else None

        # Durée et genre (souvent dans un paragraphe ou une meta)
        meta = film.get_text(" ", strip=True)
        duration = None
        genres = None
        if "Durée" in meta:
            try:
                duration = meta.split("Durée")[-1].split("min")[0].strip() + " min"
            except:
                pass
        if "Genre" in meta or "Drame" in meta or "Comédie" in meta:
            genres = ", ".join([w for w in meta.split() if w.lower() in ["drame", "comédie", "action", "biopic", "aventure", "documentaire"]])

        films.append({
            "title": title,
            "duration": duration,
            "description": description,
            "poster": poster,
            "genres": genres,
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
    # Chaque spectacle est généralement dans un article.show ou une liste similaire
    for show in soup.select("article.show, article.post, .list-item, .show-item"):
        title_el = show.select_one("h2, h3, .title")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)

        # Lien source (fiche spectacle)
        a = show.select_one("a")
        source = a["href"] if a and a["href"].startswith("http") else BASE_URL + a["href"] if a else None

        # Affiche
        img = show.select_one("img")
        poster = img["src"] if img else None
        if poster and poster.startswith("/"):
            poster = BASE_URL + poster

        # Date
        date_el = show.select_one(".date, .event-date, time")
        date_text = date_el.get_text(" ", strip=True) if date_el else "Date à venir"

        # Tentative de conversion en ISO
        release = None
        try:
            release = datetime.strptime(date_text.split()[-1], "%d/%m/%Y").isoformat()
        except:
            release = None

        # Lien réservation s’il y a un bouton
        reservation = None
        res_a = show.select_one("a[href*='billet'], a[href*='reservation'], a[href*='ticket']")
        if res_a:
            reservation = res_a["href"]

        spectacles.append({
            "title": title,
            "date": date_text,
            "release": release,
            "poster": poster,
            "cinema": "TAP Poitiers",
            "source": source,
            "reservation": reservation,
            "scraped_at": datetime.utcnow().isoformat()
        })
    return spectacles


if __name__ == "__main__":
    data = {
        "cinema": scrape_cinema(),
        "spectacle": scrape_spectacles()
    }

    with open("tap.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ TAP data scraped and saved to tap.json ({len(data['cinema'])} films, {len(data['spectacle'])} spectacles)")
