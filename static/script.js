/**
 * 智策 - 智能旅行助手 交互逻辑
 * 包含：平滑切换动画、密码显示切换、登录/注册 API 调用
 */
document.addEventListener('DOMContentLoaded', function () {
    // --- 1. 元素获取 ---
    const swipeContainer = document.getElementById('swipeContainer');

    // 切换按钮
    const toRegisterBtn = document.getElementById('toRegisterBtn'); // 灰色卡片上的注册按钮
    const toLoginBtn = document.getElementById('toLoginBtn');       // 灰色卡片上的返回登录按钮

    // 内容区域
    const infoLogin = document.getElementById('infoLogin');
    const infoRegister = document.getElementById('infoRegister');
    const loginSection = document.getElementById('loginSection');
    const registerSection = document.getElementById('registerSection');

    // 表单对象
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    // --- 2. 核心：平滑切换逻辑 ---

    /**
     * 执行内容切换的淡入淡出动效
     * @param {HTMLElement} hideEl - 需要隐藏的元素
     * @param {HTMLElement} showEl - 需要显示的元素
     */
    function switchContent(hideEl, showEl) {
        // 先让当前内容透明
        hideEl.style.opacity = '0';
        hideEl.style.transform = 'translateY(-10px)';

        setTimeout(() => {
            hideEl.style.display = 'none';

            // 显示新内容
            showEl.style.display = 'block';
            // 强制重绘以触发过渡
            showEl.offsetHeight;
            showEl.style.opacity = '1';
            showEl.style.transform = 'translateY(0)';
            showEl.classList.add('fade-in');
        }, 350); // 这里的延迟与 CSS 过渡时间配合
    }

    // 切换至注册状态
    toRegisterBtn.addEventListener('click', () => {
        swipeContainer.classList.add('active');
        switchContent(infoLogin, infoRegister);
        switchContent(loginSection, registerSection);
        switchContent(toRegisterBtn, toLoginBtn);
    });

    // 切换回登录状态
    toLoginBtn.addEventListener('click', () => {
        swipeContainer.classList.remove('active');
        switchContent(infoRegister, infoLogin);
        switchContent(registerSection, loginSection);
        switchContent(toLoginBtn, toRegisterBtn);
    });


    // --- 3. 密码显示/隐藏切换 ---

    document.querySelectorAll('.togglePwd').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.previousElementSibling; // 获取同级的 input
            const isPwd = input.type === 'password';

            input.type = isPwd ? 'text' : 'password';
            this.textContent = isPwd ? '隐藏' : '显示';

            // 激活反馈：轻微变色
            this.style.color = isPwd ? '#007AFF' : '#fff';
        });
    });


    // --- 4. 辅助函数：显示提示框 ---

    function showAlert(alertId, text, type = 'error') {
        const alertBox = document.getElementById(alertId);
        alertBox.textContent = text;
        alertBox.className = `alert ${type}`;
        alertBox.style.display = 'block';

        // 2.5秒后自动消失
        setTimeout(() => {
            alertBox.style.display = 'none';
        }, 2500);
    }


    // --- 5. 表单提交：登录逻辑 (对接 Flask) ---

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const pwd = document.getElementById('password').value.trim();
        const loginBtn = this.querySelector('button[type="submit"]');

        if (!username || !pwd) return showAlert('loginAlert', '请完善登录信息');

        // UI 状态反馈
        loginBtn.textContent = '验证中...';
        loginBtn.disabled = true;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, password: pwd })
            });

            const result = await response.json();

            if (result.code === 200) {
                showAlert('loginAlert', '登录成功，正在跳转', 'success');
                setTimeout(() => window.location.href = '/', 1200);
            } else {
                showAlert('loginAlert', result.msg || '登录失败');
            }
        } catch (error) {
            showAlert('loginAlert', '服务器连接失败');
        } finally {
            loginBtn.textContent = '登录';
            loginBtn.disabled = false;
        }
    });


    // --- 6. 表单提交：注册逻辑 (对接 Flask) ---

    registerForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const regUsername = document.getElementById('regUsername').value.trim();
        const regPwd = document.getElementById('regPassword').value.trim();
        const regBtn = this.querySelector('button[type="submit"]');

        if (!regUsername || !regPwd) return showAlert('registerAlert', '请设置用户名和密码');

        regBtn.textContent = '正在创建...';
        regBtn.disabled = true;

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: regUsername, password: regPwd })
            });

            const result = await response.json();

            if (result.code === 200) {
                showAlert('registerAlert', '注册成功！正在切换登录', 'success');
                // 自动切回登录页面
                setTimeout(() => toLoginBtn.click(), 2000);
            } else {
                showAlert('registerAlert', result.msg || '注册失败');
            }
        } catch (error) {
            showAlert('registerAlert', '网络异常');
        } finally {
            regBtn.textContent = '完成注册';
            regBtn.disabled = false;
        }
    });

    // --- 7. 优雅处理：禁用所有 a 标签默认行为 ---
    document.querySelectorAll('a').forEach(item => {
        item.addEventListener('click', e => {
            if (item.getAttribute('href') === '#') e.preventDefault();
        });
    });
});