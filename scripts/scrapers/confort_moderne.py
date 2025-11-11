import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import locale

# --- Locale française
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except:
    pass


def normalize_date(day_text: str, month_text: str):
    """Convertit un jour et un mois français en ISO si possible."""
    if not day_text or not month_text:
        return None

    months = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }

    # Ignore les cas particuliers
    if "jusqu" in day_text.lower() or "partir" in day_text.lower():
        return None

    # Extraire le jour
    m = re.search(r"(\d{1,2})", day_text)
    if not m:
        return None

    day = int(m.group(1))
    month = months.get(month_text.lower())
    if not month:
        return None

    now = datetime.now()
    year = now.year
    if month < now.month - 3:
        year += 1

    try:
        dt = datetime(year, month, day, 20, 0, 0)
        return dt.isoformat()
    except Exception:
        return None


def clean_text(text):
    """Nettoie les espaces et caractères parasites."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def scrape_confort_moderne():
    url = "https://www.confort-moderne.fr/fr/agenda/details"
    events = []

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("tr.tr-table")
        current_month = None

        for row in rows:
            tds = row.find_all("td")
            if not tds:
                continue

            # --- Si le premier td contient un nom de mois (ex: NOVEMBRE)
            possible_month = clean_text(tds[0].get_text())
            if re.match(r"^(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)$", possible_month.lower()):
                current_month = possible_month
                # ensuite, les colonnes sont décalées : date en 2e, image en 3e, etc.
                td_offset = 1
            else:
                # pas de mois sur cette ligne (héritage du précédent)
                td_offset = 0

            # --- Vérifie qu’on a au moins la colonne "date"
            if len(tds) <= td_offset:
                continue

            # --- Jour
            date_text = clean_text(tds[td_offset].get_text())

            # --- Image
            img_td = row.select_one("td.img-table .img_filter")
            poster = None
            if img_td and "background-image" in img_td.get("style", ""):
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", img_td["style"])
                if match:
                    poster = match.group(1)

            # --- Titre principal
            title_tag = row.select_one("td a.clic")
            title = clean_text(title_tag.get_text()) if title_tag else "Sans titre"

            # --- Description (artistes)
            description_span = row.select_one("td span span")
            description = clean_text(description_span.get_text()) if description_span else None

            # --- Type (Concert, Expo, etc.)
            type_td = tds[-2] if len(tds) >= 5 else None
            type_event = clean_text(type_td.get_text()) if type_td else None

            # --- Lieu
            location_td = tds[-1] if len(tds) >= 6 else None
            location = clean_text(location_td.get_text()) or "Confort Moderne, Poitiers"

            # --- Lien source
            source = url
            onclick = row.get("onclick")
            if onclick and "location.href" in onclick:
                match = re.search(r"location\.href='(.*?)'", onclick)
                if match:
                    source = match.group(1)
            elif title_tag and title_tag.get("href"):
                source = title_tag["href"]

            # --- Fusion mois + jour
            full_date = f"{current_month or ''} {date_text}".strip()
            iso_date = normalize_date(date_text, current_month or "")

            # --- Format lisible
            pretty_date = f"{date_text.capitalize()} {current_month.capitalize()}" if current_month else date_text

            events.append({
                "title": title,
                "date": pretty_date,
                "release": iso_date,
                "poster": poster,
                "description": description,
                "cinema": "Confort Moderne",
                "type": type_event,
                "location": location,
                "source": source,
                "scraped_at": datetime.now().isoformat()
            })

        # --- Suppression doublons
        unique, seen = [], set()
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
