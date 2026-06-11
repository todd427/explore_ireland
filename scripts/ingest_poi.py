"""
Build tourism POI data per county from OpenStreetMap (Overpass API).

For each Republic-of-Ireland county we take its bounding box from the served
geometry, query Overpass for tourism-relevant features, clip them to the
county polygon (so border features from neighbours don't leak in), bucket
them into Eat & Drink / Stay / See & Do, rank by "notability" (OSM has no
ratings, so we proxy with wikidata/website/stars/wikipedia tags), and write
the top results to static/data/poi/<slug>.json.

Data © OpenStreetMap contributors, licensed under the ODbL.

Usage:
    python3 scripts/ingest_poi.py            # all Irish counties
    python3 scripts/ingest_poi.py cork kerry # only these slugs

Polite to Overpass: sequential, with a pause between counties. Re-run to refresh.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEOJSON = ROOT / "static" / "data" / "all_regions.geojson"
COUNTIES = ROOT / "data" / "counties.json"
OUT_DIR = ROOT / "static" / "data" / "poi"
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
PER_CATEGORY = 20          # cap stored per bucket
PAUSE_SECONDS = 3          # between counties
MAX_RETRIES = 4            # per county, cycling endpoints with backoff

# OSM tag -> (bucket, friendly label)
EAT_DRINK = {"restaurant": "Restaurant", "cafe": "Café", "pub": "Pub",
             "bar": "Bar", "fast_food": "Fast food", "biergarten": "Beer garden"}
STAY = {"hotel": "Hotel", "guest_house": "Guesthouse", "hostel": "Hostel",
        "motel": "Motel", "chalet": "Chalet"}
SEE_DO_TOURISM = {"attraction": "Attraction", "museum": "Museum",
                  "gallery": "Gallery", "viewpoint": "Viewpoint",
                  "artwork": "Artwork", "theme_park": "Theme park",
                  "zoo": "Zoo", "aquarium": "Aquarium"}
SEE_DO_HISTORIC = {"castle": "Castle", "monument": "Monument", "ruins": "Ruins",
                   "archaeological_site": "Archaeological site",
                   "memorial": "Memorial", "fort": "Fort", "manor": "Manor"}


def overpass_query(s, w, n, e):
    bbox = f"{s},{w},{n},{e}"
    return f"""[out:json][timeout:90];
(
  node["amenity"~"^(restaurant|cafe|pub|bar|fast_food|biergarten)$"]({bbox});
  node["tourism"~"^(hotel|guest_house|hostel|motel|chalet|attraction|museum|gallery|viewpoint|artwork|theme_park|zoo|aquarium)$"]({bbox});
  node["historic"~"^(castle|monument|ruins|archaeological_site|memorial|fort|manor)$"]({bbox});
  way["tourism"~"^(hotel|guest_house|hostel|attraction|museum|gallery|theme_park|zoo|aquarium)$"]({bbox});
  way["historic"~"^(castle|ruins|archaeological_site|fort|manor)$"]({bbox});
);
out center 1200 tags;"""


def fetch(query):
    """Try each Overpass mirror with backoff; tolerate 504/429 from busy servers."""
    data = urllib.parse.urlencode({"data": query}).encode()
    last = None
    for attempt in range(MAX_RETRIES):
        url = OVERPASS_ENDPOINTS[attempt % len(OVERPASS_ENDPOINTS)]
        req = urllib.request.Request(
            url, data=data, headers={"User-Agent": "explore-islands-ingest/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read().decode())
        except Exception as ex:  # 504/429/timeout — back off and try next mirror
            last = ex
            time.sleep(5 * (attempt + 1))
    raise last


# --- geometry helpers ---------------------------------------------------------
def rings_of(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [poly[0] for poly in polys]  # exterior rings only


def bbox_of(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return min(ys), min(xs), max(ys), max(xs)  # s, w, n, e


def point_in_rings(lon, lat, rings):
    inside = False
    for ring in rings:
        n = len(ring)
        j = n - 1
        for i in range(n):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            if ((yi > lat) != (yj > lat)) and \
               (lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi):
                inside = not inside
            j = i
    return inside


# --- categorisation -----------------------------------------------------------
def classify(tags):
    a = tags.get("amenity")
    t = tags.get("tourism")
    h = tags.get("historic")
    if a in EAT_DRINK:
        return "eat_drink", EAT_DRINK[a]
    if t in STAY:
        return "stay", STAY[t]
    if t in SEE_DO_TOURISM:
        return "see_do", SEE_DO_TOURISM[t]
    if h in SEE_DO_HISTORIC:
        return "see_do", SEE_DO_HISTORIC[h]
    return None, None


def notability(tags):
    score = 0
    if tags.get("wikidata"):
        score += 3
    if tags.get("wikipedia"):
        score += 2
    if tags.get("website") or tags.get("contact:website"):
        score += 1
    if tags.get("stars"):
        score += 1
    if tags.get("name"):
        score += 1
    return score


def build_county(slug, name, feature):
    rings = rings_of(feature["geometry"])
    s, w, n, e = bbox_of(rings)
    raw = fetch(overpass_query(s, w, n, e))
    buckets = {"eat_drink": [], "stay": [], "see_do": []}
    seen = set()
    for el in raw.get("elements", []):
        tags = el.get("tags", {})
        nm = tags.get("name")
        if not nm:
            continue
        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            c = el.get("center") or {}
            lat, lon = c.get("lat"), c.get("lon")
        if lat is None or lon is None:
            continue
        if not point_in_rings(lon, lat, rings):
            continue
        bucket, label = classify(tags)
        if not bucket:
            continue
        key = (nm.lower(), round(lat, 4), round(lon, 4))
        if key in seen:
            continue
        seen.add(key)
        buckets[bucket].append({
            "name": nm,
            "kind": label,
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "cuisine": tags.get("cuisine", "").replace("_", " ").replace(";", ", ") or None,
            "website": tags.get("website") or tags.get("contact:website") or None,
            "_score": notability(tags),
        })
    for b in buckets:
        buckets[b].sort(key=lambda x: (-x["_score"], x["name"]))
        buckets[b] = buckets[b][:PER_CATEGORY]
        for item in buckets[b]:
            del item["_score"]
    return {
        "slug": slug,
        "name": name,
        "source": "OpenStreetMap contributors (ODbL)",
        "categories": buckets,
        "counts": {b: len(v) for b, v in buckets.items()},
    }


def main():
    gj = json.loads(GEOJSON.read_text(encoding="utf-8"))
    feats = {f["properties"]["slug"]: f for f in gj["features"]}
    counties = json.loads(COUNTIES.read_text(encoding="utf-8"))
    want = set(a.lower() for a in sys.argv[1:])
    targets = [c for c in counties
               if c["country_group"] == "Ireland" and (not want or c["slug"] in want)]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ingesting {len(targets)} counties from Overpass...")
    for i, c in enumerate(targets):
        slug = c["slug"]
        if slug not in feats:
            print(f"  ! {slug}: no geometry, skipping")
            continue
        try:
            doc = build_county(slug, c["name"], feats[slug])
        except Exception as ex:  # network / Overpass hiccup — keep going
            print(f"  ! {slug}: {ex}")
            continue
        (OUT_DIR / f"{slug}.json").write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  + {slug}: eat_drink={doc['counts']['eat_drink']} "
              f"stay={doc['counts']['stay']} see_do={doc['counts']['see_do']}")
        if i < len(targets) - 1:
            time.sleep(PAUSE_SECONDS)
    print("Done.")


if __name__ == "__main__":
    main()
