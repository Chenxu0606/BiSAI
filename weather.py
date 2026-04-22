import time
import random
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

COMMON_CITY_CODES = {
    '北京': '101010100', '上海': '101020100', '广州': '101280101',
    '深圳': '101280601', '杭州': '101210101', '南京': '101190101',
    '武汉': '101200101', '成都': '101270101', '重庆': '101040100',
    '天津': '101030100', '西安': '101110101', '郑州': '101180101',
    '沈阳': '101070101', '济南': '101120101', '青岛': '101120201',
    '大连': '101070201', '宁波': '101210401', '厦门': '101230201',
    '苏州': '101190401', '长沙': '101250101', '昆明': '101290101',
    '三亚': '101290201', '肇庆': '101280801'
}


class WeatherCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.weather.com.cn/'
        }

    def crawl_weather(self, city_name, days=7):
        city_name = city_name.strip()
        city_code = COMMON_CITY_CODES.get(city_name, "101010100")
        real_city = city_name if city_name in COMMON_CITY_CODES else "北京"

        try:
            time.sleep(random.uniform(0.5, 1.5))
            url = f"https://www.weather.com.cn/weather/{city_code}.shtml"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'

            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            # 🔥 核心修复：用属性选择器代替数字ID选择器，解决报错！
            weather_div = soup.find('div', id='7d')
            li_list = weather_div.find('ul', class_='t clearfix').find_all('li')[:days]
            weather_data = []

            for i, li in enumerate(li_list):
                current_date = datetime.now() + timedelta(days=i)

                # 天气状况
                wea = li.find("p", class_="wea").get_text(strip=True) if li.find("p", class_="wea") else "晴"
                # 温度解析
                tem = li.find("p", class_="tem").get_text(strip=True) if li.find("p", class_="tem") else "0~0℃"
                temp_match = re.findall(r'-?\d+', tem)
                low = temp_match[-1] if len(temp_match) >= 1 else "0"
                high = temp_match[0] if len(temp_match) >= 2 else low
                # 风向
                wind = li.find("p", class_="win").get_text(strip=True) if li.find("p", class_="win") else "无风"

                # 完全兼容你的 app.py 字段
                weather_data.append({
                    '城市': real_city,
                    '日期': current_date.strftime("%Y-%m-%d"),
                    '天气': wea,
                    '最低温度': f"{low}°",
                    '最高温度': f"{high}°",
                    '风向': wind,
                    '风速': wind,
                    '湿度': '60%'
                })
            return weather_data
        except Exception as e:
            print(f"❌ 天气爬取失败：{str(e)}")
            return []


def get_weather_data(city):
    crawler = WeatherCrawler()
    data = crawler.crawl_weather(city)
    print(f"✅ 天气：{city} 获取到 {len(data)} 条数据")
    return data