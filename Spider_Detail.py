import requests
import urllib3

# 🤫 关闭本地代理或证书引发的 HTTPS 警告，防止控制台爆 SSL 错误
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_poi_extras(poi_id, web_service_key):
    """
    深度爬虫：使用 Web 服务 API
    🎯 核心策略：精准抓取最多 4 张实景图片，不多不少，拒绝虚拟图
    """
    url = "https://restapi.amap.com/v3/place/detail"
    params = {
        "id": poi_id,
        "key": web_service_key
    }
    try:
        # 🛡️ 加入 verify=False，彻底免疫高德因高频请求强切 SSL 造成的 [SSL: UNEXPECTED_EOF_WHILE_READING] 报错
        res = requests.get(url, params=params, verify=False, timeout=5)
        data = res.json()

        if data.get('status') == '1' and data.get('pois'):
            poi_detail = data['pois'][0]

            # 📸 提取高德原生的实景图片列表
            photos = poi_detail.get('photos', [])

            # 🌟 核心破封印：提取所有可用的真实图片 URL
            all_urls = [p['url'] for p in photos if p.get('url')]

            # 🎯 严格控制：我们最多只需要 4 张图（2张留给轮播，2张留给推荐菜）
            images = all_urls[:4]

            # 📍 提取地理位置坐标
            location = poi_detail.get('location', "")

            return images, location

    except Exception as e:
        print(f"⚠️ 深度抓取异常 [ID:{poi_id}]: {e}")

    return [], ""