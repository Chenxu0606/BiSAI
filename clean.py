from pymongo import MongoClient


def clear_all_data():
    try:
        # 1. 连接数据库
        client = MongoClient('mongodb://localhost:27017/')
        db = client['travel_db']

        # 2. 定义需要清理的集合
        collections = ['hotels', 'scenics', 'restaurants', 'city_status']

        print("⚠️ 正在准备清空数据库...")

        for col_name in collections:
            count = db[col_name].count_documents({})
            db[col_name].delete_many({})
            print(f"✅ 已清空集合: [{col_name}]，共删除 {count} 条数据")

        print("=" * 30)
        print("🎉 智策旅行系统数据已全部重置！")

    except Exception as e:
        print(f"❌ 清理失败: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    confirm = input("此操作将删除所有爬取的缓存数据，确认执行吗？(y/n): ")
    if confirm.lower() == 'y':
        clear_all_data()
    else:
        print("操作已取消。")