# Explore Ireland – Placeholder 32 Counties

This build uses a synthetic grid of 32 rectangular polygons over Ireland's bounding box.
Each rectangle is mapped to one of the traditional 32 counties, with placeholder colours
(by province). This is intended purely for UI and interaction testing:

- Hover highlight in county colours
- Click-through to simple county detail pages
- Province quick-zoom buttons
- Map style and overlay toggles

Later, replace `static/data/ireland_counties.geojson` and `data/ireland_counties.geojson`
with real boundary data and enrich `data/counties.json` with proper content.
