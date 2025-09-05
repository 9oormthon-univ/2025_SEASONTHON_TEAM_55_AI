import requests
from ..common.config import Config

def get_zip_code(keyword: str):
    params = {
        "confmKey": Config.JUSO_API_KEY,
        "currentPage": 1,
        "countPerPage": 1,
        "keyword": keyword,
        "resultType": "json"
    }

    r = requests.get(Config.JUSO_BASE_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()

    juso_list = data.get("results", {}).get("juso")
    if not juso_list:
        return ""

    item = juso_list[0]
    return item.get("admCd", "")[:5]