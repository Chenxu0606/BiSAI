import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify, request, render_template, redirect, session
from flask_cors import CORS
import requests
from pymongo import MongoClient

# 导入爬虫模块
try:
    from weather import get_weather_data
    from elong_hotel import get_hotel_data
    from scenic import get_scenic_data
    from Spider import get_restaurant_data
except ImportError:
    print("错误：请确保所有爬虫脚本 (.py) 都在 app.py 同级目录下")

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'zhice_secret_key_2026'
CORS(app)

# 配置区
ZHIPU_KEY = "c89c50be435440bd8ce5311423137aee.OlxNGbimdGiC1aXU"
TENCENT_KEY = "ST2BZ-PA76J-XZ6FY-XPRNP-NKKV5-QRF6Z"
GAODE_KEY = "e8c0d29bb207f4ff24097fe0f40564ec"

# 增大线程池，用于处理并发爬取和异步存库
executor = ThreadPoolExecutor(max_workers=20)

# MongoDB 连接
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['travel_db']
hotels_col = db['hotels']
scenics_col = db['scenics']
restaurants_col = db['restaurants']
status_col = db['city_status']
users_col = db['users']


# ================= 工具函数 =================

def address_to_coordinate(city, address):
    if not address: return None
    try:
        url = "https://apis.map.qq.com/ws/geocoder/v1/"
        params = {"address": f"{city}{address}", "key": TENCENT_KEY}
        res = requests.get(url, params=params, timeout=2).json()
        if res["status"] == 0:
            return {"lat": res["result"]["location"]["lat"], "lng": res["result"]["location"]["lng"]}
    except:
        pass
    return None


def save_to_db_task(city, hotels, scenics, foods):
    """后台异步解析坐标并存库"""
    # 酒店入库
    for item in hotels:
        name = item.get("名称", "").strip()
        addr = item.get("地址", "").strip()
        if name and hotels_col.count_documents({"city": city, "name": name}) == 0:
            co = address_to_coordinate(city, addr)
            hotels_col.insert_one({
                "city": city, "name": name, "address": addr,
                "lat": co['lat'] if co else None, "lng": co['lng'] if co else None
            })

    # 景点入库
    for item in scenics:
        name = item.get("景点名称", "").strip()
        addr = item.get("具体位置", "").strip()
        if name and scenics_col.count_documents({"city": city, "name": name}) == 0:
            co = address_to_coordinate(city, addr)
            scenics_col.insert_one({
                "city": city, "name": name, "address": addr,
                "lat": co['lat'] if co else None, "lng": co['lng'] if co else None
            })

    # 美食入库
    for item in foods:
        name = item.get("店铺名称", "").strip()
        addr = item.get("详细地址", "").strip()
        if name and restaurants_col.count_documents({"city": city, "name": name}) == 0:
            co = address_to_coordinate(city, addr)
            restaurants_col.insert_one({
                "city": city, "name": name, "address": addr,
                "lat": co['lat'] if co else None, "lng": co['lng'] if co else None
            })

    status_col.update_one({"city": city}, {"$set": {"last_upd": datetime.datetime.now()}}, upsert=True)


# ================= 路由区 =================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('logged_in'): return redirect('/')
        return render_template('login.html')

    data = request.json
    username, password = data.get('username'), data.get('password')
    valid_users = {'admin': 'admin123', 'user': 'user123'}

    if username in valid_users and valid_users[username] == password:
        session['logged_in'] = True
        session['username'] = username
        return jsonify({"code": 200, "msg": "登录成功"})
    return jsonify({"code": 401, "msg": "用户名或密码错误"})


@app.route('/')
def index():
    if not session.get('logged_in'): return redirect('/login')
    return render_template('index.html')


@app.route('/api/search', methods=['GET'])
def search():
    city = request.args.get('city', '').strip()
    if not city:
        return jsonify({"code": 400, "msg": "城市不能为空"})

    # --- 1. 检查数据库缓存 ---
    cache_hotels = list(hotels_col.find({"city": city}))
    cache_scenics = list(scenics_col.find({"city": city}))
    cache_foods = list(restaurants_col.find({"city": city}))

    # 如果酒店和景点都有数据，判定为命中缓存
    if len(cache_hotels) > 0 and len(cache_scenics) > 0:
        print(f"⚡ [命中缓存] 直接从数据库返回 {city} 的数据")
        result = []
        for h in cache_hotels: result.append({"type": "hotel", "name": h['name'], "info": h['address']})
        for s in cache_scenics: result.append({"type": "scenic", "name": s['name'], "info": s['address']})
        for f in cache_foods: result.append({"type": "food", "name": f['name'], "info": f['address']})
        # 补充天气（天气通常实时性强，可单独爬或从缓存拿最新一条）
        weather_data = get_weather_data(city)
        for w in weather_data: result.append({"type": "weather", "name": w.get("天气", ""), "info": w.get("日期", "")})

        return jsonify({"code": 200, "data": result})

    # --- 2. 缓存未命中，启动并发爬取 ---
    print(f"🔍 [缓存未命中] 正在真实爬取城市：{city}")
    try:
        # 使用线程池并发运行四个爬虫任务
        future_weather = executor.submit(get_weather_data, city)
        future_hotel = executor.submit(get_hotel_data, city)
        future_scenic = executor.submit(get_scenic_data, city)
        future_food = executor.submit(get_restaurant_data, city)

        # 等待结果（总耗时取决于最慢的一个）
        weather_data = future_weather.result()
        hotel_data = future_hotel.result()
        scenic_data = future_scenic.result()
        food_data = future_food.result()

        print(f"✅ 爬取完成 -> 酒店:{len(hotel_data)} 景点:{len(scenic_data)}")

        # 构造响应
        result = []
        for item in weather_data: result.append(
            {"type": "weather", "name": item.get("天气", ""), "info": item.get("日期", "")})
        for item in hotel_data: result.append(
            {"type": "hotel", "name": item.get("名称", ""), "info": item.get("地址", "")})
        for item in scenic_data: result.append(
            {"type": "scenic", "name": item.get("景点名称", "未知"), "info": item.get("具体位置", "未知")})
        for item in food_data: result.append(
            {"type": "food", "name": item.get("店铺名称", ""), "info": item.get("详细地址", "")})

        # --- 3. 异步存库 ---
        executor.submit(save_to_db_task, city, hotel_data, scenic_data, food_data)

        return jsonify({"code": 200, "data": result})

    except Exception as e:
        print(f"❌ 搜索失败: {str(e)}")
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/api/weather_detail', methods=['GET'])
def weather_detail():
    city = request.args.get('city', '上海').strip()
    try:
        w = get_weather_data(city)
        if w:
            today = w[0]
            return jsonify({
                "code": 200, "city": city, "weather": today.get("天气", "晴"),
                "temp": {"val": today.get("最高温度", "25").replace("°", ""), "color": "#3b82f6"},
                "humidity": {"val": today.get("湿度", "60").replace("%", ""), "color": "#06b6d4"},
                "wind": {"speed": today.get("风速", "3级"), "force": today.get("风向", "东风"), "color": "#8b5cf6"},
                "desc": f"{today.get('天气')} {today.get('最高温度')}/{today.get('最低温度')}",
                "aqi": {"val": "45", "level": "优", "color": "#22c55e"},
                "sun": {"rise": "06:00", "set": "18:00", "color": "#f59e0b"}
            })
    except:
        pass
    return jsonify({"code": 200, "city": city, "weather": "未知", "temp": {"val": "20"}})


@app.route('/api/strategy/map', methods=['POST'])
def get_map():
    city = request.json.get('city', '')
    markers = []
    items = list(scenics_col.find({"city": city})) + list(hotels_col.find({"city": city}))
    for i in items:
        if i.get('lat'):
            markers.append({"latitude": i['lat'], "longitude": i['lng'], "title": i['name'], "address": i['address']})

    centers = {"北京": [39.9, 116.4], "上海": [31.2, 121.4], "广州": [23.1, 113.2], "西安": [34.3, 108.9],
               "成都": [30.6, 104.0]}
    center = centers.get(city, [30.0, 110.0])
    return jsonify({"code": 200, "center": {"latitude": center[0], "longitude": center[1]}, "markers": markers})


@app.route('/api/generate', methods=['POST'])
def generate():
    d = request.json
    prompt = f"请为我规划{d.get('name')}{d.get('days')}天旅游攻略。风格：{d.get('style')}，预算：{d.get('budget')}。请以Markdown格式输出，最后标记[ROUTE_START]景点1,景点2[ROUTE_END]。"
    try:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=ZHIPU_KEY)
        resp = client.chat.completions.create(model="glm-4-fl-25041", messages=[{"role": "user", "content": prompt}])
        return jsonify({"code": 200, "content": resp.choices[0].message.content})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/clear_cache')
def clear_cache():
    status_col.delete_many({})
    hotels_col.delete_many({})
    scenics_col.delete_many({})
    restaurants_col.delete_many({})
    return "✅ 缓存已清空"


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 智策旅行系统后端优化版已启动 (已开启缓存优先逻辑)")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)