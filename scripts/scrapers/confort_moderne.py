import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import locale

# --- Forcer la locale française (utile pour noms de mois)
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except:
    pass


def normalize_date(day_text: str, month_text: str):
    """
    Convertit un jour et un mois français en date ISO (YYYY-MM-DDT20:00:00)
    si possible. Ignore les expressions comme 'jusqu'au' ou 'à partir du'.
    """
    if not day_text or not month_text:
        return None

    months = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }

    # Cas non normalisables
    if "jusqu" in day_text.lower() or "partir" in day_text.lower():
        return None

    # Extraire le numéro du jour
    m = re.search(r"(\d{1,2})", day_text)
    if not m:
        return None

    day = int(m.group(1))
    month = months.get(month_text.lower())
    if not month:
        return None

    # Déterminer l’année (ex: janvier -> année suivante quand on est en novembre)
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
    """Nettoie les espaces et retours de ligne superflus."""
    return re.sub(r"\s+", " ", text or "").strip()


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
            cols = row.find_all("td")
            if not cols:
                continue

            # --- Mois (1ère colonne, ex: NOVEMBRE, DÉCEMBRE)
            month_td = cols[0]
            month_text = month_td.get_text(strip=True)
            if month_text:
                current_month = month_text  # mémoriser le mois courant

            # --- Date ou période
            date_td = cols[1] if len(cols) > 1 else None
            date_text = clean_text(date_td.get_text(" ", strip=True)) if date_td else ""

            # --- Image (background-image)
            img_td = row.select_one("td.img-table .img_filter")
            poster = None
            if img_td and "background-image" in img_td.get("style", ""):
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", img_td["style"])
                if match:
                    poster = match.group(1)

            # --- Titre et description (artistes)
            title_tag = row.select_one("td a.clic")
            title = clean_text(title_tag.get_text()) if title_tag else "Sans titre"
            description_span = row.select_one("td span span")
            description = clean_text(description_span.get_text()) if description_span else None

            # --- Type (Concert, Expo...)
            type_td = cols[-2] if len(cols) >= 5 else None
            type_event = clean_text(type_td.get_text()) if type_td else None

            # --- Lieu (dernière colonne)
            location_td = cols[-1] if len(cols) >= 6 else None
            location = clean_text(location_td.get_text()) or "Confort Moderne, Poitiers"

            # --- Lien source
            onclick = row.get("onclick")
            if onclick and "location.href=" in onclick:
                match = re.search(r"location\\.href='(.*?)'", onclick)
                source = match.group(1) if match else url
            else:
                link_tag = row.select_one("a.clic")
                source = link_tag["href"] if link_tag and "href" in link_tag.attrs else url

            # --- Date complète (texte et ISO)
            month_lower = (current_month or "").strip().lower()
            full_date = f"{month_lower} {date_text}".strip()
            iso_date = normalize_date(date_text, month_lower)

            # --- Formater la date lisible proprement
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

        # --- Supprimer les doublons
        unique = []
        seen = set()
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
