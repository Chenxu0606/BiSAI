import time
import random
from app import get_hotel_data, get_scenic_data, get_restaurant_data, save_to_db_task, hotels_col

# 想要预存的城市列表
POPULAR_CITIES = ["北京", "上海", "广州", "深圳", "杭州", "西安", "成都", "南京", "厦门", "青岛"]


def pre_populate_stable():
    print("=" * 50)
    print("🚀 智策旅行系统 - 数据库单线程预热 (稳健模式)")
    print("提示: 此模式模拟真人操作，速度较慢但更安全")
    print("=" * 50)

    for city in POPULAR_CITIES:
        # 1. 检查数据库是否已有数据
        if hotels_col.count_documents({"city": city}) > 0:
            print(f"⏭️  {city} 已存在，跳过。")
            continue

        print(f"\n📍 正在处理城市: {city}")

        try:
            # 2. 执行爬取 (建议在 elong_hotel.py 里确保每次爬完都 driver.quit())
            print(f"   🏨 爬取酒店数据...")
            h = get_hotel_data(city)

            print(f"   🏞️ 爬取景点数据...")
            s = get_scenic_data(city)

            print(f"   🍲 爬取美食数据...")
            f = get_restaurant_data(city)

            # 3. 入库
            save_to_db_task(city, h, s, f)
            print(f"✅ {city} 数据保存成功！")

            # 4. 关键：随机休眠 5-10 秒，防止 IP 被封
            wait_time = random.uniform(5, 10)
            print(f"😴 休息 {round(wait_time, 2)} 秒后继续下一个城市...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"❌ {city} 爬取中断: {e}")
            print("⏳ 发生错误，等待 20 秒后尝试下一个城市...")
            time.sleep(20)

    print("\n" + "=" * 50)
    print("✨ 所有城市处理完毕！")


if __name__ == '__main__':
    pre_populate_stable()