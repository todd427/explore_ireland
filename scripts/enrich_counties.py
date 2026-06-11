"""
One-off data builder for data/counties.json.

1. Computes a real area-weighted centroid for every region from the served
   geometry (static/data/all_regions.geojson), fixing the {0,0} placeholders.
2. Merges hand-written content (motto/nickname, key places, industries,
   history) for the Republic of Ireland counties.

Re-run after editing IRISH_CONTENT or the geojson:
    python3 scripts/enrich_counties.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COUNTIES = ROOT / "data" / "counties.json"
GEOJSON = ROOT / "static" / "data" / "all_regions.geojson"


def ring_centroid(ring):
    """Area-weighted centroid + signed area of a single linear ring."""
    a = cx = cy = 0.0
    n = len(ring)
    for i in range(n - 1):
        x0, y0 = ring[i][0], ring[i][1]
        x1, y1 = ring[i + 1][0], ring[i + 1][1]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if a == 0:
        # Degenerate ring: fall back to vertex average.
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        return (sum(xs) / len(xs), sum(ys) / len(ys), 0.0)
    a *= 0.5
    return (cx / (6 * a), cy / (6 * a), a)


def feature_centroid(geom):
    """Centroid of a (Multi)Polygon, weighted by polygon exterior-ring area."""
    t = geom["type"]
    if t == "Polygon":
        polys = [geom["coordinates"]]
    elif t == "MultiPolygon":
        polys = geom["coordinates"]
    else:
        return None
    tot_a = tx = ty = 0.0
    for poly in polys:
        x, y, a = ring_centroid(poly[0])  # exterior ring
        w = abs(a) or 1e-12
        tx += x * w
        ty += y * w
        tot_a += w
    if tot_a == 0:
        return None
    return {"lat": round(ty / tot_a, 5), "lng": round(tx / tot_a, 5)}


# --- Hand-written content for the 26 counties + Cork City ---------------------
# motto = the popularly-known nickname/tagline for the county.
IRISH_CONTENT = {
    "carlow": dict(motto="The Dolmen County",
        key_places=["Carlow Town", "Tullow", "Bagenalstown", "Borris"],
        key_industries=["Tillage & agriculture", "Food processing", "Brewing"],
        key_history=["Brownshill Dolmen — reputedly the heaviest capstone in Europe",
                     "Norman Carlow Castle guarded the River Barrow",
                     "Site of an early clash in the 1798 Rebellion"]),
    "cavan": dict(motto="The Breffni County",
        key_places=["Cavan Town", "Belturbet", "Virginia", "Ballyjamesduff"],
        key_industries=["Dairy & agriculture", "Manufacturing", "Tourism (lakelands)"],
        key_history=["Drumlin-and-lake landscape with the Shannon Pot, source of the River Shannon",
                     "Heartland of the O'Reilly clan of East Breffni",
                     "One of the three Ulster counties in the Republic"]),
    "clare": dict(motto="The Banner County",
        key_places=["Ennis", "Kilrush", "Doolin", "Lahinch"],
        key_industries=["Tourism", "Aviation (Shannon)", "Agriculture"],
        key_history=["The Cliffs of Moher and the limestone Burren draw visitors worldwide",
                     "Daniel O'Connell's 1828 by-election win here forced Catholic Emancipation",
                     "A stronghold of traditional Irish music"]),
    "cork": dict(motto="The Rebel County",
        key_places=["Cork City", "Cobh", "Kinsale", "Midleton", "Youghal"],
        key_industries=["Pharmaceuticals & tech", "Food & whiskey", "Maritime & port"],
        key_history=["Cobh was the Titanic's final port of call in 1912",
                     "The Lusitania was sunk off the Old Head of Kinsale in 1915",
                     "Home county of Michael Collins, killed at Béal na Bláth in 1922"]),
    "corkcity": dict(motto="The Real Capital",
        key_places=["English Market", "St Fin Barre's Cathedral", "Shandon", "UCC"],
        key_industries=["Technology", "Pharmaceuticals", "Education & port"],
        key_history=["Grew from a 7th-century monastery founded by St Finbarr",
                     "Built on islands in the River Lee — its main streets are culverted channels",
                     "Much of the centre was burned by Crown forces in 1920"]),
    "donegal": dict(motto="Tír Chonaill",
        key_places=["Letterkenny", "Donegal Town", "Bundoran", "Glenveagh"],
        key_industries=["Tourism", "Fishing (Killybegs)", "Donegal tweed"],
        key_history=["Land of the O'Donnell chieftains until the 1607 Flight of the Earls",
                     "Slieve League boasts some of Europe's highest sea cliffs",
                     "Holds Ireland's largest Gaeltacht (Irish-speaking region)"]),
    "dublin": dict(motto="The Pale",
        key_places=["Dublin City", "Dún Laoghaire", "Howth", "Swords"],
        key_industries=["Technology (Silicon Docks)", "Finance (IFSC)", "Tourism & government"],
        key_history=["Founded as a Viking settlement at the 'black pool' (Dubh Linn)",
                     "The 1916 Easter Rising centred on the GPO on O'Connell Street",
                     "Trinity College holds the medieval Book of Kells"]),
    "galway": dict(motto="The City of the Tribes",
        key_places=["Galway City", "Clifden", "Connemara", "Aran Islands"],
        key_industries=["Medical technology", "Tourism", "Irish language & arts"],
        key_history=["Ruled for centuries by fourteen merchant 'tribes'",
                     "Connemara and the Aran Islands form a major Gaeltacht",
                     "The Spanish Arch recalls old trade links with Iberia"]),
    "kerry": dict(motto="The Kingdom",
        key_places=["Killarney", "Tralee", "Dingle", "Kenmare"],
        key_industries=["Tourism", "Dairy (Kerry Group)", "Film & food"],
        key_history=["Carrauntoohil in the MacGillycuddy's Reeks is Ireland's highest peak",
                     "The monastic island of Skellig Michael is a UNESCO World Heritage Site",
                     "Home of Daniel O'Connell, 'The Liberator', at Derrynane"]),
    "kildare": dict(motto="The Thoroughbred County",
        key_places=["Naas", "Newbridge", "Maynooth", "The Curragh"],
        key_industries=["Bloodstock & racing", "Pharmaceuticals", "Commuter belt"],
        key_history=["The Curragh plain is the heart of Irish horse racing and the Irish National Stud",
                     "St Brigid founded her great monastery at Kildare ('church of the oak')",
                     "Maynooth is home to Ireland's national seminary and a university"]),
    "kilkenny": dict(motto="The Marble City",
        key_places=["Kilkenny City", "Thomastown", "Graiguenamanagh", "Callan"],
        key_industries=["Tourism", "Craft & design", "Brewing (Smithwick's)"],
        key_history=["Kilkenny Castle was the seat of the powerful Butler/Ormonde dynasty",
                     "The 1366 Statutes of Kilkenny tried to curb Gaelic culture among settlers",
                     "Capital of Confederate Ireland in the 1640s; a hurling powerhouse"]),
    "laois": dict(motto="The O'Moore County",
        key_places=["Portlaoise", "Portarlington", "Mountmellick", "Abbeyleix"],
        key_industries=["Agriculture", "Logistics & distribution", "Tourism"],
        key_history=["The Rock of Dunamase is a dramatic ruined hilltop fortress",
                     "Formerly 'Queen's County', planted under Mary I in the 1550s",
                     "The Slieve Bloom Mountains rise along its western edge"]),
    "leitrim": dict(motto="The Wild Rose County",
        key_places=["Carrick-on-Shannon", "Manorhamilton", "Drumshanbo"],
        key_industries=["Tourism (waterways)", "Agriculture", "Craft distilling"],
        key_history=["Has the shortest coastline and smallest population of any Irish county",
                     "The Shannon–Erne Waterway threads through its drumlins and lakes",
                     "Birthplace of 1916 signatory Seán Mac Diarmada"]),
    "limerick": dict(motto="The Treaty County",
        key_places=["Limerick City", "Adare", "Newcastle West", "Foynes"],
        key_industries=["Technology & manufacturing", "Education (UL)", "Agriculture"],
        key_history=["The 1691 Treaty of Limerick ended the Williamite War in Ireland",
                     "King John's Castle has guarded the Shannon since the 13th century",
                     "Foynes flying-boat base is the birthplace of Irish coffee"]),
    "longford": dict(motto="The Slashers",
        key_places=["Longford Town", "Granard", "Ballymahon", "Edgeworthstown"],
        key_industries=["Agriculture", "Manufacturing", "Tourism"],
        key_history=["The Iron-Age Corlea Trackway, a preserved bog road, dates to 148 BC",
                     "Associated with writers Oliver Goldsmith and Maria Edgeworth",
                     "Royal Canal and Camlin river country in the Irish midlands"]),
    "louth": dict(motto="The Wee County",
        key_places=["Dundalk", "Drogheda", "Carlingford", "Ardee"],
        key_industries=["Manufacturing & food", "Brewing", "Ports & logistics"],
        key_history=["Ireland's smallest county, on the Cooley Peninsula of the Táin Bó Cúailnge epic",
                     "Mellifont was Ireland's first Cistercian abbey (1142)",
                     "Monasterboice's high crosses are among the finest in Ireland"]),
    "mayo": dict(motto="The Maritime County",
        key_places=["Castlebar", "Westport", "Ballina", "Achill Island"],
        key_industries=["Tourism", "Agriculture", "Medical devices"],
        key_history=["Knock Shrine marks a reported 1879 Marian apparition",
                     "The 1798 'Year of the French' saw the Races of Castlebar",
                     "Pirate queen Grace O'Malley (Granuaile) ruled its coast in the 1500s"]),
    "meath": dict(motto="The Royal County",
        key_places=["Navan", "Trim", "Kells", "Hill of Tara"],
        key_industries=["Agriculture", "Commuter belt", "Heritage tourism"],
        key_history=["The Hill of Tara was the seat of the High Kings of Ireland",
                     "Newgrange in the Boyne Valley predates the pyramids and Stonehenge",
                     "Trim Castle is the largest Anglo-Norman castle in Ireland"]),
    "monaghan": dict(motto="The Farney County",
        key_places=["Monaghan Town", "Carrickmacross", "Clones", "Castleblayney"],
        key_industries=["Poultry & mushrooms", "Food processing", "Carrickmacross lace"],
        key_history=["A county of drumlins and small lakes in the historic province of Ulster",
                     "Birthplace of poet Patrick Kavanagh at Inniskeen",
                     "Carrickmacross has been famous for fine lace since the 1820s"]),
    "offaly": dict(motto="The Faithful County",
        key_places=["Tullamore", "Birr", "Banagher", "Clonmacnoise"],
        key_industries=["Whiskey (Tullamore D.E.W.)", "Agriculture", "Peatlands & energy"],
        key_history=["Clonmacnoise was one of medieval Europe's great monastic centres",
                     "Birr Castle's 1845 'Leviathan' was the world's largest telescope for decades",
                     "Formerly 'King's County', renamed at independence"]),
    "roscommon": dict(motto="The Rossies",
        key_places=["Roscommon Town", "Boyle", "Castlerea", "Strokestown"],
        key_industries=["Livestock & agriculture", "Tourism", "Peat"],
        key_history=["Rathcroghan was the legendary capital of Connacht and seat of Queen Medb",
                     "Strokestown Park houses the National Famine Museum",
                     "Birthplace of Douglas Hyde, Ireland's first President"]),
    "sligo": dict(motto="The Yeats County",
        key_places=["Sligo Town", "Strandhill", "Enniscrone", "Tobercurry"],
        key_industries=["Tourism & surfing", "Agriculture", "Services"],
        key_history=["W. B. Yeats is buried at Drumcliffe 'under bare Ben Bulben's head'",
                     "Carrowmore is one of Europe's largest megalithic cemeteries",
                     "Knocknarea is crowned by the cairn said to hold Queen Maeve"]),
    "tipperary": dict(motto="The Premier County",
        key_places=["Clonmel", "Thurles", "Cashel", "Nenagh"],
        key_industries=["Dairy (Golden Vale)", "Agri-food", "Tourism"],
        key_history=["The Rock of Cashel was the seat of the kings of Munster",
                     "The GAA was founded in Thurles in 1884",
                     "Inspired the WWI marching song 'It's a Long Way to Tipperary'"]),
    "waterford": dict(motto="The Déise",
        key_places=["Waterford City", "Dungarvan", "Tramore", "Ardmore"],
        key_industries=["Waterford Crystal", "Pharmaceuticals", "Agri-food (the blaa)"],
        key_history=["Founded by Vikings in 914, it is Ireland's oldest city",
                     "Reginald's Tower has stood over the quays for a millennium",
                     "The 1170 marriage of Strongbow and Aoife sealed the Norman conquest"]),
    "westmeath": dict(motto="The Lake County",
        key_places=["Mullingar", "Athlone", "Belvedere", "Lough Ennell"],
        key_industries=["Beef & agriculture", "Manufacturing", "Tourism"],
        key_history=["Athlone sits at Ireland's geographic centre on the River Shannon",
                     "Sean's Bar in Athlone claims to be Ireland's oldest pub",
                     "Belvedere House is famed for its Georgian gardens and follies"]),
    "wexford": dict(motto="The Model County",
        key_places=["Wexford Town", "Enniscorthy", "Gorey", "New Ross"],
        key_industries=["Agriculture & soft fruit", "Tourism", "Opera Festival"],
        key_history=["The 1798 Rebellion's fiercest fighting was at Vinegar Hill, Enniscorthy",
                     "The Normans first landed nearby at Bannow Bay in 1169",
                     "The Kennedy ancestral homestead stands at Dunganstown near New Ross"]),
    "wicklow": dict(motto="The Garden of Ireland",
        key_places=["Wicklow Town", "Bray", "Greystones", "Glendalough"],
        key_industries=["Tourism", "Film", "Agriculture"],
        key_history=["Glendalough was a monastic city founded by St Kevin in the 6th century",
                     "The Military Road was cut through the mountains to flush out 1798 rebels",
                     "Powerscourt's gardens and waterfall are among Ireland's finest"]),
}


def main():
    counties = json.loads(COUNTIES.read_text(encoding="utf-8"))
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))
    centroids = {}
    for f in geo["features"]:
        slug = f["properties"].get("slug")
        c = feature_centroid(f["geometry"])
        if slug and c:
            centroids[slug] = c

    updated_centroids = enriched = 0
    for c in counties:
        slug = c["slug"]
        if slug in centroids:
            c["centroid"] = centroids[slug]
            updated_centroids += 1
        if slug in IRISH_CONTENT:
            c.update(IRISH_CONTENT[slug])
            enriched += 1

    COUNTIES.write_text(json.dumps(counties, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"centroids updated: {updated_centroids}/{len(counties)}")
    print(f"Irish counties enriched: {enriched}/{len(IRISH_CONTENT)}")


if __name__ == "__main__":
    main()
