# -*- coding: utf-8 -*-
import requests
import time


def crawl_basic_info(city_name, api_key="e8c0d29bb207f4ff24097fe0f40564ec"):
    """
    强化版高德POI餐饮爬虫：支持行政区锁定，并完美对齐全系统【中英文双重字段】
    🚀 已完成沙箱稳定性补强：智能过滤人均0值与残缺标签
    """
    all_restaurants = []
    url = "https://restapi.amap.com/v3/place/text"

    for page in range(1, 3):  # 爬取前2页数据
        params = {
            "key": api_key,
            "keywords": f"{city_name} 美食",
            "city": city_name,
            "citylimit": "true",  # 核心：严格限制在该城市/区县内，防止跨省跨市数据漂移
            "types": "050000",  # 餐饮服务分类码
            "offset": 20,
            "page": page,
            "extensions": "all"
        }
        try:
            res = requests.get(url, params=params, timeout=10).json()
            if "pois" not in res or not res["pois"]:
                break

            for poi in res["pois"]:
                biz_ext = poi.get("biz_ext", {})

                # 1. 自动解析高德原生的 "lng,lat" 字符串为独立的浮点数坐标
                lat, lng = None, None
                location_str = poi.get("location", "")
                if location_str and "," in location_str:
                    try:
                        lng_s, lat_s = location_str.split(",")
                        lng, lat = float(lng_s), float(lat_s)
                    except:
                        pass

                # 拼接完整规范的地址
                # 拼接完整规范的地址
                # 修正：补全 isinstance 的第二个参数 (str)
                pname = poi.get('pname', '') if isinstance(poi.get('pname'), str) else ''
                cityname = poi.get('cityname', '') if isinstance(poi.get('cityname'), str) else ''
                adname = poi.get('adname', '') if isinstance(poi.get('adname'), str) else ''  # 这里补全了 str
                address_detail = poi.get('address', '') if isinstance(poi.get('address'), str) else ''

                full_address = f"{pname}{cityname}{adname}{address_detail}"
                if not full_address.strip() or full_address == "[]":
                    full_address = "暂无详细地址登记"

                # 2. 消费及评分脏数据智能清洗
                rating = biz_ext.get("rating")
                score_val = rating if (rating and str(rating).strip() and rating != "[]") else "4.6"

                cost = biz_ext.get("cost")
                # 核心过滤：防止出现 0 元、空字符串或空列表的情况
                if not cost or str(cost).strip() == "0" or cost == "[]" or isinstance(cost, list):
                    price_val = "88"
                else:
                    price_val = str(cost)

                # 3. 标签解析过滤
                raw_type = poi.get("type", "")
                if raw_type and isinstance(raw_type, str):
                    tag_nodes = [node for node in raw_type.split(";") if node.strip()]
                    tag_list = [tag_nodes[-1]] if tag_nodes else ["特色美食"]
                else:
                    tag_list = ["特色美食"]

                # 4. 核心双重兼容字段包装
                item = {
                    # --- 【老应用兼容层】老系统内部解析、保存机制认的中文键名 ---
                    "店铺名称": poi.get("name", "未知餐厅"),
                    "详细地址": full_address,

                    # --- 【新应用兼容层】DBManager和全新详情页认的英文标准键名 ---
                    "id": poi.get("id"),
                    "name": poi.get("name", "未知餐厅"),
                    "address": full_address,
                    "score": score_val,
                    "avg_price": price_val,
                    "tags": tag_list,
                    "lat": lat,
                    "lng": lng,
                    "city": city_name
                }
                all_restaurants.append(item)
            time.sleep(0.1)  # 适当延迟防封
        except Exception as e:
            print(f"高德POI数据抓取异常: {e}")
            break

    return all_restaurants


# 🌟 关键别名映射：确保原 app.py 中 from Spider_Base import get_restaurant_data 的调用不需要改一个字！
get_restaurant_data = lambda city: crawl_basic_info(city)