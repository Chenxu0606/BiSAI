var map, infoWindow, markers = [];
var idleTime = 0;

function initMap(data) {
    map = new AMap.Map('map-container', {
        zoom: 12,
        center: [116.397, 39.909],
        mapStyle: 'amap://styles/darkblue',
        viewMode: '3D',
        pitch: 45
    });

    infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -30) });

    if (data && data.length > 0) {
        renderMarkers(data);
        map.setFitView();
    }

    map.on('moveend', () => {
        let center = map.getCenter();
        fetch(`/api/nearby?lng=${center.lng}&lat=${center.lat}`)
            .then(res => res.json())
            .then(res_data => renderMarkers(res_data, false));
    });

    // 待机系统
    setInterval(() => {
        idleTime++;
        if (idleTime >= 30) document.getElementById('idle-overlay').style.display = 'flex';
    }, 1000);

    const wake = () => {
        idleTime = 0;
        document.getElementById('idle-overlay').style.display = 'none';
    };
    ['mousemove', 'click', 'keydown'].forEach(e => window.addEventListener(e, wake));
}

function renderMarkers(data, resetView = true) {
    markers.forEach(m => m.setMap(null));
    markers = [];
    data.forEach(item => {
        let pos = item.坐标 ? item.坐标.split(',') : item.location_point.coordinates;
        let marker = new AMap.Marker({ position: [parseFloat(pos[0]), parseFloat(pos[1])], map: map });
        marker.on('click', () => {
            infoWindow.setContent(`<div style="color:#333;padding:10px;"><b>${item.店铺名称}</b><br><small>${item.详细地址}</small></div>`);
            infoWindow.open(map, marker.getPosition());
        });
        markers.push(marker);
    });
    if(resetView && markers.length > 0) map.setFitView();
}

function moveMap(lnglat, name, addr) {
    let pos = lnglat.split(',');
    let target = [parseFloat(pos[0]), parseFloat(pos[1])];
    map.panTo(target);
    map.setZoom(16);
    setTimeout(() => {
        infoWindow.setContent(`<div style="color:#333;padding:10px;"><b>${name}</b><br><small>${addr}</small></div>`);
        infoWindow.open(map, target);
    }, 500);
}