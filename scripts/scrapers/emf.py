import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re


BASE_URL = "https://emf.fr/le-programme/#s=&date={}&tax="


def generate_dates(start="2025-11-16", end="2025-12-14"):
    start_date = datetime.strptime(start, "%Y-%m-%d")
    end_date = datetime.strptime(end, "%Y-%m-%d")
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime("%d-%m-%Y"))
        current += timedelta(days=1)
    return dates


def clean(text):
    if not text:
        return ""
    return " ".join(text.strip().split())


# ---------------------------------------------------------
# 🔥 Scrape le CSS inline et construit un dictionnaire :
#    { "91225": "https://....jpg" }
# ---------------------------------------------------------
def extract_images_from_inline_css(soup):
    image_map = {}

    styles = soup.find_all("style")

    pattern = r"\.e-loop-item-(\d+).*?background-image:\s*url\((.*?)\)"

    for style in styles:
        css = style.text
        matches = re.findall(pattern, css, re.DOTALL)
        for loop_id, img in matches:
            image_map[loop_id] = img.strip('"\' ')

    return image_map


# ---------------------------------------------------------
# Scraper la page interne
# ---------------------------------------------------------
def scrape_event_page(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
    except:
        return {"description": "", "reservation": None}

    desc_block = soup.select_one(".elementor-widget-theme-post-content")
    description = clean(desc_block.get_text(" ", strip=True)) if desc_block else ""

    reservation_btn = soup.find("a", string=lambda t: t and "réserv" in t.lower())
    reservation_link = reservation_btn["href"] if reservation_btn else None

    return {
        "description": description,
        "reservation": reservation_link
    }


# ---------------------------------------------------------
# Scrape une journée
# ---------------------------------------------------------
def scrape_day(date_str):
    url = BASE_URL.format(date_str)
    print(f"Scraping : {url}")

    try:
        r = requests.get(url, timeout=10)
    except:
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    # 🔥 Extraire les images à partir des styles inline
    image_map = extract_images_from_inline_css(soup)

    results = []

    for item in soup.select(".e-loop-item"):
        try:
            # Trouver l'ID e-loop-item-XXXXX
            loop_id = None
            for c in item.get("class", []):
                match = re.match(r"e-loop-item-(\d+)", c)
                if match:
                    loop_id = match.group(1)

            # URL
            link_tag = item.select_one("a[href*='/event/']")
            if not link_tag:
                continue
            event_url = link_tag["href"]

            # Catégorie
            category = clean(item.select_one("span").text if item.select_one("span") else "")

            # Titre
            title_tag = item.select_one("h3")
            title = clean(title_tag.text) if title_tag else ""

            # Extrait
            excerpt_tag = item.select_one(".elementor-widget-theme-post-excerpt p")
            excerpt = clean(excerpt_tag.text) if excerpt_tag else ""

            # 🔥 Image via CSS inline
            image = image_map.get(loop_id)

            # Contenu interne
            details = scrape_event_page(event_url)

            results.append({
                "url": event_url,
                "title": title,
                "category": category,
                "excerpt": excerpt,
                "description": details["description"],
                "img": image,
                "reservation": details["reservation"],
                "source": "espace mendes france",
                "occurrence": {"date": date_str}
            })

        except Exception as e:
            print("Erreur sur un item :", e)
            continue

    return results


# ---------------------------------------------------------
# Fusion
# ---------------------------------------------------------
def merge_events(events):
    merged = {}

    for ev in events:
        url = ev["url"]
        if url not in merged:
            merged[url] = {
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

        merged[url]["occurrences"].append(ev["occurrence"])

    return list(merged.values())


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
def scrape_emf():
    all_events = []

    for date in generate_dates("2025-11-16", "2025-12-14"):
        all_events.extend(scrape_day(date))

    cleaned = merge_events(all_events)

    with open("emf_events.json", "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    print(f"\n👍 {len(cleaned)} événements uniques sauvegardés dans emf_events.json")
    return cleaned


if __name__ == "__main__":
    scrape_emf()
