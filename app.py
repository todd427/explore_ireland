from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import counties, geo

app = FastAPI(title="Explore Islands")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(counties.router, prefix="/api/counties", tags=["counties"])
app.include_router(geo.router, prefix="/api/geo", tags=["geo"])

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/county/{slug}", response_class=HTMLResponse)
async def county_page(request: Request, slug: str):
    from routers.counties import COUNTY_DATA
    county = COUNTY_DATA.get(slug)
    return templates.TemplateResponse("county.html", {"request": request, "county": county})
