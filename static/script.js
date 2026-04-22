document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('toggleBtn');
    const password = document.getElementById('password');
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const alertBox = document.getElementById('alert');

    // 显示/隐藏密码
    toggleBtn.addEventListener('click', function () {
        const type = password.type === 'password' ? 'text' : 'password';
        password.type = type;
        this.textContent = type === 'password' ? '显示' : '隐藏';
    });

    // 提示框
    function showAlert(text, type = 'error') {
        alertBox.textContent = text;
        alertBox.className = `alert ${type}`;
        alertBox.style.display = 'block';
        setTimeout(() => {
            alertBox.style.display = 'none';
        }, 2500);
    }

    // 🔥 核心修复：对接 Flask 后端登录 API
    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const username = document.getElementById('username').value.trim();
        const pwd = password.value.trim();

        if (!username) return showAlert('请输入用户名或邮箱');
        if (!pwd) return showAlert('请输入密码');

        loginBtn.textContent = '登录中...';
        loginBtn.disabled = true;

        try {
            // 向后端发送登录请求
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: pwd
                })
            });

            const result = await response.json();

            if (result.code === 200) {
                // 登录成功 → 跳转到首页
                showAlert('登录成功，正在跳转', 'success');
                setTimeout(() => {
                    window.location.href = '/'; // 跳转到 Flask 首页路由
                }, 1500);
            } else {
                // 登录失败
                showAlert(result.msg);
            }
        } catch (error) {
            showAlert('网络异常，请重试');
        } finally {
            // 恢复按钮状态
            loginBtn.textContent = '登录';
            loginBtn.disabled = false;
        }
    });

    // 禁用链接默认跳转
    document.querySelectorAll('a').forEach(item => {
        item.addEventListener('click', e => e.preventDefault());
    });
});