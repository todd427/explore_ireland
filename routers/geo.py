from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/me")
async def my_location(request: Request):
    ip = request.client.host
    return {"ip": ip, "guessed_county": None, "confidence": 0.0}
