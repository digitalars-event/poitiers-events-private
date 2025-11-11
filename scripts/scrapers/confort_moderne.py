import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

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

            # --- Mois (souvent 1ère colonne)
            month_td = cols[0]
            if month_td and month_td.get_text(strip=True):
                current_month = month_td.get_text(strip=True)

            # --- Date / période
            date_td = cols[1] if len(cols) > 1 else None
            date_text = date_td.get_text(" ", strip=True) if date_td else ""

            # --- Image (fond de div.img_filter)
            img_td = row.select_one("td.img-table .img_filter")
            poster = None
            if img_td and "background-image" in img_td.get("style", ""):
                match = re.search(r"url\(['\"]?(.*?)['\"]?\)", img_td["style"])
                if match:
                    poster = match.group(1)

            # --- Titre et description (artistes)
            title_td = row.select_one("td a.clic")
            title = title_td.get_text(strip=True) if title_td else "Sans titre"
            description_span = row.select_one("td span span")
            description = description_span.get_text(strip=True) if description_span else None

            # --- Type (Concert, Expo...)
            type_td = row.select_one("td.expo, td span")
            type_event = type_td.get_text(strip=True) if type_td else None

            # --- Lien source (onclick ou <a>)
            onclick = row.get("onclick")
            if onclick and "location.href=" in onclick:
                match = re.search(r"location\.href='(.*?)'", onclick)
                source = match.group(1) if match else url
            else:
                link_tag = row.select_one("a.clic")
                source = link_tag["href"] if link_tag and "href" in link_tag.attrs else url

            # --- Concatène mois + date si possible
            full_date = f"{current_month} {date_text}".strip()

            events.append({
                "title": title,
                "date": full_date,
                "poster": poster,
                "description": description,
                "cinema": "Confort Moderne",
                "type": type_event,
                "location": "Confort Moderne, Poitiers",
                "source": source,
                "scraped_at": datetime.now().isoformat()
            })

        # Nettoyage doublons
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
