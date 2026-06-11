# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

"Explore Islands – Ireland + UK" — a FastAPI app serving a dark-mode Leaflet map of
Irish counties (grouped by province: Ulster/Connacht/Leinster/Munster) and UK level-2
regions (grouped by nation: England/Scotland/Wales/Northern Ireland). Clicking a region
opens a detail page. Despite the `explore_ireland` directory name, the app title is
"Explore Islands" and covers both Ireland and the UK.

## Commands

```bash
pip install -r requirements.txt          # deps: fastapi, uvicorn, jinja2, python-multipart
uvicorn app:app --reload                 # run dev server at http://127.0.0.1:8000
```

There are no tests, linter config, or build step in this repo.

## Architecture

FastAPI backend + vanilla-JS Leaflet frontend, joined by a **`slug`** key.

- `app.py` — entrypoint. Mounts `/static`, sets up Jinja2 templates, includes routers
  under `/api/counties` and `/api/geo`. Serves two HTML pages: `/` (map) and
  `/county/{slug}` (detail page, looks up `COUNTY_DATA` directly).
- `routers/counties.py` — loads `data/counties.json` at import time into the
  `COUNTY_DATA` dict keyed by slug. Exposes `GET /api/counties/` (list) and
  `GET /api/counties/{slug}`.
- `routers/geo.py` — `GET /api/geo/me` returns caller IP; county guessing is stubbed
  (returns `None`).
- `static/js/map.js` — the whole frontend. On load it fetches `/api/counties/` (metadata)
  and `/static/data/all_regions.geojson` (geometry), then joins them on
  `feature.properties.slug`. Supports a render mode (`outline` | `colours`) and an overlay
  mode (`political` | `cultural` | `geographic`). Clicking a feature navigates to
  `/county/${slug}`.
- `templates/index.html`, `templates/county.html` — Leaflet/CSS are pulled from unpkg CDN;
  local assets from `/static`.

### The slug contract (most important to understand)

A region exists end-to-end only if its `slug` appears in **both**:
1. `data/counties.json` — each object has `slug`, `name`, `region`, `country_group`,
   colours, and (mostly empty) `key_places`/`key_industries`/`key_history`/`centroid` fields.
2. `static/data/all_regions.geojson` — each feature's `properties` carries `name`, `slug`,
   `region`, plus the geometry.

The JS join is `countiesMeta[feature.properties.slug]`; a geometry feature with no matching
metadata slug (or vice-versa) silently renders without data. When adding or renaming
regions, update both files and keep slugs identical.

### Data sources & duplication caveat

- The map loads geometry from `static/data/all_regions.geojson` (128 features). Note that
  `data/` also contains `all_regions.geojson` and `ireland_counties.geojson` copies — these
  are **not** the ones served to the map; `static/data/` is the live copy. Don't assume
  editing `data/*.geojson` changes the map.
- Region geometry originates from GADM IRL/GBR level-2 (per README); county metadata in
  `counties.json` is largely placeholder (empty mottos, zeroed centroids).
- Root-level `*.zip` files and `ls`/`requirements.txt` duplicates are stale build snapshots,
  not part of the running app. (`requirements.txt` is the real dep file; `ls` is an
  accidental copy of it.)
