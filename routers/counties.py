import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter()

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "counties.json"

with open(DATA_PATH, "r", encoding="utf-8") as f:
    COUNTY_DATA = {c["slug"]: c for c in json.load(f)}

@router.get("/")
async def list_counties():
    return list(COUNTY_DATA.values())

@router.get("/{slug}")
async def get_county(slug: str):
    county = COUNTY_DATA.get(slug)
    if not county:
        raise HTTPException(status_code=404, detail="County not found")
    return county
