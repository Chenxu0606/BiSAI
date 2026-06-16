import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, jsonify, request, render_template, redirect, session
from flask_cors import CORS
import requests
from pymongo import MongoClient
from collections import Counter
import urllib3
import os
print("当前工作目录:", os.getcwd())
print("静态目录:", os.path.abspath("static"))

# 🤫 忽略不安全的 HTTPS 证书警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ================= 1. 绝对不动的原版导入 =================
try:
    from weather import get_weather_data
    from elong_hotel import get_hotel_data
    from scenic import get_scenic_data
    from Spider_Base import get_restaurant_data
    from database_manager import db_manager
except ImportError:
    print("错误：请确保所有爬虫脚本 (.py) 都在 app.py 同级目录下")

# ================= 2. 餐饮核心深度爬虫导入 =================
try:
    from Spider_Base import crawl_basic_info
    from Spider_Detail import fetch_poi_extras
except ImportError:
    print("提示: 美食详情爬虫模块未就绪，但不影响主系统运行")

app = Flask(
    __name__,
    static_folder="static",
    static_url_path="/static"
)
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'zhice_secret_key_2026'
CORS(app)

# ================= 3. 核心环境配置中心 (完全保留原样) =================
ZHIPU_KEY = "c89c50be435440bd8ce5311423137aee.OlxNGbimdGiC1aXU"
TENCENT_KEY = "ST2BZ-PA76J-XZ6FY-XPRNP-NKKV5-QRF6Z"
GAODE_KEY = "e8c0d29bb207f4ff24097fe0f40564ec"

# 美食高阶版密钥与安全兜底图
OLD_KEY = "e8c0d29bb207f4ff24097fe0f40564ec"
WEB_SERVICE_KEY = "519487ed40595fd66ea1c7485fcbc691"
BACKUP_IMG = "https://via.placeholder.com/600x400?text=该店暂无实地图片"

# 线程池与数据库资源分配
executor = ThreadPoolExecutor(max_workers=20)
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['travel_db']
hotels_col = db['hotels']
scenics_col = db['scenics']
restaurants_col = db['restaurants']
status_col = db['city_status']
users_col = db['users']


# ================= 4. 核心地图与落库工具函数 =================
def address_to_coordinate(city, address):
    if not address or address == "未知": return None
    try:
        url = "https://apis.map.qq.com/ws/geocoder/v1/"
        params = {"address": address, "region": city, "key": TENCENT_KEY}
        res = requests.get(url, params=params, timeout=2).json()
        if res["status"] == 0:
            return {"lat": res["result"]["location"]["lat"], "lng": res["result"]["location"]["lng"]}
    except:
        pass
    return None


def save_to_db_task(city, hotels, scenics, foods):
    for item in hotels:
        name = item.get("名称", "").strip()
        addr = item.get("地址", "").strip()
        if name and hotels_col.count_documents({"city": city, "name": name}) == 0:
            co = address_to_coordinate(city, addr)
            hotels_col.insert_one({"city": city, "name": name, "address": addr, "lat": co['lat'] if co else None,
                                   "lng": co['lng'] if co else None})
    for item in scenics:
        name = item.get("景点名称", "").strip()
        addr = item.get("具体位置", "").strip()
        if name and scenics_col.count_documents({"city": city, "name": name}) == 0:
            co = address_to_coordinate(city, addr)
            scenics_col.insert_one({"city": city, "name": name, "address": addr, "lat": co['lat'] if co else None,
                                    "lng": co['lng'] if co else None})
    for item in foods:
        name = item.get("店铺名称", "").strip()
        addr = item.get("详细地址", "").strip()
        if name and restaurants_col.count_documents({"city": city, "name": name}) == 0:
            co = address_to_coordinate(city, addr)
            restaurants_col.insert_one({"city": city, "name": name, "address": addr, "lat": co['lat'] if co else None,
                                        "lng": co['lng'] if co else None})
    status_col.update_one({"city": city}, {"$set": {"last_upd": datetime.datetime.now()}}, upsert=True)


# ================= 5. 系统安全验证与控制台大屏路由 =================
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
    if not city: return jsonify({"code": 400, "msg": "城市不能为空"})

    cache_hotels = list(hotels_col.find({"city": city}))
    cache_scenics = list(scenics_col.find({"city": city}))
    cache_foods = list(restaurants_col.find({"city": city}))

    if len(cache_hotels) > 0 and len(cache_scenics) > 0:
        result = []
        for h in cache_hotels: result.append(
            {"type": "hotel", "name": h['name'], "info": h['address'], "lat": h.get('lat'), "lng": h.get('lng')})
        for s in cache_scenics: result.append(
            {"type": "scenic", "name": s['name'], "info": s['address'], "lat": s.get('lat'), "lng": s.get('lng')})
        for f in cache_foods: result.append(
            {"type": "food", "name": f['name'], "info": f['address'], "lat": f.get('lat'), "lng": f.get('lng')})
        try:
            weather_data = get_weather_data(city)
            for w in weather_data: result.append(
                {"type": "weather", "name": w.get("天气", ""), "info": w.get("日期", "")})
        except:
            pass
        return jsonify({"code": 200, "data": result})

    try:
        future_weather = executor.submit(get_weather_data, city)
        future_hotel = executor.submit(get_hotel_data, city)
        future_scenic = executor.submit(get_scenic_data, city)
        future_food = executor.submit(get_restaurant_data, city)

        weather_data = future_weather.result() or []
        hotel_data = future_hotel.result() or []
        scenic_data = future_scenic.result() or []
        food_data = future_food.result() or []

        result = []
        for item in weather_data: result.append(
            {"type": "weather", "name": item.get("天气", ""), "info": item.get("日期", "")})
        for item in hotel_data:
            addr = item.get("地址", "")
            co = address_to_coordinate(city, addr)
            result.append(
                {"type": "hotel", "name": item.get("名称", ""), "info": addr, "lat": co['lat'] if co else None,
                 "lng": co['lng'] if co else None})
        for item in scenic_data:
            addr = item.get("具体位置", "")
            co = address_to_coordinate(city, addr)
            result.append(
                {"type": "scenic", "name": item.get("景点名称", "未知"), "info": addr, "lat": co['lat'] if co else None,
                 "lng": co['lng'] if co else None})
        for item in food_data:
            addr = item.get("详细地址", "")
            co = address_to_coordinate(city, addr)
            result.append(
                {"type": "food", "name": item.get("店铺名称", ""), "info": addr, "lat": co['lat'] if co else None,
                 "lng": co['lng'] if co else None})

        executor.submit(save_to_db_task, city, hotel_data, scenic_data, food_data)
        db_manager.save_restaurants(city, food_data)
        return jsonify({"code": 200, "data": result})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)})


@app.route('/api/weather_detail', methods=['GET'])
def weather_detail():
    city = request.args.get('city', '上海').strip()
    try:
        w = get_weather_data(city)
        if w:
            today = w[0]
            return jsonify({"code": 200, "city": city, "weather": today.get("天气", "晴"),
                            "temp": {"val": today.get("最高温度", "25").replace("°", ""), "color": "#3b82f6"},
                            "humidity": {"val": today.get("湿度", "60").replace("%", ""), "color": "#06b6d4"},
                            "wind": {"speed": today.get("风速", "3级"), "force": today.get("风向", "东风"),
                                     "color": "#8b5cf6"},
                            "desc": f"{today.get('天气')} {today.get('最高温度')}/{today.get('最低温度')}",
                            "aqi": {"val": "45", "level": "优", "color": "#22c55e"},
                            "sun": {"rise": "06:00", "set": "18:00", "color": "#f59e0b"}})
    except:
        pass
    return jsonify({"code": 200, "city": city, "weather": "未知", "temp": {"val": "20"}})


@app.route('/api/generate', methods=['POST'])
def generate():
    d = request.json
    user_demand = f"请为我规划{d.get('name')}{d.get('days')}天旅游攻略。风格：{d.get('style')}，预算：{d.get('budget')}。请以Markdown格式输出，最后标记[ROUTE_START]景点1,景点2[ROUTE_END]。"
    try:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=ZHIPU_KEY)
        response = client.chat.completions.create(model="glm-4-flash",
                                                  messages=[{"role": "system", "content": "你是一个专业的旅游规划专家"},
                                                            {"role": "user", "content": user_demand}], top_p=0.7,
                                                  temperature=0.9)
        return jsonify({"code": 200, "answer": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"code": 500, "msg": f"AI 请求失败: {str(e)}"})


@app.route('/clear_cache')
def clear_cache():
    db.hotels.delete_many({})
    db.scenics.delete_many({})
    db.restaurants.delete_many({})
    return "✅ 缓存已清空"


# ================= 6. 餐饮板块前台视图路由 =================
@app.route('/food/search')
def food_search(): return render_template('food_search.html')


@app.route('/food/standby')
def food_standby(): return render_template('food_standby.html', city=request.args.get('city', '长沙'))


@app.route('/food/food_list')
def food_list(): return render_template('food_list.html', city=request.args.get('city', '长沙'))


@app.route('/food/detail')
def food_detail(): return render_template('food_detail.html', name=request.args.get('name', ''))


# ================= 7. 追加的餐饮专属后端大数据清洗接口 =================
@app.route('/api/food/search_keywords')
def api_keywords():
    city = request.args.get('city', '长沙')
    data = db_manager.find_by_city(city)

    if not data or (len(data) > 0 and 'images' not in data[0]):
        print(f"🚀 [智策系统] 正在进行深度基因缝合: {city}")
        raw_list = []
        try:
            raw_list = crawl_basic_info(city, OLD_KEY)
        except Exception as e:
            print(f"⚠️ 基础爬虫突发异常: {e}")

        final_data = []
        if raw_list:
            for item in raw_list[:15]:
                p_id = item.get('id')
                try:
                    imgs, loc = fetch_poi_extras(p_id, WEB_SERVICE_KEY)
                except Exception as e:
                    imgs, loc = [], None
                item['images'] = imgs if imgs else []
                if loc: item['location'] = loc
                final_data.append(item)

        if final_data:
            db_manager.save_restaurants(city, final_data)
            data = final_data

    if data:
        # ✨ 使用 .get() 方法，如果某家店没爬到分类，就默认给个“特色美食”的标签，绝不报错卡死！
        all_types = [i.get('type', '特色美食') for i in data]
        top_types = Counter(all_types).most_common(12)
        keywords = [[tag, 18 if idx < 3 else 14] for idx, (tag, count) in enumerate(top_types)]
        return jsonify({"code": 200, "keywords": keywords})
    return jsonify({"code": 200, "keywords": []})


# 🌟 双路由兼容：智能阶梯图文渲染分流中心
@app.route('/api/food/item_detail')
@app.route('/api/food/single_detail')
def api_item_detail():
    name = request.args.get('name')
    detail = db_manager.find_one_restaurant(name)

    if detail:
        img_pool = detail.get('images', [])
        real_imgs = [img for img in img_pool if img and "placeholder.com" not in img]
        img_count = len(real_imgs)

        print(f"[智能分流] 【{name}】 数据库实际高清图数: {img_count}张")

        # 🚀 4/3/2/1 级精准图文阶梯错开布局核心算法
        if img_count >= 4:
            detail['images'] = real_imgs[0:2]
            detail['dishes'] = [
                {"name": "到店特推·招牌风味菜", "image": real_imgs[2]},
                {"name": "特色风味·厨师长推荐", "image": real_imgs[3]}
            ]
        elif img_count == 3:
            detail['images'] = [real_imgs[0]]
            detail['dishes'] = [
                {"name": "到店必尝", "image": real_imgs[1]},
                {"name": "口碑特推", "image": real_imgs[2]}
            ]
        elif img_count == 2:
            detail['images'] = [real_imgs[0]]
            detail['dishes'] = [
                {"name": "独家珍藏", "image": real_imgs[1]}
            ]
        else:
            detail['dishes'] = []
            detail['images'] = real_imgs if img_count == 1 else [BACKUP_IMG, BACKUP_IMG]

        return jsonify({"code": 200, "data": detail})

    return jsonify({"code": 404})


@app.route('/api/food/list_data')
def api_food_list():
    results = db_manager.find_by_city(request.args.get('city', '长沙'))
    formatted_list = []
    for item in results:
        formatted_list.append({
            "name": item.get("name", "未探测到店名"),
            "score": item.get("score", "4.5"),
            "type": item.get("type", "美食"),
            "address": item.get("address", "暂无详细地址")
        })
    return jsonify({"code": 200, "data": formatted_list})



@app.route("/attraction_center")
def attraction_center():
    return render_template("attraction_center.html")

# ================= 8. AI 路由大联盟 =================
@app.route('/ai_guide')
def ai_guide():
    return render_template('AIchat.html')



@app.route('/api/ai/generate-guide', methods=['POST'])
def generate_guide():
    data = request.json or {}

    # 1. 核心修复：先用 str() 强转，再用 or 兜底，彻底解决数字/None 触发 .strip() 崩溃的问题
    departure = str(data.get('departure') or '未知').strip()
    destination = str(data.get('destination') or '未知').strip()
    start_date = str(data.get('startDate') or '未定').strip()
    end_date = str(data.get('endDate') or '未定').strip()
    people = data.get('people', 1)
    budget = str(data.get('budget') or '未定').strip()
    travel_type = str(data.get('travelType') or '综合体验').strip()
    preference = str(data.get('preference') or '无特殊偏好').strip()
    remark = str(data.get('remark') or '无').strip()

    # 2. 组装强力提示词（Prompt），封死 AI 反问的退路
    prompt_content = f"""
    请为我规划一次深度旅行，以下是我的全部已知需求。
    【绝对禁止】向我反问诸如“目的地是哪”、“预算多少”等问题！请直接根据已知信息生成 Markdown 格式的完整行程攻略：

    - 出发地：{departure}
    - 目的地：{destination}
    - 日期：{start_date} 至 {end_date}
    - 人数：{people}
    - 预算：{budget}
    - 出行风格：{travel_type}
    - 个性偏好：{preference}
    - 备注信息：{remark}

    请输出结构清晰的攻略，必须包含：目的地亮点、每日精确路线、住宿建议和特色美食推荐。
    """

    try:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=ZHIPU_KEY)
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system",
                 "content": "你是一个高效直接的旅行规划专家智小策，绝不向用户索要额外信息，直接给出最佳方案。"},
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.7
        )
        return jsonify({"content": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"content": f"生成失败: {str(e)}"}), 500


@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.json or {}
    question = data.get('question')
    travel_info = data.get('travelInfo', {})  # 获取前端传来的背景信息

    if not question:
        return jsonify({"answer": "你说什么？我没听清。"})

    # 提取聊天时的背景城市
    current_dest = travel_info.get('destination', '未知目的地')

    try:
        from zhipuai import ZhipuAI
        client = ZhipuAI(api_key=ZHIPU_KEY)

        # 让 AI 带着上下文陪聊，就不会出现前言不搭后语的情况
        system_msg = f"你叫智小策。用户目前正在规划去【{current_dest}】的旅行，请结合这个背景，简短、专业、友善地解答用户的问题。"

        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": question}
            ]
        )
        return jsonify({"answer": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"answer": f"抱歉，我短路了：{str(e)}"})


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route('/city_detail')
def city_detail():
    return render_template('city_detail.html')


if __name__ == '__main__':
    # 🚀 使用 use_reloader=False 彻底杜绝主进程二次启动，完美护航多线程爬虫与高并发大屏
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)