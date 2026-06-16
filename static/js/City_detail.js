/**
 * 城市详情页核心逻辑
 * 1. 拦截搜索输入
 * 2. 异步请求后端数据 (模拟 MongoDB) + 外部 API (图片/天气)
 * 3. 渲染 DOM
 */


// ================= DOM 元素获取 =================
const elements = {
    bgLayer: document.getElementById('bg-layer'),
    searchInput: document.getElementById('city-search'),
    searchBtn: document.getElementById('search-btn'),
    cityName: document.getElementById('city-name'),
    citySlogan: document.getElementById('city-slogan'),
    cityTags: document.getElementById('city-tags'),
    temp: document.getElementById('weather-temp'),
    weatherStatus: document.getElementById('weather-status'),
    statPop: document.getElementById('stat-pop'),
    statGdp: document.getElementById('stat-gdp'),
    statArea: document.getElementById('stat-area')
};

// ================= 核心逻辑方法 =================

// 1. 模拟你的 MongoDB 后端请求
// 实际开发中，这里应当是 fetch(`http://localhost:3000/api/cities/${cityName}`)
async function fetchCityFromMongoDB(cityName) {
    console.log(`正在从 MongoDB 查询数据: ${cityName}`);

    // 这里做了一个前端的假数据返回，模拟你保存在 DB 里的结构
    const mockDB = {
        "上海": {
            population: "2487万", gdp: "4.72万亿", area: "6340",
            slogan: "魔都，潮流与历史的交汇点", highlights: ["外滩", "东方明珠", "陆家嘴"],
            lat: "31.23", lon: "121.47"
        },
        "成都": {
            population: "2126万", gdp: "2.21万亿", area: "14335",
            slogan: "天府之国，安逸与活力的代名词", highlights: ["大熊猫基地", "宽窄巷子", "春熙路"],
            lat: "30.65", lon: "104.06"
        }
    };

    return new Promise((resolve) => {
        setTimeout(() => {
            if(mockDB[cityName]) {
                resolve(mockDB[cityName]);
            } else {
                // 如果数据库没找到，返回默认兜底数据
                resolve({
                    population: "未知", gdp: "未知", area: "未知",
                    slogan: "探索这座美丽的城市", highlights: ["地标建筑", "特色美食"],
                    lat: "39.90", lon: "116.40" // 默认北京坐标
                });
            }
        }, 300); // 模拟网络延迟
    });
}

// 2. 获取城市背景图
async function fetchCityImage(cityName) {
    const path = `/static/images/city/${cityName}.jpg`;

    return new Promise((resolve) => {
        const img = new Image();

        img.onload = () => {
            resolve(path);
        };

        img.onerror = () => {
            resolve('/static/images/city/default.jpg');
        };

        img.src = path;
    });
}

// 3. 获取实时天气数据 (中国天气网)
async function fetchWeather(city) {
    try {
        const res = await fetch(`/api/weather_detail?city=${city}`);
        const data = await res.json();

        return {
            temp: data.temp.val,
            text: data.desc
        };
    } catch (e) {
        console.error("天气接口失败", e);
        return { temp: "--", text: "暂无数据" };
    }
}
// ================= UI 更新逻辑 =================
async function updateDashboard(cityName) {
    if (!cityName) return;

    elements.cityName.textContent = "加载中...";
    elements.citySlogan.textContent = "正在同步最新数据";

    // 1. 获取后端数据库数据
    const dbData = await fetchCityFromMongoDB(cityName);

    // 2. 更新基础文本
    elements.cityName.textContent = cityName;
    elements.citySlogan.textContent = dbData.slogan;
    elements.statPop.textContent = dbData.population;
    elements.statGdp.textContent = dbData.gdp;
    elements.statArea.textContent = `${dbData.area} km²`;

    // 3. 渲染标签
    elements.cityTags.innerHTML = '';
    dbData.highlights.forEach(tag => {
        const span = document.createElement('span');
        span.className = 'tag';
        span.textContent = tag;
        elements.cityTags.appendChild(span);
    });

    // 4. 并行请求外部 API (图片和天气) 加快渲染速度
    const [imgUrl, weatherData] = await Promise.all([
        fetchCityImage(cityName),
        fetchWeather(cityName)
    ]);

    // 5. 更新背景
    if (elements.bgLayer) {

    if (imgUrl) {
        elements.bgLayer.style.backgroundImage = `url(${imgUrl})`;
    } else {
        elements.bgLayer.style.backgroundImage =
            'linear-gradient(135deg,#dbeafe,#eff6ff)';
    }

}

    // 6. 更新天气
    elements.temp.textContent = weatherData.temp;
    elements.weatherStatus.textContent = weatherData.text;
}

// ================= 事件绑定 =================
elements.searchBtn.addEventListener('click', () => {
    const val = elements.searchInput.value.trim();
    if(val) updateDashboard(val);
});

elements.searchInput.addEventListener('keypress', (e) => {
    if(e.key === 'Enter') {
        const val = elements.searchInput.value.trim();
        if(val) updateDashboard(val);
    }
});

// 页面加载时默认初始化上海的数据
window.addEventListener('DOMContentLoaded', () => {
    updateDashboard('上海');
});