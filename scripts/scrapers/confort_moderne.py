import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import locale

# --- Locale française pour les noms de mois
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except:
    pass


def clean_text(text):
    """Nettoie les espaces et caractères parasites."""
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_date(day_text: str, month_text: str):
    """Convertit une combinaison jour/mois français en ISO 8601."""
    if not day_text or not month_text:
        return None

    months = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }

    # Cas spéciaux
    if "jusqu" in day_text.lower() or "partir" in day_text.lower():
        return None

    # Trouver un chiffre dans le texte
    m = re.search(r"(\d{1,2})", day_text)
    if not m:
        return None

    day = int(m.group(1))
    month = months.get(month_text.strip().lower())
    if not month:
        return None

    now = datetime.now()
    year = now.year
    if month < now.month - 3:  # janvier après novembre → année suivante
        year += 1

    try:
        dt = datetime(year, month, day, 20, 0, 0)
        return dt.isoformat()
    except Exception:
        return None


def scrape_confort_moderne():
    url = "https://www.confort-moderne.fr/fr/agenda/details"
    events = []

    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        current_month = None
        rows = soup.select("tr.tr-table")

        for row in rows:
            cols = row.find_all("td")
            if not cols:
                continue

            # Détection du mois
            month_text = clean_text(cols[0].get_text()) if cols else ""
            if re.search(r"(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)", month_text.lower()):
                current_month = month_text
                offset = 1
            else:
                offset = 0

            # --- Date (jour)
            try:
                date_text = clean_text(cols[offset].get_text())
            except IndexError:
                date_text = ""

            # --- Image
            img_tag = row.select_one(".img_filter")
            poster = None
            if img_tag and "background-image" in img_tag.get("style", ""):
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", img_tag["style"])
                if match:
                    poster = match.group(1)

            # --- Titre et artistes
            title_tag = row.select_one("a.clic")
            title = clean_text(title_tag.get_text()) if title_tag else "Sans titre"

            artist_tag = row.select_one("td span span")
            description = clean_text(artist_tag.get_text()) if artist_tag else None

            # --- Type (Concert, Expo, etc.)
            type_td = cols[-2] if len(cols) >= 5 else None
            type_event = clean_text(type_td.get_text()) if type_td else None

            # --- Lieu
            location_td = cols[-1] if len(cols) >= 6 else None
            location = clean_text(location_td.get_text()) or "Confort Moderne, Poitiers"

            # --- Lien
            onclick = row.get("onclick", "")
            match = re.search(r"location.href='(.*?)'", onclick)
            source = match.group(1) if match else url

            # --- Fusion des dates
            full_date = f"{current_month or ''} {date_text}".strip()
            iso_date = normalize_date(date_text, current_month or "")

            events.append({
                "title": title,
                "date": full_date,
                "release": iso_date,
                "poster": poster,
                "description": description,
                "cinema": "Confort Moderne",
                "type": type_event,
                "location": location,
                "source": source,
                "scraped_at": datetime.now().isoformat()
            })

        # Nettoyage doublons
        seen = set()
        unique = []
        for ev in events:
            key = (ev["title"].lower(), ev["date"].lower())
            if key not in seen:
                seen.add(key)
                unique.append(ev)

        print(f"🎸 Confort Moderne : {len(unique)} événements collectés")
        return unique

    except Exception as e:
        print(f"❌ Erreur lors du scraping Confort Moderne : {e}")
        return []


if __name__ == "__main__":
    data = scrape_confort_moderne()
    output = {
        "generated_at": datetime.now().isoformat(),
        "events": data
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("💾 Données sauvegardées dans events.json")
