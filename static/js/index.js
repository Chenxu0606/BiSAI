const { createApp, ref, onMounted } = Vue;

createApp({
    setup() {
        const searchCity = ref('');
        const weather = ref({});
        const hotels = ref([]);
        const scenics = ref([]);
        const loading = ref(false);

        // 动画控制
        const weatherVisible = ref(false);
        const hotelsVisible = ref(false);
        const scenicsVisible = ref(false);

        // 卡片轮换控制
        const activeChart = ref('price');
        let autoSwitchTimer = null;

        // 初始化价格图表 (优化 Grid 和字号)
        const initPriceChart = (cityName) => {
            const chartDom = document.getElementById('price-chart');
            if (!chartDom) return;
            const pChart = echarts.init(chartDom);
            pChart.setOption({
                tooltip: { trigger: 'axis' },
                grid: { top: 20, left: 35, right: 10, bottom: 25 }, // 紧凑布局
                xAxis: {
                    type: 'category',
                    data: ['4.14', '4.16', '4.18', '今日', '预测'],
                    axisLabel: { fontSize: 10 } // 缩小文字
                },
                yAxis: {
                    type: 'value',
                    axisLabel: { fontSize: 10 },
                    splitLine: { lineStyle: { type: 'dashed' } }
                },
                series: [{
                    name: '均价',
                    data: [420, 435, 410, 520, 550],
                    type: 'line', smooth: true, color: '#007AFF',
                    areaStyle: { color: 'rgba(0, 122, 255, 0.08)' },
                    symbol: 'circle'
                }]
            });
        };

        // 初始化温度图表 (优化 Grid 和字号)
        const initTempChart = (cityName) => {
            const chartDom = document.getElementById('temp-chart');
            if (!chartDom) return;
            const tChart = echarts.init(chartDom);
            tChart.setOption({
                tooltip: { trigger: 'axis' },
                grid: { top: 20, left: 35, right: 10, bottom: 25 }, // 紧凑布局
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
                    type: 'line', smooth: true, color: '#FF9500',
                    areaStyle: { color: 'rgba(255, 149, 0, 0.1)' }
                }]
            });
        };

        // 初始化雷达图 (缩小半径适配小卡片)
        const initHotChart = (cityName) => {
            const chartDom = document.getElementById('hot-chart');
            if (!chartDom) return;
            const hChart = echarts.init(chartDom);
            hChart.setOption({
                radar: {
                    indicator: [
                        { name: '人流', max: 100 }, { name: '价格', max: 100 },
                        { name: '好评', max: 100 }, { name: '交通', max: 100 }, { name: '餐饮', max: 100 }
                    ],
                    radius: 55, // 减小半径防止溢出
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
        };

        const toggleChart = () => {
            activeChart.value = activeChart.value === 'price' ? 'temp' : 'price';
            // 必须在 DOM 渲染后的 nextTick 执行，这里用 setTimeout 模拟
            setTimeout(() => {
                activeChart.value === 'price' ? initPriceChart(searchCity.value) : initTempChart(searchCity.value);
            }, 50);
        };

        const doSearch = async () => {
            const city = searchCity.value.trim();
            if (!city) return;
            loading.value = true;
            if (autoSwitchTimer) clearInterval(autoSwitchTimer);

            try {
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

                const res = await axios.get(`/api/search?city=${city}`);
                const items = res.data.data || [];
                hotels.value = items.filter(x => x.type === 'hotel').slice(0, 3);
                scenics.value = items.filter(x => x.type === 'scenic').slice(0, 4);
                hotelsVisible.value = true;
                scenicsVisible.value = true;

                // 初始化默认图表
                setTimeout(() => {
                    initPriceChart(city);
                    initHotChart(city);
                    // 开启自动轮换 (每8秒切换一次)
                    autoSwitchTimer = setInterval(toggleChart, 8000);
                }, 400);

            } catch (e) {
                console.error("搜索失败:", e);
                // 演示模式：如果接口报错，依然显示图表框架
                setTimeout(() => { initPriceChart(city); initHotChart(city); }, 400);
            }
            loading.value = false;
        };

        onMounted(() => {
            searchCity.value = '上海';
            doSearch();
        });

        return {
            searchCity, weather, hotels, scenics, loading,
            weatherVisible, hotelsVisible, scenicsVisible,
            activeChart, doSearch, toggleChart
        };
    }
}).mount('#app');