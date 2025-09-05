import requests
import asyncio
import httpx
import time
from datetime import datetime
from .utils import get_zip_code
from ..common.config import Config

PAGE_SIZE, MAX_ROWS = 100, 200

def fetch_policies(ziptxt: str, max_rows=MAX_ROWS):
    all_rows, page = [], 1
    zipCd = get_zip_code(ziptxt)

    parts, zipKwd = ziptxt.split(), ""
    if len(parts) > 1:
        second = parts[1]
        if second.endswith(("시", "군")): zipKwd = second[:-1]
        elif second.endswith("구") and len(second) > 2: zipKwd = second[:-1]
        else: zipKwd = second

    while len(all_rows) < max_rows:
        params = {
            "apiKeyNm": Config.YOUTH_API_KEY, "rtnType": "json",
            "pageNum": page, "pageSize": PAGE_SIZE,
            "plcyNm": zipKwd, "zipCd": zipCd
        }
        r = requests.get(Config.YOUTH_POLICY_BASE_URL, params=params, timeout=30)
        rows = r.json().get("result", {}).get("youthPolicyList", [])
        if not rows: break
        all_rows.extend([row for row in rows if row.get("zipCd", "").startswith(zipCd)])
        page += 1
    return all_rows[:max_rows]

def parse_date_range(date_str: str):
    try:
        return datetime.strptime(date_str.split("~")[1].strip(), "%Y%m%d").date()
    except:
        return None

def get_rank10():
    s = requests.Session()
    s.get(Config.YOUTH_RANK_BASE_URL, timeout=8)
    r = s.get(f"{Config.YOUTH_RANK_BASE_URL}/wrk/yrm/plcy/RankPlcy", 
              params={"isMaskingYn": "Y"}, timeout=8)
    r.raise_for_status()
    data = r.json()
    return [{"plcyNo": item["plcyNo"]} for item in data.get("result", {}).get("rankPlcyList", [])]

async def get_policy_detail(client, plcyNo):
    params = {"apiKeyNm": Config.YOUTH_API_KEY, "plcyNo": plcyNo}
    try:
        resp = await client.get(Config.YOUTH_POLICY_BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"API 요청 오류 ({plcyNo}): {e}")
        return {}

    if "result" in data and "youthPolicyList" in data["result"]:
        policies = data["result"]["youthPolicyList"]
        if policies:
            p = policies[0]
            url_final = p.get("aplyUrlAddr") or p.get("refUrlAddr1") or p.get("refUrlAddr2") or ""
            return {
                "plcyNo": plcyNo,
                "plcyNm": p.get("plcyNm"),
                "sprvsnInstCdNm": p.get("sprvsnInstCdNm"),
                "inqCnt": int(p.get("inqCnt") or 0),
                "url": url_final,
            }
    return {}

async def enrich_policies(policy_list):
    async with httpx.AsyncClient() as client:
        tasks = [get_policy_detail(client, item["plcyNo"]) for item in policy_list]
        results = await asyncio.gather(*tasks)
    results = [r for r in results if r]
    results.sort(key=lambda x: x.get("inqCnt", 0), reverse=True)
    return results