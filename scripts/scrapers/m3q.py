import requests
from bs4 import BeautifulSoup

URL = "https://m3q.centres-sociaux.fr/saison-culturelle-2025-26/"

def scrape_m3q():
    response = requests.get(URL, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    events = []

    # Toutes les sections Elementor
    sections = soup.find_all("section", class_="elementor-section")

    current_date = None

    for i, section in enumerate(sections):
        # 1) DÉTECTION DES TITRES DE DATE
        date_block = section.find("p")
        if date_block and date_block.get_text(strip=True).upper().startswith(
                ("LUNDI", "MARDI", "MERCREDI", "JEUDI", "VENDREDI", "SAMEDI", "DIMANCHE")
        ):
            current_date = date_block.get_text(strip=True)
            continue

        # 2) DÉTECTION DES BLOCS ÉVÉNEMENTS (image + infos)
        image = section.find("img")
        title = section.find("h4")
        texts = section.find_all("div", class_="elementor-widget-container")

        if image and title and current_date:
            # IMAGE
            image_url = image["src"]

            # TITRE
            event_title = title.get_text(strip=True)

            # Sous-titre + description + heure
            subtitle = None
            description = ""
            time_info = None

            for t in texts:
                content = t.get_text("\n", strip=True)

                # Sous-titre "· xxx"
                if content.startswith("·"):
                    subtitle = content

                # Heure formatée : "→ Vendredi 10 octobre / 20h30"
                if "→" in content:
                    time_info = content.replace("→", "").strip()

                # Description multi-lignes
                if not content.startswith("·") and "→" not in content and len(content) > 10:
                    if not content.upper().startswith(("AGENDA", "TÉLÉCHARGEZ", "SAMEDI", "DIMANCHE")):
                        description += content + "\n"

            description = description.strip() if description else None

            # Billetterie
            button = section.find("a", class_="elementor-button")
            booking_url = button["href"] if button else None

            events.append({
                "etablissement": "Maison des 3 quartiers",
                "date": current_date,
                "title": event_title,
                "subtitle": subtitle,
                "description": description,
                "time": time_info,
                "image": image_url,
                "ticket": booking_url
            })

    return events


if __name__ == "__main__":
    data = scrape_m3q()
    import json
    print(json.dumps(data, indent=4, ensure_ascii=False))
