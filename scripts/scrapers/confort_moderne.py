import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def scrape_confort_moderne():
    url = "https://www.confort-moderne.fr/fr/agenda/details"
    events = []

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("table tbody tr")
        current_month = None

        for row in rows:
            cols = row.find_all("td")
            if not cols:
                continue

            # Colonne Mois (souvent sur la gauche)
            if "NOVE" in cols[0].get_text(strip=True).upper() or len(cols) == 5:
                month_text = cols[0].get_text(strip=True)
                if month_text:
                    current_month = month_text
                    continue

            # Si l’élément a au moins 5 colonnes valides
            if len(cols) >= 5:
                date = cols[0].get_text(strip=True)
                img_tag = cols[1].find("img")
                poster = img_tag["src"] if img_tag and "src" in img_tag.attrs else None

                title_block = cols[2].get_text(" ", strip=True)
                title = title_block.split("\n")[0].strip()
                description = title_block.replace(title, "").strip()

                type_event = cols[3].get_text(strip=True)
                location = cols[4].get_text(strip=True)

                # Compose un champ date lisible
                if current_month:
                    full_date = f"{date} {current_month}".strip()
                else:
                    full_date = date.strip()

                events.append({
                    "title": title,
                    "date": full_date,
                    "poster": poster,
                    "description": description or None,
                    "cinema": "Confort Moderne",
                    "type": type_event,
                    "location": location,
                    "source": url,
                    "scraped_at": datetime.now().isoformat()
                })

        # Supprime doublons et nettoie
        seen = set()
        unique_events = []
        for ev in events:
            key = ev["title"] + ev.get("date", "")
            if key not in seen:
                seen.add(key)
                unique_events.append(ev)

        print(f"🎸 Confort Moderne : {len(unique_events)} événements collectés")
        return unique_events

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
