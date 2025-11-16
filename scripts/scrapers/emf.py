
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time

BASE_URL = "https://emf.fr/le-programme/#s=&date={}&tax="

# ---------------------------------------------------------
# Génération des dates
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
# Cleaner
# ---------------------------------------------------------
def clean(text):
    if not text:
        return ""
    return " ".join(text.strip().split())

# ---------------------------------------------------------
# Scraper la page interne de l’événement
# ---------------------------------------------------------
def scrape_event_page(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
    except:
        return {"description": "", "image": None, "reservation": None}

    # Description : zone Elementor principale
    desc_block = soup.select_one(".elementor-widget-theme-post-content")
    description = clean(desc_block.get_text(" ", strip=True)) if desc_block else ""

    # ----- IMAGE -----
    image = None

    # 1) Cherche une image dans un background-image inline
    bg_div = soup.find(style=lambda v: v and "background-image" in v)
    if bg_div:
        import re
        match = re.search(r'url\((.*?)\)', bg_div["style"])
        if match:
            image = match.group(1).strip('\'"')

    # 2) Sinon fallback sur img classique
    if not image:
        img_tag = soup.find("img")
        if img_tag:
            image = img_tag.get("src")

    # ----- RÉSERVATION -----
    reservation_btn = soup.find("a", string=lambda t: t and "réserv" in t.lower())
    reservation_link = reservation_btn["href"] if reservation_btn else None

    return {
        "description": description,
        "image": image,
        "reservation": reservation_link
    }

# ---------------------------------------------------------
# Scraper la liste (boucle Elementor)
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
    events_html = soup.select(".e-loop-item")
    results = []

    for item in events_html:
        try:
            link_tag = item.select_one("a[href*='/event/']")
            if not link_tag:
                continue

            url = link_tag["href"]

            category = clean(item.select_one("span") and item.select_one("span").text)
            title_tag = item.select_one("h3")
            title = clean(title_tag.text) if title_tag else "Sans titre"

            excerpt_tag = item.select_one(".elementor-widget-theme-post-excerpt p")
            excerpt = clean(excerpt_tag.text) if excerpt_tag else ""

            # --------------------------
            # 🔥 EXTRACTION IMAGE LISTING
            # --------------------------
            image = None

            bg_div = item.find(style=lambda v: v and "background-image" in v)
            if bg_div:
                import re
                match = re.search(r'url\((.*?)\)', bg_div["style"])
                if match:
                    image = match.group(1).strip("'\"")

            if not image:
                img_tag = item.find("img")
                if img_tag:
                    image = img_tag.get("src")

            # Infos page interne
            details = scrape_event_page(url)

            results.append({
                "url": url,
                "title": title,
                "category": category,
                "excerpt": excerpt,
                "description": details["description"],
                "img": image,  # <<< 🔥 ICI !!!
                "reservation": details["reservation"],
                "source": "espace mendes france",
                "occurrence": {
                    "date": date_str
                }
            })

        except Exception as e:
            print("Erreur sur un item :", e)
            continue

    return results


# ---------------------------------------------------------
# Fusion des événements identiques
# ---------------------------------------------------------
def merge_events(events):
    merged = {}

    for ev in events:
        key = ev["url"]

        if key not in merged:
            merged[key] = {
                "url": ev["url"],
                "title": ev["title"],
                "category": ev["category"],
                "excerpt": ev["excerpt"],
                "description": ev["description"],
                "img": ev["img"],
                "reservation": ev["reservation"],
                "source": ev["source"],
                "occurrences": []
            }

        merged[key]["occurrences"].append(ev["occurrence"])

    return list(merged.values())

# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def scrape_emf():
    all_events = []

    for date in generate_dates("2025-11-16", "2025-12-14"):
        all_events.extend(scrape_day(date))
        time.sleep(0.7)

    cleaned = merge_events(all_events)

    with open("emf_events.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"\n👍 {len(cleaned)} événements uniques sauvegardés dans emf_events.json")
    return cleaned

if __name__ == "__main__":
    scrape_emf()

