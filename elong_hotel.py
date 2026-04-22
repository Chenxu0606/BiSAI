import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List, Dict, Any, Optional, Callable


class ElongHotelAutoScraper:

    def __init__(self, max_workers=3, headless=True, max_hotels_per_city=20, chrome_driver_path=None):
        if chrome_driver_path is None:
            chrome_driver_path = r"D:\A.BiSAI\chromedriver.exe"

        self.service = Service(chrome_driver_path)
        self.max_workers = max_workers
        self.headless = headless
        self.max_hotels_per_city = max_hotels_per_city
        self.lock = threading.Lock()

        self.city_list = [
            "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安",
            "南京", "苏州", "重庆", "长沙", "青岛", "厦门", "三亚", "昆明"
        ]

        self.city_pinyin_map = self._init_city_pinyin_map()

        self.city_id_map = self._fetch_all_city_ids()

        self.cookie_string = """Esid=a474bdfe-85af-4444-9307-fb7aa957a9cd; firsttime=1773794197024; H5CookieId=fae64091-e4fa-4b45-a2f1-e06a04e64f03; H5Channel=mnoreferseo%2CSEO; CookieGuid=d5e79dba-68a423-8d01-93a043fa2720; SessionGuid=5f353aa7-32eb-4d9f-b427-2cc0c0c8c5f9; fv=pcweb; SessionToken=b26970cd-cd2c-44d8-ab26-dca432f3fced622; Lgid=LRpRtrsC3gsExwGXhEk%2FlpaR3waA7McUH7SGryL5%2FSGKEko0r3PI5Xvy93KGCYWb0ry6DsjSO8GE1NED6C6eVqZA656WIvx6rztMIPaKGrsKNMgmSeKMfPFgRD%2BmvI9fwXoNNF9YBKpXtPqGqeIk1A%3D%3D; tcUser=%7B%22AccessToken%22%3A%22EA52231F532BFAECF2BE91AE57CBFE3C%22%2C%22MemberId%22%3A%229977faa51a6af6bb9f1a41ab6e22d2d8%22%7D; x-user-dun=x7NxxxxxIa2sH5txI8qH8eWEulPbf7CIx7CCI7QqhqCOWaKFa5aEz5VQaER0A%2FsIOwAm6IjIxxKXRdJWCLPr3U1m9P%2B0kN1eUwM017lQfzlLf41S0ECW%2BlzJ9POJ87ox2rorqQpNeyCJT5o6az%2BPss%2BUyPxudIPIzaMxn3AGKnuYzOHoOe4962xfhHQsMlIZhVrSmlilhGQ4yJkfd9k4EWrlBCHSOsU9b9k965IXoLv4fDXWaz5argHUApPahHLHej%2BaZMN03l693m%2BrRFLqFZ8jmZ%2FXUQtYxA%2FXEVHQ4zVKWUunxA%2FqrfJxh1PPr58RHmp3erZExpxReSmdYZPrOIuwGBNr68fdEkwE6RSrY%2FOG5MuG2hREsvdRFXNEs4gRY5NEs4gdY5NrOIuwGBNr68SUzB9rfw1IimCaINuGxAxae5JnhsVGrfHfyh8YI5jiI7c%3D; JSESSIONID=33C6BFABDBA47FE0DF31C0C8B11D7518; lasttime=1774248964117"""

        print("=" * 60)
        print("     艺龙酒店自动爬虫      ")
        print(f"     并发线程数: {self.max_workers}")
        print(f"     无头模式: {self.headless}")
        print(f"     默认每城市爬取: {self.max_hotels_per_city} 条")
        print(f"     已加载 {len(self.city_id_map)} 个城市ID")
        print("=" * 60)

    def _init_city_pinyin_map(self):
        return {
            "北京": "beijing", "上海": "shanghai", "天津": "tianjin", "重庆": "chongqing",
            "广州": "guangzhou", "深圳": "shenzhen", "杭州": "hangzhou", "成都": "chengdu",
            "武汉": "wuhan", "西安": "xian", "南京": "nanjing", "苏州": "suzhou",
            "长沙": "changsha", "青岛": "qingdao", "厦门": "xiamen", "三亚": "sanya",
            "昆明": "kunming", "大连": "dalian", "宁波": "ningbo", "无锡": "wuxi",
            "佛山": "foshan", "东莞": "dongguan", "郑州": "zhengzhou", "济南": "jinan",
        }

    def _fetch_all_city_ids(self) -> Dict[str, str]:
        city_id_map = {}

        try:
            print("正在从艺龙API获取城市ID...")
            url = "https://www.elong.com/tapi/gethotelcitysbyletter"
            headers = {
                "accept": "application/json, text/plain, */*",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
                "appfrom": "15",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0 Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if "data" in data:
                for city in data["data"]:
                    city_name = city.get("cityName")
                    city_id = city.get("cityId")
                    if city_name and city_id:
                        city_id_map[city_name] = city_id

                print(f"✓ 成功从API获取 {len(city_id_map)} 个城市ID")
            else:
                print("⚠️ API返回数据格式异常，使用备用映射")
                city_id_map = self._get_fallback_city_map()

        except Exception as e:
            print(f"⚠️ 获取城市ID失败: {e}")
            print("   使用备用城市ID映射")
            city_id_map = self._get_fallback_city_map()

        return city_id_map

    def _get_fallback_city_map(self) -> Dict[str, str]:
        return {
            "北京": "0101", "上海": "0201", "广州": "0301", "深圳": "0401",
            "杭州": "0501", "成都": "2301", "武汉": "1801", "西安": "2701",
            "南京": "1101", "苏州": "1102", "重庆": "0401", "长沙": "1901",
            "青岛": "1601", "厦门": "1401", "三亚": "2201", "昆明": "2501",
        }

    def _create_driver(self):
        options = Options()

        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')

        if self.headless:
            options.add_argument('--headless=new')

        options.add_argument('--log-level=3')
        options.add_argument('--silent')
        options.add_argument('--remote-debugging-port=9222')

        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0 Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')

        return webdriver.Chrome(service=self.service, options=options)

    def _get_city_url(self, city_name: str) -> str:
        city_name = city_name.strip()

        if city_name in self.city_id_map:
            city_id = self.city_id_map[city_name]
            today = datetime.now().strftime('%Y-%m-%d')
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            url = f"https://www.elong.com/hotel/hotellist?city={city_id}&inDate={today}&outDate={tomorrow}"
            return url

        city_pinyin = self._get_city_pinyin(city_name)
        url = f"http://hotel.elong.com/{city_pinyin}/"
        return url

    def _parse_cookie_string(self, cookie_string: str) -> List[Dict[str, str]]:
        cookies = []
        for item in cookie_string.split(';'):
            item = item.strip()
            if not item or '=' not in item:
                continue
            name, value = item.split('=', 1)
            cookies.append({
                'name': name.strip(),
                'value': value.strip(),
                'domain': '.elong.com',
                'path': '/',
            })
        return cookies

    def _apply_cookies(self, driver):
        try:
            driver.get("https://www.elong.com")
            time.sleep(1)

            cookies = self._parse_cookie_string(self.cookie_string)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except:
                    pass

            driver.refresh()
            time.sleep(1)
            return True
        except:
            return False

    def _get_city_pinyin(self, city_name: str) -> str:
        city_name = city_name.strip()
        if city_name in self.city_pinyin_map:
            return self.city_pinyin_map[city_name]

        for known_city, pinyin in self.city_pinyin_map.items():
            if city_name in known_city or known_city in city_name:
                return pinyin

        return city_name.lower()

    def _verify_city_page(self, driver, expected_city: str) -> bool:
        try:
            page_title = driver.title
            if expected_city != "北京" and "北京" in page_title and expected_city not in page_title:
                page_source = driver.page_source[:5000]
                if expected_city not in page_source:
                    return False
            return True
        except:
            return True

    def scrape_city(self, city: str, max_hotels: Optional[int] = None, callback: Optional[Callable] = None) -> Dict[
        str, Any]:
        if max_hotels is None:
            max_hotels = self.max_hotels_per_city

        try:
            url = self._get_city_url(city)
            print(f"正在访问: {url}")

            driver = self._create_driver()

            try:
                self._apply_cookies(driver)

                driver.get(url)
                time.sleep(5)

                if not self._verify_city_page(driver, city):
                    print(f"  ❌ 城市验证失败，可能跳转到了错误页面")
                    return {
                        'city': city,
                        'success': False,
                        'error': '页面跳转错误',
                        'data': [],
                        'count': 0
                    }

                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR,
                             "a[href*='/hotel/'], .hotel-item, [class*='hotel'], div[class*='list-item']"))
                    )
                    print("页面加载完成，开始提取数据...")
                except:
                    print("等待超时，尝试继续...")

                last_height = driver.execute_script("return document.body.scrollHeight")
                for i in range(5):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                hotels = self._extract_hotels_improved(driver, city, max_hotels, callback)

                return {
                    'city': city,
                    'success': True,
                    'data': hotels,
                    'count': len(hotels)
                }

            finally:
                driver.quit()

        except Exception as e:
            print(f"错误: {e}")
            return {
                'city': city,
                'success': False,
                'error': str(e),
                'data': [],
                'count': 0
            }

    def _extract_hotels_improved(self, driver, city: str, max_hotels: int = 20, callback: Optional[Callable] = None) -> \
            List[Dict[str, Any]]:
        hotels = []

        hotel_cards = []

        selectors = [
            "div[class*='hotel-item']",
            "div[class*='hotel-card']",
            "div[class*='list-item']",
            "div[data-key*='hotel']",
            "li[class*='hotel']"
        ]

        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements and len(elements) > 0:
                hotel_cards = elements
                print(f"使用选择器: {selector}, 找到 {len(hotel_cards)} 个酒店卡片")
                break

        if not hotel_cards:
            hotel_cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/hotel/']")
            print(f"使用链接选择器，找到 {len(hotel_cards)} 个链接")

        print(f"总共找到 {len(hotel_cards)} 个酒店卡片，目标爬取 {max_hotels} 条")

        processed = set()
        hotel_count = 0

        for card in hotel_cards:
            if hotel_count >= max_hotels:
                break

            try:
                card_text = card.text
                if not card_text or len(card_text) < 50:
                    continue

                card_hash = hash(card_text[:200])
                if card_hash in processed:
                    continue
                processed.add(card_hash)

                hotel_info = self._parse_hotel_from_text_enhanced(card_text)

                if hotel_info.get('酒店名称') and len(hotel_info['酒店名称']) > 2:
                    hotel_info['城市'] = city
                    hotels.append(hotel_info)
                    hotel_count += 1

                    address_info = f" - 地址: {hotel_info['地址']}" if hotel_info.get('地址') else ""
                    print(f"  ✓ {hotel_count}. {hotel_info['酒店名称']} - {hotel_info['价格']}{address_info}")

                    if callback:
                        callback(hotel_info)

            except Exception as e:
                continue

        return hotels

    def _parse_hotel_from_text_enhanced(self, text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        hotel_info = {
            '酒店名称': '',
            '类型': '',
            '评分': '',
            '点评数': '',
            '地址': '',
            '特色': '',
            '价格': '暂无',
            '收藏数': '',
            '抓取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        address_keywords = [
            '广场', '中心', '区', '路', '街', '巷', '弄', '大道',
            '附近', '地区', '商圈', '商务区', '步行街', '美食街', '夜市',
            '景区', '公园', '博物馆', '火车站', '高铁站', '汽车站', '机场',
            '地铁站', '商业街', '文化街', '古镇', '度假区', '开发区',
            '产业园', '科技园', '大学城', 'CBD', '商务中心', '市场'
        ]

        exclude_words = [
            '免费停车', '洗衣服务', '健身中心', '接机服务', '充电桩',
            '早餐', '亲子房', '会议厅', '行李寄存', '影音房', '浴缸',
            '棋牌房', '智能客控', '干衣机', '家庭房', '机器人服务',
            '无烟楼层', '新开业', '停车场', '游泳池', '餐厅', '送餐服务'
        ]

        for i, line in enumerate(lines):
            if any(kw in line for kw in ['酒店', '宾馆', '公寓', '民宿', '客栈', '山庄', '度假村']) and len(line) < 50:
                if not line.startswith('"') and not line.startswith('“'):
                    if not hotel_info['酒店名称']:
                        hotel_info['酒店名称'] = line
                        continue

            type_keywords = ['经济', '舒适', '高档', '豪华', '五星', '四星', '三星', '精品', '奢华']
            for kw in type_keywords:
                if kw in line and len(line) < 20 and not line.startswith('"'):
                    if not hotel_info['类型']:
                        hotel_info['类型'] = line
                        break

            if not hotel_info['评分']:
                score_match = re.search(r'^(\d+\.\d+)$', line) or re.search(r'(\d+\.\d+)\s*分', line)
                if score_match:
                    hotel_info['评分'] = score_match.group(1) + '分'
                    continue

            if '条点评' in line and not hotel_info['点评数']:
                comment_match = re.search(r'(\d+)\s*条点评', line)
                if comment_match:
                    hotel_info['点评数'] = comment_match.group(1) + '条点评'
                    continue

            if not hotel_info['地址']:
                if line.startswith('"') or line.startswith('“'):
                    continue

                if any(ex in line for ex in exclude_words):
                    continue

                is_address = False
                for kw in address_keywords:
                    if kw in line:
                        is_address = True
                        break

                if is_address and 3 < len(line) < 60:
                    if any(word in line for word in ['靠近', '位于', '地处']):
                        hotel_info['地址'] = line
                        break
                    elif re.search(r'\d+号|\d+-\d+号|第\d+号', line):
                        hotel_info['地址'] = line
                        break
                    elif len(line) < 40 and not any(ex in line for ex in ['赞!', '抢!', '推荐']):
                        hotel_info['地址'] = line
                        break

        if not hotel_info['地址']:
            for line in lines:
                if any(word in line for word in ['靠近', '位于', '地处']) and len(line) < 50:
                    if not any(ex in line for ex in exclude_words):
                        hotel_info['地址'] = line
                        break

        for line in lines:
            if ('￥' in line or '¥' in line) and hotel_info['价格'] == '暂无':
                price_match = re.search(r'[￥¥](\d+)', line)
                if price_match:
                    price = int(price_match.group(1))
                    if price > 10:
                        hotel_info['价格'] = f"¥{price}"
                        break

        feature_keywords = [
            '免费停车', '洗衣服务', '健身中心', '影音房', '智能客控',
            '干衣机', '充电桩', '棋牌房', '浴缸', '近地铁', '家庭房',
            '行李寄存', '亲子房', '机器人服务', '会议厅', '无烟楼层',
            '接机服务', '新开业', '停车场', '游泳池', '餐厅', '送餐服务',
            '早餐', '茶室', '咖啡厅', '棋牌室', '商务中心', '24小时前台'
        ]

        features = []
        for line in lines:
            for f in feature_keywords:
                if f in line and not line.startswith('"'):
                    if line not in features and len(line) < 30:
                        features.append(line)
                        break

        hotel_info['特色'] = ' | '.join(features[:8]) if features else ''

        for line in lines:
            if '人收藏' in line and not hotel_info['收藏数']:
                match = re.search(r'(\d+)\+?人收藏', line)
                if match:
                    hotel_info['收藏数'] = match.group(1) + '人收藏'
                    break

        if not hotel_info['酒店名称'] and lines:
            first_line = lines[0]
            if not first_line.startswith('"') and not first_line.startswith('“'):
                if any(kw in first_line for kw in ['酒店', '宾馆', '公寓', '民宿']):
                    hotel_info['酒店名称'] = first_line

        return hotel_info

    def scrape_multiple_cities(self, city_list: Optional[List[str]] = None, max_hotels_per_city: Optional[int] = None,
                               callback: Optional[Callable] = None) -> Dict[str, Any]:
        if city_list is None:
            city_list = self.city_list

        if max_hotels_per_city is None:
            max_hotels_per_city = self.max_hotels_per_city

        print(f"\n🚀 开始批量爬取 {len(city_list)} 个城市，每个城市目标 {max_hotels_per_city} 条")
        print("-" * 60)

        all_results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_city = {executor.submit(self.scrape_city, city, max_hotels_per_city, callback): city
                              for city in city_list}

            for future in as_completed(future_to_city):
                city = future_to_city[future]
                try:
                    result = future.result()
                    all_results[city] = result

                    if result['success']:
                        print(f"✓ {city}: 成功抓取 {result['count']}/{max_hotels_per_city} 家酒店")
                        if result['data']:
                            for i, hotel in enumerate(result['data'][:3], 1):
                                address_show = f" - {hotel['地址']}" if hotel.get('地址') else ""
                                print(f"   {i}. {hotel['酒店名称']}{address_show}")
                    else:
                        print(f"✗ {city}: 抓取失败")

                except Exception as e:
                    print(f"✗ {city}: 异常 - {str(e)}")
                    all_results[city] = {
                        'city': city,
                        'success': False,
                        'error': str(e),
                        'data': [],
                        'count': 0
                    }

        self._save_all_data(all_results)
        self._print_statistics(all_results, max_hotels_per_city)

        return all_results

    def _save_all_data(self, all_results: Dict[str, Any], output_dir: str = "."):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        os.makedirs(output_dir, exist_ok=True)

        full_filename = os.path.join(output_dir, f"elong_hotels_full_{timestamp}.json")
        with open(full_filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        summary = []
        for city, result in all_results.items():
            if result['success']:
                for hotel in result['data']:
                    summary.append(hotel)

        summary_filename = os.path.join(output_dir, f"elong_hotels_summary_{timestamp}.json")
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        csv_filename = os.path.join(output_dir, f"elong_hotels_{timestamp}.csv")
        with open(csv_filename, 'w', encoding='utf-8-sig') as f:
            headers = ['城市', '酒店名称', '类型', '评分', '点评数', '地址', '特色', '价格', '收藏数', '抓取时间']
            f.write(','.join(headers) + '\n')

            for hotel in summary:
                row = [
                    hotel.get('城市', ''),
                    hotel.get('酒店名称', '').replace(',', '，'),
                    hotel.get('类型', '').replace(',', '，'),
                    hotel.get('评分', ''),
                    hotel.get('点评数', ''),
                    hotel.get('地址', '').replace(',', '，'),
                    hotel.get('特色', '').replace(',', '，'),
                    hotel.get('价格', ''),
                    hotel.get('收藏数', ''),
                    hotel.get('抓取时间', '')
                ]
                f.write(','.join(row) + '\n')

        print(f"\n💾 数据已保存到 {output_dir}:")
        print(f"   - 完整JSON: {full_filename}")
        print(f"   - 汇总JSON: {summary_filename} ({len(summary)} 条酒店记录)")
        print(f"   - CSV文件: {csv_filename} ({len(summary)} 条酒店记录)")

    def _print_statistics(self, all_results: Dict[str, Any], target_per_city: int = 20):
        print("\n" + "=" * 60)
        print("📊 爬取统计")
        print("=" * 60)

        success_count = sum(1 for r in all_results.values() if r['success'])
        total_hotels = sum(r['count'] for r in all_results.values())

        expected_total = success_count * target_per_city
        completion_rate = (total_hotels / expected_total * 100) if expected_total > 0 else 0

        print(f"成功城市: {success_count}/{len(all_results)}")
        print(f"总计酒店: {total_hotels} 家")
        print(f"完成率: {completion_rate:.1f}%")

        hotels_with_address = 0
        for result in all_results.values():
            if result['success']:
                for hotel in result['data']:
                    if hotel.get('地址'):
                        hotels_with_address += 1
        if total_hotels > 0:
            print(
                f"有地址信息的酒店: {hotels_with_address}/{total_hotels} ({hotels_with_address / total_hotels * 100:.1f}%)")

    def scrape_single_city(self, city: str, max_hotels: Optional[int] = None, save: bool = True) -> Dict[str, Any]:
        if max_hotels is None:
            max_hotels = self.max_hotels_per_city

        result = self.scrape_city(city, max_hotels)

        if result['success']:
            print(f"\n{'=' * 60}")
            print(f"✓ {city} 抓取成功，共 {result['count']}/{max_hotels} 家酒店")
            print(f"{'=' * 60}")

            if result['data']:
                for i, hotel in enumerate(result['data'], 1):
                    print(f"\n【{i}. {hotel['酒店名称']}】")
                    if hotel.get('类型'):
                        print(f"   类型: {hotel['类型']}")
                    if hotel.get('评分'):
                        print(f"   评分: {hotel['评分']}")
                    if hotel.get('点评数'):
                        print(f"   点评: {hotel['点评数']}")
                    if hotel.get('地址'):
                        print(f"   地址: {hotel['地址']}")
                    if hotel.get('特色'):
                        print(f"   特色: {hotel['特色']}")
                    if hotel.get('收藏数'):
                        print(f"   收藏: {hotel['收藏数']}")
                    print(f"   💰 价格: {hotel['价格']}")
            else:
                print("未找到酒店数据")

            if save:
                filename = f"elong_hotels_{city}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(result['data'], f, ensure_ascii=False, indent=2)
                print(f"\n💾 数据已保存到: {filename}")

        else:
            print(f"\n✗ {city} 抓取失败")

        return result

    def get_city_id(self, city_name: str) -> Optional[str]:
        return self.city_id_map.get(city_name)

    def get_supported_cities(self) -> List[str]:
        return list(self.city_id_map.keys())


def main():
    scraper = ElongHotelAutoScraper(max_workers=1, headless=True, max_hotels_per_city=20)

    print("\n" + "=" * 60)
    print("艺龙酒店爬虫工具")
    print("=" * 60)
    print(f"默认每城市爬取: {scraper.max_hotels_per_city} 条")
    print("模式说明:")
    print("  模式2: 爬取单个城市（显示完整信息）")
    print("  模式3: 自定义城市列表批量爬取")
    print("=" * 60)

    choice = input("\n请选择模式 (2 或 3): ").strip()

    if choice == '2':
        city = input("请输入城市名称: ").strip()
        if city:
            if city in scraper.city_id_map or city in scraper.city_pinyin_map:
                print(f"将爬取 {city} 前 {scraper.max_hotels_per_city} 家酒店...")
                scraper.scrape_single_city(city)
            else:
                print(f"警告: {city} 可能不在支持列表中，将尝试使用拼音访问")
                scraper.scrape_single_city(city)

    elif choice == '3':
        print(f"\n预设城市示例: {', '.join(scraper.city_list[:5])}...")
        cities_input = input("请输入城市列表（用逗号分隔，例如: 北京,上海,广州）: ").strip()
        city_list = [c.strip() for c in cities_input.split(',') if c.strip()]

        if city_list:
            output_dir = input("请输入输出目录（直接回车使用当前目录）: ").strip()
            if not output_dir:
                output_dir = "."

            workers = input(f"请输入并发线程数（默认{scraper.max_workers}，直接回车使用默认值）: ").strip()
            if workers.isdigit():
                scraper.max_workers = int(workers)

            print(f"\n将爬取 {len(city_list)} 个城市，每个城市前 {scraper.max_hotels_per_city} 家酒店...")

            scraper.scrape_multiple_cities(city_list)

    else:
        print("无效选择，请输入 2 或 3")

    print("\n✅ 爬取完成！")


# ===================== 核心适配：给app.py调用的函数（和jiudian.py完全一致）=====================
def get_hotel_data(city, count=10):
    """
    完全兼容原jiudian.py的调用方式
    :param city: 城市名
    :param count: 爬取数量
    :return: 列表格式，字段：名称、地址、价格、评分、类型
    """
    try:
        # 初始化爬虫（无头模式，不弹窗）
        scraper = ElongHotelAutoScraper(headless=True, max_hotels_per_city=count)
        # 爬取城市数据
        result = scraper.scrape_city(city)
        # 格式化数据，匹配原有格式
        hotel_list = []
        for item in result.get('data', []):
            hotel_list.append({
                "名称": item.get("酒店名称", ""),
                "地址": item.get("地址", "暂无地址"),
                "价格": item.get("价格", "¥未知"),
                "评分": item.get("评分", "暂无评分"),
                "类型": item.get("类型", "酒店")
            })
        return hotel_list
    except Exception as e:
        print(f"艺龙爬虫调用失败: {e}")
        return []


__all__ = ['ElongHotelAutoScraper', 'main', 'get_hotel_data']

if __name__ == "__main__":
    main()