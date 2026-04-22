import requests

API_KEY = "yur9o2XXo15GYfXveKM6io37CScGJFgF"


def get_scenic_data(city, count=20):
    try:
        search_url = "http://api.map.baidu.com/place/v2/search"
        search_params = {
            "query": "景点", "region": city, "output": "json",
            "ak": API_KEY, "page_size": count, "scope": 2
        }
        response = requests.get(search_url, params=search_params, timeout=10)
        result = response.json()
        if result.get("status") != 0:
            return []

        scenic_list = []
        for item in result.get("results", [])[:count]:
            info = item.get("detail_info", {})
            scenic_list.append({
                "景点名称": item.get("name", "未知"),
                "具体位置": item.get("address", "未知"),
                "评分": info.get("overall_rating", "暂无"),
                "参考价格": info.get("price", "免费"),
                "营业时间": info.get("open_time", "未知"),
                "城市": city
            })
        return scenic_list
    except:
        return []

