const { createApp, ref, onMounted, nextTick } = Vue;

createApp({
    setup() {
        const searchCity = ref('');
        const weather = ref({});
        const hotels = ref([]);
        const scenics = ref([]);
        const foods = ref([]);
        const loading = ref(false);

        const visitorCount = ref(128420);

        const weatherVisible = ref(false);
        const hotelsVisible = ref(false);
        const scenicsVisible = ref(false);

        const activeChart = ref('price');
        const currentPage = ref('home');

        // ====== 今日旅游推荐状态 ======
        const todayDate = ref('');
        const todayTip = ref({ content: '', tag: '' });

        let autoSwitchTimer = null;
        let map = null;
        let userPosition = null;

        let priceChartInstance = null;
        let priceTimer = null;

        // =========================
        // 生成今日推荐数据
        // =========================
        const initTodayRecommend = () => {
            const tips = [
                { content: "北京：逛故宫、登长城、吃烤鸭，感受千年古都的历史底蕴与现代繁华。", tag: "古都" },
                { content: "上海：漫步外滩、打卡陆家嘴、逛田子坊，体验魔都的时尚与烟火气。", tag: "都市" },
                { content: "杭州：游西湖、品龙井、逛灵隐寺，人间天堂，一步一景。", tag: "江南" },
                { content: "苏州：赏园林、乘乌篷船、听评弹，小桥流水，江南韵味十足。", tag: "江南" },
                { content: "西安：逛兵马俑、登城墙、吃羊肉泡馍，梦回大唐，历史感拉满。", tag: "古都" },
                { content: "成都：逛宽窄巷子、看大熊猫、吃火锅，慢生活巴适得板。", tag: "休闲" },
                { content: "重庆：打卡洪崖洞、吃火锅、坐长江索道，8D魔幻山城超震撼。", tag: "山城" },
                { content: "厦门：逛鼓浪屿、吃沙茶面、看海边日落，文艺清新海滨小城。", tag: "海滨" },
                { content: "青岛：逛八大关、喝啤酒、吃海鲜，红瓦绿树，碧海蓝天。", tag: "海滨" },
                { content: "大理：游洱海、登苍山、逛古城，风花雪月，治愈心灵。", tag: "文艺" },
                { content: "丽江：逛古城、看玉龙雪山、遇四方街，浪漫慢生活圣地。", tag: "文艺" },
                { content: "三亚：海边度假、潜水冲浪、吃热带水果，冬日避寒首选。", tag: "度假" },
                { content: "桂林：游漓江、看山水、逛西街，桂林山水甲天下。", tag: "山水" },
                { content: "张家界：看奇峰怪石、走玻璃栈道，仙境般的自然奇观。", tag: "山水" },
                { content: "南京：逛中山陵、游夫子庙、吃鸭血粉丝汤，六朝古都底蕴深厚。", tag: "古都" },
                { content: "天津：逛意风区、听相声、吃煎饼果子，幽默风趣的海滨老城。", tag: "都市" },
                { content: "广州：逛小蛮腰、吃早茶、逛沙面，美食之都，烟火气十足。", tag: "美食" },
                { content: "深圳：逛世界之窗、游海边、打卡科技之城，年轻活力大都市。", tag: "都市" },
                { content: "昆明：逛滇池、游石林、赏花，四季如春的花城。", tag: "春城" },
                { content: "哈尔滨：看冰雕、逛中央大街、吃俄式西餐，冰城冬日超梦幻。", tag: "冰雪" },
                { content: "长春：逛净月潭、看伪满皇宫，北国春城风景宜人。", tag: "北方" },
                { content: "沈阳：逛故宫、吃东北菜，历史厚重的东北老城。", tag: "古都" },
                { content: "福州：逛三坊七巷、吃佛跳墙，温泉之城，古韵十足。", tag: "古都" },
                { content: "济南：逛趵突泉、登千佛山、游大明湖，泉城风光秀丽。", tag: "泉城" },
                { content: "太原：逛晋祠、吃面食，龙城太原，历史悠久。", tag: "古都" },
                { content: "合肥：逛三河古镇、吃徽菜，包公故里，人文荟萃。", tag: "人文" },
                { content: "南昌：逛滕王阁、吃瓦罐汤，红色古都，英雄之城。", tag: "人文" },
                { content: "南宁：逛青秀山、吃螺蛳粉，绿城南宁，四季常青。", tag: "绿城" },
                { content: "银川：逛沙湖、吃滩羊，塞上江南，风光无限。", tag: "西北" },
                { content: "兰州：逛黄河铁桥、吃牛肉面，西北重镇，风味独特。", tag: "西北" },
                { content: "西宁：逛青海湖、吃牦牛肉，青藏高原门户，风景绝美。", tag: "西北" },
                { content: "拉萨：逛布达拉宫、转八廓街，雪域圣城，净化心灵。", tag: "圣城" },
                { content: "乌鲁木齐：逛大巴扎、吃瓜果，西域风情，美食天堂。", tag: "西域" },
                { content: "呼和浩特：驰骋草原，住蒙古包，体验地道游牧风情。", tag: "草原" }
            ];
            const dayOfMonth = new Date().getDate();
            todayTip.value = tips[dayOfMonth % tips.length];
            todayDate.value = new Date().toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        };

        // =========================
        // 价格趋势图
        // =========================
        const initPriceChart = (cityName) => {
            const chartDom = document.getElementById('price-chart');
            if (!chartDom) return;

            if (priceChartInstance) {
                priceChartInstance.dispose();
            }

            try {
                priceChartInstance = echarts.init(chartDom);
                let timeData = [];
                let priceData = [];
                let currentDate = new Date();

                const getTime = () => {
                    const month = currentDate.getMonth() + 1;
                    const day = currentDate.getDate();
                    const text = `${month}/${day}`;
                    currentDate.setDate(currentDate.getDate() + 1);
                    return text;
                };

                const randomPrice = (last) => {
                    const change = Math.floor(Math.random() * 50 - 25);
                    let newPrice = last + change;
                    if (newPrice < 320) newPrice = 320;
                    if (newPrice > 680) newPrice = 680;
                    return newPrice;
                };

                let basePrice = 420;
                for (let i = 0; i < 5; i++) {
                    timeData.push(getTime());
                    basePrice = randomPrice(basePrice);
                    priceData.push(basePrice);
                }

                priceChartInstance.setOption({
                    tooltip: { trigger: 'axis' },
                    grid: { top: 20, left: 35, right: 10, bottom: 25 },
                    xAxis: {
                        type: 'category',
                        boundaryGap: false,
                        data: timeData,
                        axisLabel: { fontSize: 10, color: '#86868b' }
                    },
                    yAxis: {
                        type: 'value',
                        min: 200,
                        max: 700,
                        axisLabel: { fontSize: 10 },
                        splitLine: { lineStyle: { type: 'dashed', color: '#dbe7ff' } }
                    },
                    series: [{
                        name: '酒店均价',
                        type: 'line',
                        smooth: true,
                        data: priceData,
                        color: '#007AFF',
                        symbol: 'circle',
                        symbolSize: 6,
                        lineStyle: { width: 3 },
                        areaStyle: { color: 'rgba(0,122,255,0.08)' }
                    }]
                });

                if (priceTimer) clearInterval(priceTimer);
                priceTimer = setInterval(() => {
                    if (!priceChartInstance) return;
                    timeData.shift();
                    priceData.shift();
                    timeData.push(getTime());
                    const lastPrice = priceData[priceData.length - 1] || 420;
                    priceData.push(randomPrice(lastPrice));

                    priceChartInstance.setOption({
                        xAxis: { data: timeData },
                        series: [{ data: priceData }]
                    });
                }, 5000);
            } catch(e) {
                console.error("价格图表初始化失败", e);
            }
        };

        // =========================
        // 温度图
        // =========================
        const initTempChart = () => {
            const chartDom = document.getElementById('temp-chart');
            if (!chartDom) return;

            try {
                const tChart = echarts.init(chartDom);
                tChart.setOption({
                    tooltip: { trigger: 'axis' },
                    grid: { top: 20, left: 35, right: 10, bottom: 25 },
                    xAxis: {
                        type: 'category',
                        data: ['06时', '12时', '18时', '预测'],
                        axisLabel: { fontSize: 10 }
                    },
                    yAxis: {
                        type: 'value',
                        axisLabel: { fontSize: 10, formatter: '{value}°' },
                        splitLine: { lineStyle: { type: 'dashed' } }
                    },
                    series: [{
                        name: '温度',
                        data: [18, 26, 22, 20],
                        type: 'line',
                        smooth: true,
                        color: '#FF9500',
                        areaStyle: { color: 'rgba(255,149,0,0.1)' }
                    }]
                });
            } catch(e) {
                console.error("温度图表初始化失败", e);
            }
        };

        // =========================
        // 游客趋势图
        // =========================
        const initVisitorChart = () => {
            const chartDom = document.getElementById('visitor-chart');
            if (!chartDom) return;

            try {
                const vChart = echarts.init(chartDom);
                vChart.setOption({
                    grid: { top: 10, left: 10, right: 10, bottom: 10 },
                    xAxis: { type: 'category', show: false, data: ['周一', '周二', '周三', '周四', '周五'] },
                    yAxis: { type: 'value', show: false },
                    series: [{
                        data: [9000, 12000, 15000, 18000, 22000],
                        type: 'line',
                        smooth: true,
                        symbol: 'none',
                        lineStyle: { width: 4, color: '#007AFF' },
                        areaStyle: { color: 'rgba(0,122,255,0.12)' }
                    }]
                });
            } catch(e) {
                console.error("游客图表初始化失败", e);
            }
        };

        // =========================
        // 热度雷达图
        // =========================
        const initHotChart = (cityName) => {
            const chartDom = document.getElementById('hot-chart');
            if (!chartDom) return;

            try {
                const hChart = echarts.init(chartDom);
                hChart.setOption({
                    radar: {
                        indicator: [
                            { name: '人流', max: 100 },
                            { name: '价格', max: 100 },
                            { name: '好评', max: 100 },
                            { name: '交通', max: 100 },
                            { name: '餐饮', max: 100 }
                        ],
                        radius: 55,
                        center: ['50%', '55%'],
                        axisName: { fontSize: 10, color: '#86868b' }
                    },
                    series: [{
                        type: 'radar',
                        data: [{ value: [80, 70, 90, 60, 85], name: cityName }],
                        itemStyle: { color: '#5856D6' },
                        areaStyle: { opacity: 0.2 }
                    }]
                });
            } catch(e) {
                console.error("热度图表初始化失败", e);
            }
        };

        // =========================
        // 图表切换
        // =========================
        const toggleChart = () => {
            activeChart.value = activeChart.value === 'price' ? 'temp' : 'price';
            nextTick(() => {
                if (activeChart.value === 'price') {
                    initPriceChart(searchCity.value);
                } else {
                    initTempChart();
                }
            });
        };

        // =========================
        // 地图初始化
        // =========================
        const initRealMap = () => {
            const mapContainer = document.getElementById('mapContainer');
            if (!mapContainer || typeof AMap === 'undefined') return;

            try {
                if (!map) {
                    map = new AMap.Map('mapContainer', {
                        zoom: 13,
                        resizeEnable: true
                    });
                }
                if (userPosition) {
                    map.setCenter(userPosition);
                    map.setZoom(14);
                }
            } catch (e) {
                console.log('地图初始化失败', e);
            }
        };

        // =========================
        // 添加地图标记
        // =========================
        const addMapMarkers = () => {
            if (!map) return;

            try {
                map.clearMap();

                if (userPosition) {
                    new AMap.Marker({
                        map,
                        position: userPosition,
                        title: '您的当前位置',
                        icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_bs.png'
                    });
                    map.setCenter(userPosition);
                }

                hotels.value.forEach(hotel => {
                    if (hotel.lat && hotel.lng) {
                        new AMap.Marker({
                            map: map,
                            position: new AMap.LngLat(hotel.lng, hotel.lat),
                            title: hotel.name,
                            icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_go.png'
                        });
                    }
                });

                scenics.value.forEach(scenic => {
                    if (scenic.lat && scenic.lng) {
                        new AMap.Marker({
                            map: map,
                            position: new AMap.LngLat(scenic.lng, scenic.lat),
                            title: scenic.name,
                            icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png'
                        });
                    }
                });

                foods.value.forEach(food => {
                    if (food.lat && food.lng) {
                        new AMap.Marker({
                            map: map,
                            position: new AMap.LngLat(food.lng, food.lat),
                            title: food.name,
                            icon: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_r.png'
                        });
                    }
                });
            } catch (e) {
                console.log('地图标记加载失败', e);
            }
        };

        // =========================
        // 搜索
        // =========================
        const doSearch = async () => {
            const city = searchCity.value.trim();
            if (!city) return;

            loading.value = true;
            if (autoSwitchTimer) clearInterval(autoSwitchTimer);

            try {
                // 天气数据
                const wRes = await axios.get('/api/weather_detail', { params: { city } });
                weather.value = {
                    city: wRes.data.city,
                    temp: wRes.data.temp.val,
                    desc: wRes.data.desc,
                    humidity: wRes.data.humidity.val,
                    wind: wRes.data.wind.speed,
                    aqi: wRes.data.aqi.val,
                    sunrise: wRes.data.sun.rise
                };

                weatherVisible.value = true;

                // 搜索周边数据
                const res = await axios.get(`/api/search?city=${city}`);
                const items = res.data.data || [];

                hotels.value = items.filter(x => x.type === 'hotel').slice(0, 3);
                scenics.value = items.filter(x => x.type === 'scenic').slice(0, 4);
                foods.value = items.filter(x => x.type === 'food').slice(0, 12);

                hotelsVisible.value = true;
                scenicsVisible.value = true;

                await nextTick();
                initPriceChart(city);
                initHotChart(city);
                initVisitorChart();
                initRealMap();
                addMapMarkers();

                autoSwitchTimer = setInterval(toggleChart, 8000);
            } catch (e) {
                console.error('搜索接口请求失败，进入本地 Mock 兜底逻辑', e);

                weather.value = {
                    city: city,
                    temp: '26°',
                    desc: '晴',
                    humidity: '58',
                    wind: '2级',
                    aqi: '45',
                    sunrise: '06:10'
                };
                weatherVisible.value = true;

                hotels.value = [{
                    id: 1, name: '示例酒店', address: '示例地址',
                    lng: userPosition ? userPosition[0] : 121.47,
                    lat: userPosition ? userPosition[1] : 31.23
                }];
                scenics.value = [{
                    id: 1, name: '示例景点',
                    lng: userPosition ? userPosition[0] : 121.47,
                    lat: userPosition ? userPosition[1] : 31.23
                }];
                foods.value = [{
                    id: 1, name: '示例餐厅',
                    lng: userPosition ? userPosition[0] : 121.47,
                    lat: userPosition ? userPosition[1] : 31.23
                }];

                hotelsVisible.value = true;
                scenicsVisible.value = true;

                await nextTick();
                initPriceChart(city);
                initHotChart(city);
                initVisitorChart();
                initRealMap();
                addMapMarkers();
            } finally {
                loading.value = false;
            }
        };

        // 新增：防闪退缺失函数定义
        const goFoodPage = () => {
            console.log('跳转至餐饮详情页');
        };

        // =========================
        // 页面初始化
        // =========================
        onMounted(() => {
            // 初始化旅游推荐
            initTodayRecommend();

            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    async (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        userPosition = [lng, lat];

                        try {
                            const res = await axios.get(
                                `https://restapi.amap.com/v3/geocode/regeo?location=${lng},${lat}&key=4e66b2a63134502213b13b5e64db2010`
                            );
                            const address = res.data.regeocode.addressComponent;
                            const city = typeof address.city === 'string' ? address.city : address.province || '上海';
                            searchCity.value = city;
                            doSearch();
                        } catch (e) {
                            console.log('城市解析失败，进入上海默认搜索');
                            searchCity.value = '上海';
                            doSearch();
                        }
                    },
                    (err) => {
                        console.log('用户拒绝定位或定位超时，进入上海默认搜索', err);
                        searchCity.value = '上海';
                        doSearch();
                    },
                    { timeout: 5000 } // 设置5秒超时，防止原生定位无响应死锁
                );
            } else {
                searchCity.value = '上海';
                doSearch();
            }
        });

        // =========================
        // 导出至模板使用
        // =========================
        return {
            searchCity,
            weather,
            hotels,
            scenics,
            foods,
            currentPage,
            loading,
            weatherVisible,
            hotelsVisible,
            scenicsVisible,
            activeChart,
            visitorCount,
            todayDate,
            todayTip,
            doSearch,
            toggleChart,
            goFoodPage
        };
    }
}).mount('#app');