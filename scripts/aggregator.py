#!/usr/bin/env python3
# coding: utf-8

import json
from datetime import datetime, timezone

# --- Imports des scrapers ---
from scrapers import confort_moderne


def main():
    all_events = []

    # --- CONFORT MODERNE ---
    print("\n🎸 CONFORT MODERNE...")
    try:
        confort_events = confort_moderne.scrape_confort_moderne()
        print(f"✅ {len(confort_events)} événements récupérés depuis le Confort Moderne.")
        all_events += confort_events
    except Exception as e:
        print(f"❌ Erreur lors du scraping Confort Moderne : {e}")

    # --- Nettoyage des doublons ---
    seen = set()
    unique = []
    for ev in all_events:
        key = (
            ev.get("title", "").strip().lower(),
            ev.get("source", "").strip().lower(),
        )
        if key not in seen:
            seen.add(key)
            unique.append(ev)

    # --- Tri chronologique robuste ---
    def parse_date(value):
        if not value:
            return datetime.max
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except Exception:
            return datetime.max

    def sort_key(ev):
        return parse_date(ev.get("release")) or parse_date(ev.get("date"))

    unique.sort(key=sort_key)

    # --- Sauvegarde ---
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "events": unique,
    }

    with open("events.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(
        f"\n💾 {len(unique)} événements sauvegardés dans events.json "
        f"({len(all_events)} collectés avant dédoublonnage)"
    )

    # --- Résumé final ---
    print(f"   🎸 Confort Moderne : {len(locals().get('confort_events', []))}")


if __name__ == "__main__":
    main()
