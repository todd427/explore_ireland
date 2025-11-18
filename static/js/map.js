const map = L.map("map", {
  zoomControl: true,
  attributionControl: false
}).setView([53.4, -8.0], 7);

L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  { maxZoom: 18 }
).addTo(map);

let countiesMeta = {};
let countyLayer = null;
let currentMode = "outline";   // outline | colours
let overlayMode = "political"; // political | cultural | geographic

function applyBaseStyleForLayer(layer) {
  const slug = layer.feature.properties.slug;
  const county = countiesMeta[slug] || {};
  if (overlayMode === "geographic") {
    // should be hidden; but guard anyway
    layer.setStyle({opacity:0, fillOpacity:0});
    return;
  }
  if (currentMode === "colours") {
    layer.setStyle({
      color: county.primary_colour || "#ffffff",
      weight: 1.8,
      fillColor: county.primary_colour || "#ffffff",
      fillOpacity: 0.18
    });
  } else {
    // outline mode
    layer.setStyle({
      color: "#ffffff",
      weight: 1.5,
      fillColor: "transparent",
      fillOpacity: 0.0
    });
  }
}

function applyBaseStyle() {
  if (!countyLayer) return;
  countyLayer.eachLayer(layer => applyBaseStyleForLayer(layer));
}

function setMode(mode) {
  currentMode = mode;
  applyBaseStyle();
  updateModeButtons();
}

function setOverlay(mode) {
  overlayMode = mode;
  if (mode === "geographic") {
    if (map.hasLayer(countyLayer)) {
      map.removeLayer(countyLayer);
    }
  } else {
    if (!map.hasLayer(countyLayer)) {
      countyLayer.addTo(map);
    }
    applyBaseStyle();
  }
  updateOverlayButtons();
}

function focusProvince(provinceSlug) {
  if (!countyLayer) return;
  const target = provinceSlug.toLowerCase();
  let combinedBounds = null;
  countyLayer.eachLayer(layer => {
    const slug = layer.feature.properties.slug;
    const county = countiesMeta[slug];
    if (county && county.province && county.province.toLowerCase() === target) {
      const b = layer.getBounds();
      if (!combinedBounds) {
        combinedBounds = b;
      } else {
        combinedBounds.extend(b);
      }
    }
  });
  if (combinedBounds) {
    map.fitBounds(combinedBounds, { padding: [30, 30] });
  }
}

function setupUI() {
  const outlineBtn = document.querySelector('[data-mode="outline"]');
  const coloursBtn = document.querySelector('[data-mode="colours"]');
  const politicalBtn = document.querySelector('[data-overlay="political"]');
  const culturalBtn = document.querySelector('[data-overlay="cultural"]');
  const geographicBtn = document.querySelector('[data-overlay="geographic"]');

  outlineBtn.addEventListener("click", () => setMode("outline"));
  coloursBtn.addEventListener("click", () => setMode("colours"));

  politicalBtn.addEventListener("click", () => setOverlay("political"));
  culturalBtn.addEventListener("click", () => setOverlay("cultural"));
  geographicBtn.addEventListener("click", () => setOverlay("geographic"));

  document.querySelectorAll("[data-province]").forEach(btn => {
    btn.addEventListener("click", () => {
      const prov = btn.getAttribute("data-province");
      focusProvince(prov);
    });
  });

  updateModeButtons();
  updateOverlayButtons();
}

function updateModeButtons() {
  document.querySelectorAll("[data-mode]").forEach(btn => {
    const mode = btn.getAttribute("data-mode");
    btn.classList.toggle("active", mode === currentMode);
  });
}

function updateOverlayButtons() {
  document.querySelectorAll("[data-overlay]").forEach(btn => {
    const mode = btn.getAttribute("data-overlay");
    btn.classList.toggle("active", mode === overlayMode);
  });
}

async function loadEverything() {
  const [metaRes, geoRes, meRes] = await Promise.all([
    fetch("/api/counties/"),
    fetch("/static/data/ireland_counties.geojson"),
    fetch("/api/geo/me")
  ]);

  const metaList = await metaRes.json();
  const geoData = await geoRes.json();
  const me = await meRes.json();

  metaList.forEach(c => { countiesMeta[c.slug] = c; });

  countyLayer = L.geoJSON(geoData, {
    style: () => ({
      color: "#ffffff",
      weight: 1.5,
      fillOpacity: 0.0,
      fillColor: "transparent",
      className: "county-shape"
    }),
    onEachFeature: (feature, layer) => {
      const slug = feature.properties.slug;
      const county = countiesMeta[slug];

      layer.on("mouseover", () => {
        if (overlayMode === "geographic") return;
        if (!county) return;
        layer.setStyle({
          weight: 3,
          color: county.primary_colour || "#ffffff",
          fillColor: county.primary_colour || "#ffffff",
          fillOpacity: 0.3
        });
        layer.bindTooltip(
          `<b>${county.name}</b><br>${(county.colours || []).join(" / ")}`,
          { className: "county-tooltip", sticky: true }
        ).openTooltip();
      });

      layer.on("mouseout", () => {
        layer.closeTooltip();
        applyBaseStyleForLayer(layer);
      });

      layer.on("click", (e) => {
        // On touch devices, first tap highlights, second tap navigates
        if (e.originalEvent && e.originalEvent.pointerType === "touch") {
          if (!layer._touchedOnce) {
            layer._touchedOnce = true;
            setTimeout(() => { layer._touchedOnce = false; }, 800);
            return;
          }
        }
        window.location.href = `/county/${slug}`;
      });
    }
  }).addTo(map);

  applyBaseStyle();

  const guessed = me.guessed_county;
  if (guessed && countyLayer) {
    countyLayer.eachLayer(layer => {
      if (layer.feature.properties.slug === guessed) {
        map.fitBounds(layer.getBounds(), { padding: [30, 30] });
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  setupUI();
  loadEverything().catch(console.error);
});
