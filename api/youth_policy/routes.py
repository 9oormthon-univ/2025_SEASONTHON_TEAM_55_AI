from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
import asyncio
import time
from datetime import datetime
from .services import fetch_policies, parse_date_range, get_rank10, enrich_policies

router = APIRouter()

@router.get("/policies")
def get_policies(address: str = Query(..., description="예: 광주광역시 남구")):
    start = time.time()
    rows = fetch_policies(address)
    if not rows:
        return JSONResponse(status_code=200, content={"message": "No Content"})

    today = datetime.today().date()
    policies = []

    for row in rows:
        end_date = parse_date_range(row.get("aplyYmd", ""))
        if end_date and end_date < today: continue
        if "청년" not in (row.get("plcyNm") or ""): continue

        url = row.get("aplyUrlAddr") or row.get("refUrlAddr1") or row.get("refUrlAddr2") or ""
        policies.append({
            "plcyNm": row.get("plcyNm", ""),
            "sprvsnInstCdNm": row.get("sprvsnInstCdNm", ""),
            "inqCnt": int(row.get("inqCnt") or 0),
            "url": url
        })

    if not policies:
        return JSONResponse(status_code=200, content={"message": "No Content"})

    policies = sorted(policies, key=lambda x: x["inqCnt"], reverse=True)[:20]
    return JSONResponse(status_code=200, content={"policies": policies})

@router.get("/top10")
def rank10():
    start = time.time()
    rank_list = get_rank10()
    enriched = asyncio.run(enrich_policies(rank_list))
    return JSONResponse(status_code=200, content={
        "policies": enriched
    })