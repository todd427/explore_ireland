const map = L.map("map", {
  zoomControl: true,
  attributionControl: false
}).setView([54.0, -4.0], 6);

map.zoomControl.setPosition("bottomright");

L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  { maxZoom: 12 }
).addTo(map);

let countiesMeta = {};
let countyLayer = null;
let currentMode = "outline";   // outline | colours
let overlayMode = "political"; // political | cultural | geographic

function applyBaseStyleForLayer(layer) {
  const slug = layer.feature.properties.slug;
  const county = countiesMeta[slug] || {};
  if (overlayMode === "geographic") {
    layer.setStyle({opacity:0, fillOpacity:0});
    return;
  }
  if (currentMode === "colours") {
    layer.setStyle({
      color: county.primary_colour || "#ffffff",
      weight: 1.6,
      fillColor: county.primary_colour || "#ffffff",
      fillOpacity: 0.18
    });
  } else {
    layer.setStyle({
      color: "#ffffff",
      weight: 1.4,
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

function focusRegion(regionSlug) {
  if (!countyLayer) return;
  const target = regionSlug.toLowerCase();
  let combinedBounds = null;
  countyLayer.eachLayer(layer => {
    const slug = layer.feature.properties.slug;
    const county = countiesMeta[slug];
    if (!county || !county.region) return;
    const rSlug = county.region.toLowerCase().replace(/\s+/g,"");
    if (rSlug === target) {
      const b = layer.getBounds();
      if (!combinedBounds) combinedBounds = b;
      else combinedBounds.extend(b);
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

  document.querySelectorAll("[data-region]").forEach(btn => {
    btn.addEventListener("click", () => {
      const region = btn.getAttribute("data-region");
      focusRegion(region);
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
  const [metaRes, geoRes] = await Promise.all([
    fetch("/api/counties/"),
    fetch("/static/data/all_regions.geojson"),
  ]);

  const metaList = await metaRes.json();
  const geoData = await geoRes.json();

  metaList.forEach(c => { countiesMeta[c.slug] = c; });

  countyLayer = L.geoJSON(geoData, {
    style: (feature) => ({
      color: "#ffffff",
      weight: 1.4,
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
          `<b>${county.name}</b><br>${(county.region || "")}`,
          { className: "county-tooltip", sticky: true }
        ).openTooltip();
      });

      layer.on("mouseout", () => {
        layer.closeTooltip();
        applyBaseStyleForLayer(layer);
      });

      layer.on("click", (e) => {
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
}

document.addEventListener("DOMContentLoaded", () => {
  setupUI();
  loadEverything().catch(console.error);
});
