/* =====================================
   Attraction Center JS
   中国景点探索中心
===================================== */

/* =====================================
   HERO轮播数据
===================================== */

const heroImages = [
    "/static/images/attractions/westlake.jpg",
    "/static/images/attractions/bb.jpg",
    "/static/images/attractions/cc.jpg",
    "/static/images/attractions/tiantan.jpg"

];

/* =====================================
   AI推荐数据
===================================== */

const aiRecommendations = [
    {
        name: "青海湖",
        desc: "中国最美湖泊之一，夏季避暑圣地",
        image: "/static/images/attractions/qinghaihu.jpg"
    },
    {
        name: "呼伦贝尔",
        desc: "草原风光天花板，自驾旅行首选",
        image: "/static/images/attractions/hulunbeier.jpg"
    },
    {
        name: "长白山",
        desc: "森林、天池与雪山的完美结合",
        image: "/static/images/attractions/changbaishan.jpg"
    }
];

/* =====================================
   十大景点
===================================== */

const topAttractions = [
    {
        name: "故宫",
        image: "/static/images/attractions/gugong.jpg"
    },
    {
        name: "西湖",
        image: "/static/images/attractions/xihu.jpg"
    },
    {
        name: "九寨沟",
        image: "/static/images/attractions/jiuzhaigou.jpg"
    },
    {
        name: "黄山",
        image: "/static/images/attractions/huangshan.jpg"
    },
    {
        name: "张家界",
        image: "/static/images/attractions/zhangjiajie.jpg"
    },
    {
        name: "布达拉宫",
        image: "/static/images/attractions/potala.jpg"
    },
    {
        name: "鼓浪屿",
        image: "/static/images/attractions/gulangyu.jpg"
    },
    {
        name: "长城",
        image: "/static/images/attractions/greatwall.jpg"
    },
    {
        name: "稻城亚丁",
        image: "/static/images/attractions/daocheng.jpg"
    },
    {
        name: "喀纳斯",
        image: "/static/images/attractions/kanasi.jpg"
    }
];

/* =====================================
   Hero背景轮播
===================================== */

let heroIndex = 0;

function initHeroSlider() {

    const heroBg = document.getElementById("hero-bg");
    if (!heroBg) return;

    heroIndex = 0;

    heroBg.style.backgroundImage = `url("${heroImages[0]}")`;
    heroBg.style.opacity = "1";

    setInterval(() => {

        heroIndex = (heroIndex + 1) % heroImages.length;

        const img = new Image();
        img.src = heroImages[heroIndex];

        img.onload = () => {
            heroBg.style.backgroundImage = `url("${img.src}")`;
        };

    }, 5000);
}
/* =====================================
   AI推荐渲染
===================================== */



function renderAIRecommendations() {

    const container = document.getElementById("ai-recommend-list");
    if (!container) return;

    container.innerHTML = "";

    aiRecommendations.forEach(item => {

        const card = document.createElement("div");
        card.className = "recommend-card glass-card";

        card.innerHTML = `
            <div class="recommend-cover"></div>
            <div class="recommend-body">
                <h3>${item.name}</h3>
                <p>${item.desc}</p>
            </div>
        `;

        const cover = card.querySelector(".recommend-cover");

        cover.style.backgroundImage = `url("${item.image}")`;

        container.appendChild(card);
    });
}

/* =====================================
   十大景点渲染
===================================== */

function renderTopAttractions() {

    const container =
        document.getElementById("top-attractions");

    if (!container) return;

    container.innerHTML = "";

    topAttractions.forEach(item => {

        const card =
            document.createElement("div");

        card.className =
            "attraction-card glass-card";

        card.innerHTML = `
            <div class="attraction-cover"></div>
        
            <div class="attraction-info">
                <h3>${item.name}</h3>
                <p>中国热门景点</p>
            </div>
        `;

        const cover =
            card.querySelector(".attraction-cover");

        cover.style.backgroundImage =
            `url('${item.image}')`;

                container.appendChild(card);

            });

        }

/* =====================================
   热门城市点击
===================================== */

function bindCityCards() {

    const cityCards =
        document.querySelectorAll(".city-card");

    cityCards.forEach(card => {

        card.addEventListener("click", () => {

            const city =
                card.dataset.city;

            window.location.href =
                `/city_detail?city=${encodeURIComponent(city)}`;

        });

    });

}

/* =====================================
   Explore按钮
===================================== */

function bindExploreButton() {

    const btn =
        document.getElementById("explore-btn");

    if (!btn) return;

    btn.addEventListener("click", () => {

        const section =
            document.querySelector(".section-card");

        if (!section) return;

        section.scrollIntoView({
            behavior: "smooth"
        });

    });

}

/* =====================================
   横向滚动优化
===================================== */

function initHorizontalScroll() {

    const container =
        document.getElementById("top-attractions");

    if (!container) return;

    container.addEventListener("wheel", e => {

        e.preventDefault();

        container.scrollLeft +=
            e.deltaY;

    });

}

/* =====================================
   页面滚动渐显动画
===================================== */

function initRevealAnimation() {

    const cards =
        document.querySelectorAll(
            ".glass-card"
        );

    const observer =
        new IntersectionObserver(entries => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    entry.target.style.opacity = "1";

                    entry.target.style.transform =
                        "translateY(0)";

                }

            });

        }, {
            threshold: 0.15
        });

    cards.forEach(card => {

        card.style.opacity = "0";

        card.style.transform =
            "translateY(40px)";

        card.style.transition =
            "all 0.8s ease";

        observer.observe(card);

    });

}

/* =====================================
   API接口预留
===================================== */

async function loadAttractionsFromAPI() {

    try {

        const response =
            await fetch("/api/attractions");

        const result =
            await response.json();

        console.log(
            "景点接口返回数据：",
            result
        );

    } catch (error) {

        console.warn(
            "景点接口未启动，使用本地Mock数据"
        );

    }

}

/* =====================================
   初始化
===================================== */

window.addEventListener(
    "DOMContentLoaded",
    () => {

        initHeroSlider();

        renderAIRecommendations();

        renderTopAttractions();

        bindCityCards();

        bindExploreButton();

        initHorizontalScroll();

        initRevealAnimation();

        loadAttractionsFromAPI();

    }
);