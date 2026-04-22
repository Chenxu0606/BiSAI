import requests
import time

API_KEY = "519487ed40595fd66ea1c7485fcbc691"
TARGET_COUNT = 30

def get_restaurants(city, page=1):
    url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": API_KEY, "keywords": "美食", "city": city,
        "types": "050000", "page": page, "extensions": "all"
    }
    try:
        data = requests.get(url, params=params, timeout=15).json()
        return data if data.get("status") == "1" else None
    except:
        return None

def parse_restaurant(poi, city):
    biz_ext = poi.get("biz_ext", {})
    return {
        "城市": city, "店铺名称": poi.get("name", ""),
        "详细地址": poi.get("address", ""), "类别": poi.get("type", ""),
        "评分": float(biz_ext.get("rating", 0)) if biz_ext.get("rating") else 0.0
    }

def get_restaurant_data(city):
    all_data = []
    page = 1
    while len(all_data) < TARGET_COUNT:
        data = get_restaurants(city, page)
        if not data: break
        for poi in data.get("pois", []):
            if len(all_data) >= TARGET_COUNT: break
            all_data.append(parse_restaurant(poi, city))
        page += 1
        time.sleep(0.2)
    print(f"✅ 餐饮：获取到 {len(all_data)} 条数据")
    return all_data

