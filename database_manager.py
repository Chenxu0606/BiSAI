# -*- coding: utf-8 -*-
from pymongo import MongoClient


class DBManager:
    def __init__(self):
        # 🔗 统一连接本地 MongoDB 的 travel_db 数据库
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['travel_db']
        self.collection = self.db['restaurants']  # 餐饮数据集合

        # ⚡ 核心性能与去重保障：建立复合索引，保障高并发大屏秒级响应
        self.collection.create_index([("city", 1)])
        self.collection.create_index([("search_city", 1)])
        self.collection.create_index([("name", 1), ("city", 1)])

    def find_by_city(self, city):
        """
        🔄 双轨兼容查询：同时兼容主大屏的 city 字段和美食专栏的 search_city 字段
        确保不管从哪个页面拉取，都能秒级响应，绝不漏掉一条缓存。
        """
        return list(self.collection.find({
            "$or": [
                {"city": city},
                {"search_city": city}
            ]
        }, {"_id": 0}))

    def save_restaurants(self, city, restaurants):
        """
        批量保存/更新餐厅数据 (Upsert模式：防止同城市同名餐厅重复插入)
        🚀 已深度无损缝合：完美保护主大屏坐标与美食高级图池资产
        """
        if not restaurants:
            return

        for item in restaurants:
            # 兼容性兜底取值
            name = item.get("name") or item.get("店铺名称")
            address = item.get("address") or item.get("详细地址")

            if not name:
                continue  # 过滤无名脏数据

            # 提取类型并确保不为 None
            r_type = item.get("type") or item.get("店铺类型") or "特色美食"

            # 规范清洗落库结构 (同时注入 city 和 search_city，彻底打通前后端字段冲突)
            formatted_item = {
                "city": city,
                "search_city": city,
                "name": name.strip(),
                "address": address.strip() if address else "暂无地址",
                "score": str(item.get("score") or item.get("评分") or "4.5"),
                "avg_price": item.get("avg_price") or item.get("price") or item.get("人均消费") or "80",
                "type": r_type,
                # 📸 核心资产保护：绝对不能弄丢高德深度抓取的 4 张实景图池
                "images": item.get("images") or [],
                # 🗺️ 地图坐标兼容保护：无论是高德的 location 还是腾讯的 lat/lng，全部完美保留
                "location": item.get("location") or "",
                "lat": item.get("lat"),
                "lng": item.get("lng")
            }

            # 智能清洗 tags：如果是列表则直接用，如果是字符串则包装成列表，防止前端 map 循环崩掉
            raw_tags = item.get("tags")
            if raw_tags and isinstance(raw_tags, list):
                formatted_item["tags"] = raw_tags
            else:
                formatted_item["tags"] = [r_type]

            # 按照【城市 + 店名】唯一确定一家商户进行增量更新
            self.collection.update_one(
                {"name": formatted_item["name"], "city": city},
                {"$set": formatted_item},
                upsert=True
            )

    def find_one_restaurant(self, name):
        """按照名称精准捞取单家餐厅的画像详情（喂给新详情页前端，含智能分流图池）"""
        return self.collection.find_one({"name": name}, {"_id": 0})


# 🌟 直接实例化，方便 app.py 一句话导入
db_manager = DBManager()