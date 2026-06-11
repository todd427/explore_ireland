// County detail page: draws the county outline, drops colour-coded tourism
// pins (from OpenStreetMap), and fills the listings below the map.
// Config is injected by the template into window.COUNTY.
(function () {
  const cfg = window.COUNTY;
  if (!cfg || !cfg.slug) return;
  const el = document.getElementById("county-map");
  if (!el) return;

  // Tourism categories -> colour + label. Keep in sync with county.css.
  const CATS = {
    eat_drink: { colour: "#ff8c42", label: "Eat & Drink" },
    stay:      { colour: "#4ea1ff", label: "Stay" },
    see_do:    { colour: "#2dd4bf", label: "See & Do" },
  };

  const map = L.map("county-map", {
    zoomControl: true,
    attributionControl: true,
    scrollWheelZoom: false,
  });
  map.zoomControl.setPosition("bottomright");
  map.attributionControl.setPrefix(false);

  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 18, attribution: "© OpenStreetMap contributors" }
  ).addTo(map);

  const fallback = () => {
    const c = cfg.centroid;
    if (c && (c.lat || c.lng)) map.setView([c.lat, c.lng], 8);
    else map.setView([53.4, -7.9], 6);
  };

  // 1. Draw the county outline, then fit to it.
  fetch("/static/data/all_regions.geojson")
    .then((r) => r.json())
    .then((gj) => {
      const feat = gj.features.find(
        (f) => f.properties && f.properties.slug === cfg.slug
      );
      if (!feat) return fallback();
      const layer = L.geoJSON(feat, {
        style: {
          color: cfg.primary || "#ffcc00",
          weight: 2,
          fillColor: cfg.primary || "#ffcc00",
          fillOpacity: 0.10,
        },
      }).addTo(map);
      map.fitBounds(layer.getBounds(), { padding: [24, 24] });
    })
    .catch(fallback);

  // 2. Load POIs: drop pins on the map and build the listings.
  const escapeHtml = (s) =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  fetch(`/static/data/poi/${cfg.slug}.json`)
    .then((r) => (r.ok ? r.json() : null))
    .then((poi) => {
      const listings = document.getElementById("listings");
      if (!poi || !poi.categories) {
        if (listings) listings.remove();
        return;
      }
      Object.entries(CATS).forEach(([key, meta]) => {
        const items = poi.categories[key] || [];
        if (!items.length) return;

        // Map pins
        items.forEach((it) => {
          if (it.lat == null || it.lon == null) return;
          const site = it.website
            ? `<br><a href="${escapeHtml(it.website)}" target="_blank" rel="noopener">website</a>`
            : "";
          L.circleMarker([it.lat, it.lon], {
            radius: 5,
            color: meta.colour,
            weight: 1.5,
            fillColor: meta.colour,
            fillOpacity: 0.8,
          })
            .bindPopup(
              `<strong>${escapeHtml(it.name)}</strong><br>` +
                `<span style="opacity:.7">${escapeHtml(it.kind)}` +
                `${it.cuisine ? " · " + escapeHtml(it.cuisine) : ""}</span>${site}`
            )
            .addTo(map);
        });

        // Listing card
        const card = document.createElement("section");
        card.className = "card poi-card";
        const rows = items
          .map((it) => {
            const name = it.website
              ? `<a href="${escapeHtml(it.website)}" target="_blank" rel="noopener">${escapeHtml(it.name)}</a>`
              : escapeHtml(it.name);
            const sub = [it.kind, it.cuisine].filter(Boolean).map(escapeHtml).join(" · ");
            return `<li><span class="poi-dot" style="background:${meta.colour}"></span>` +
              `<span class="poi-name">${name}</span>` +
              `<span class="poi-sub">${sub}</span></li>`;
          })
          .join("");
        card.innerHTML =
          `<h2><span class="poi-dot" style="background:${meta.colour}"></span>${meta.label}` +
          ` <span class="poi-count">${items.length}</span></h2>` +
          `<ul class="poi-list">${rows}</ul>`;
        if (listings) listings.appendChild(card);
      });

      const note = document.getElementById("poi-note");
      if (note) note.hidden = false;
    })
    .catch(() => {});
})();
