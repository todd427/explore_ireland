// Renders a small map highlighting just the county the user clicked.
// Config is injected by the template into window.COUNTY.
(function () {
  const cfg = window.COUNTY;
  if (!cfg || !cfg.slug) return;
  const el = document.getElementById("county-map");
  if (!el) return;

  const map = L.map("county-map", {
    zoomControl: true,
    attributionControl: false,
    scrollWheelZoom: false,
  });
  map.zoomControl.setPosition("bottomright");

  L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 12 }
  ).addTo(map);

  const fallback = () => {
    const c = cfg.centroid;
    if (c && (c.lat || c.lng)) map.setView([c.lat, c.lng], 8);
    else map.setView([53.4, -7.9], 6); // centre of Ireland
  };

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
          fillOpacity: 0.18,
        },
      }).addTo(map);
      map.fitBounds(layer.getBounds(), { padding: [24, 24] });
    })
    .catch(fallback);
})();
