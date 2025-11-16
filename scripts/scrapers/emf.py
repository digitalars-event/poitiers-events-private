import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time

BASE_URL = "https://emf.fr/le-programme/#s=&date={}&tax="

# ---------------------------------------------------------
# 🔧 Génération de la liste des dates à scraper
# ---------------------------------------------------------
def generate_dates(start="2025-11-16", end="2025-12-14"):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")

    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime("%d-%m-%Y"))
        current += timedelta(days=1)
    return dates

# ---------------------------------------------------------
# 🔍 Extraction propre du texte
# ---------------------------------------------------------
def clean(text):
    if not text:
        return ""
    return " ".join(text.strip().split())

# ---------------------------------------------------------
# 🔥 Scraper un jour
# ---------------------------------------------------------
def scrape_day(date_str):
    url = BASE_URL.format(date_str)
    print(f"Scraping : {url}")

    try:
        r = requests.get(url, timeout=10)
    except Exception as e:
        print("Erreur request :", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    # Chaque événement est un "e-loop-item"
    events_html = soup.select(".e-loop-item")
    results = []

    for item in events_html:
        try:
            # Lien principal → identifiant unique de l’événement
            link_tag = item.select_one("a[href*='/event/']")
            if not link_tag:
                continue

            url = link_tag["href"]

            # Catégorie (ex: Expositions)
            category = clean(item.select_one("span") and item.select_one("span").text)

            # Titre
            title_tag = item.select_one("h3")
            title = clean(title_tag.text) if title_tag else "Sans titre"

            # Résumé court
            excerpt_tag = item.select_one(".elementor-widget-theme-post-excerpt p")
            excerpt = clean(excerpt_tag.text) if excerpt_tag else ""

            # Date + heure du jour
            date_time_tag = item.select_one(".elementor-widget-text-editor")
            date_time = clean(date_time_tag.text) if date_time_tag else ""

            # Image
            img_tag = item.find("img")
            img = img_tag["src"] if img_tag else None

            results.append({
                "url": url,
                "title": title,
                "category": category,
                "excerpt": excerpt,
                "img": img,
                "occurrence": {
                    "date": date_str,
                    "datetime_raw": date_time
                }
            })

        except Exception as e:
            print("Erreur sur un item :", e)
            continue

    return results

# ---------------------------------------------------------
# 🧠 Fusionner les événements identiques
# ---------------------------------------------------------
def merge_events(events):
    merged = {}

    for ev in events:
        key = ev["url"]  # identifiant unique = l'URL

        if key not in merged:
            merged[key] = {
                "url": ev["url"],
                "title": ev["title"],
                "category": ev["category"],
                "excerpt": ev["excerpt"],
                "img": ev["img"],
                "occurrences": []
            }

        merged[key]["occurrences"].append(ev["occurrence"])

    return list(merged.values())

# ---------------------------------------------------------
# 🚀 Script principal
# ---------------------------------------------------------
def scrape_emf():
    all_events = []

    dates = generate_dates("2025-11-16", "2025-12-14")

    for date in dates:
        events_day = scrape_day(date)
        all_events.extend(events_day)
        time.sleep(1)  # éviter de spammer le site

    cleaned = merge_events(all_events)

    with open("emf_events.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"\n👍 Scraping terminé, {len(cleaned)} événements uniques sauvegardés dans emf_events.json")

if __name__ == "__main__":
    scrape_emf()
