const map=L.map("map",{zoomControl:true,attributionControl:false}).setView([53.4,-8.0],7);
L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",{maxZoom:18}).addTo(map);

let countiesMeta={};

async function loadEverything(){
  const [metaRes,geoRes,meRes]=await Promise.all([
    fetch("/api/counties/"),
    fetch("/static/data/ireland_counties.geojson"),
    fetch("/api/geo/me")
  ]);

  const metaList=await metaRes.json();
  const geoData=await geoRes.json();
  const me=await meRes.json();

  metaList.forEach(c=>countiesMeta[c.slug]=c);

  const layer=L.geoJSON(geoData,{
    style:()=>({color:"#ffffff",weight:1.2,fillOpacity:0.0,fillColor:"transparent"}),
    onEachFeature:(feature,layer)=>{
      const slug=feature.properties.slug;
      const county=countiesMeta[slug];

      layer.on("mouseover",()=>{
        layer.setStyle({
          weight:2,
          color:county.primary_colour||"#ffffff",
          fillColor:county.primary_colour||"#ffffff",
          fillOpacity:0.2
        });
        layer.bindTooltip(`<b>${county.name}</b><br>Colours: ${county.colours.join(" / ")}`,{className:"county-tooltip"}).openTooltip();
      });

      layer.on("mouseout",()=>{
        layer.setStyle({color:"#ffffff",weight:1.2,fillOpacity:0.0,fillColor:"transparent"});
        layer.closeTooltip();
      });

      layer.on("click",()=>{window.location.href=`/county/${slug}`;});
    }
  }).addTo(map);

  if(me.guessed_county){
    layer.eachLayer(l=>{
      if(l.feature.properties.slug===me.guessed_county){
        map.fitBounds(l.getBounds());
      }
    });
  }
}

loadEverything().catch(console.error);
