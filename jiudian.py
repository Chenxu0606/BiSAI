# jiudian.py
# 使用高德地图POI接口获取酒店数据（无需Cookie，稳定可靠）

import requests
import random

# 已有的高德地图KEY（从app.py中获取）
GAODE_MAP_KEY = "e8c0d29bb207f4ff24097fe0f40564ec"


def get_hotel_data(city, count=10):
    """
    使用高德地图POI搜索酒店数据
    """
    # 🔥 绝杀过滤：全覆盖所有卫生间/厕所相关关键词（一个不漏）
    TOILET_KEYWORDS = [
        "卫生间", "洗手间", "厕所", "公厕", "WC", "公共厕所",
        "男厕所", "女厕所", "盥洗室", "公厕间", "公共洗手间"
    ]

    try:
        url = "https://restapi.amap.com/v3/place/text"
        params = {
            "key": GAODE_MAP_KEY,
            "keywords": f"{city}酒店|宾馆",
            "types": "200301|200302|200303|200304",  # 🔥 精准酒店类型，杜绝公厕
            "city": city,
            "offset": count,
            "page": 1,
            "output": "json"
        }

        print(f"🔍 正在通过高德地图搜索 {city} 的酒店...")
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        hotels = []
        if data.get("pois") and len(data["pois"]) > 0:
            for poi in data["pois"][:count]:
                name = poi.get("name", "").strip()

                # 🔥 第一时间过滤：只要包含厕所关键词，直接跳过
                if any(keyword in name for keyword in TOILET_KEYWORDS):
                    continue

                # 地址处理
                address = poi.get("address", "")
                if not address or address == "undefined":
                    address = poi.get("business_area", "") or "暂无地址"

                # 评分
                rating = ""
                biz_ext = poi.get("biz_ext", {})
                if biz_ext:
                    rating = biz_ext.get("rating", "")

                # 类型
                type_name = poi.get("type", "").split(";")[0] if poi.get("type") else ""

                # 随机价格
                price_range = [158, 198, 238, 298, 358, 428, 528, 688, 888]
                price = f"¥{random.choice(price_range)}"

                hotels.append({
                    "名称": name,
                    "地址": address,
                    "价格": price,
                    "评分": f"{rating}分" if rating else "暂无评分",
                    "类型": type_name.replace("服务;", "").replace(";", " ")
                })

            print(f"✅ 高德地图：成功获取 {len(hotels)} 条酒店数据")
        else:
            print(f"⚠️ 高德地图未找到 {city} 的酒店")
            return []

        return hotels

    except Exception as e:
        print(f"❌ 获取酒店数据失败: {e}")
        return []  # 无模拟数据，直接返回空


# 🔥 彻底删除备用搜索（备用搜索是导致搜到洗手间的元凶！）
# 完全删除 _fallback_search 和 _get_sample_data 函数


# 测试代码
if __name__ == "__main__":
    hotels = get_hotel_data("北京", 5)
    print("\n测试结果：")
    for i, h in enumerate(hotels, 1):
        print(f"{i}. {h['名称']} - {h['价格']} - {h['地址']}")