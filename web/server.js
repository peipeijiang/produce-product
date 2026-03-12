const express = require('express');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = 3457;

// CORS 配置
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    
    next();
});

app.use(express.json());

// 启动 Chrome 浏览器
app.post('/api/start-chrome', (req, res) => {
    const scriptPath = path.join(__dirname, '../start-chrome.sh');
    
    console.log('🚀 启动 Chrome 浏览器...');
    
    const child = spawn('bash', [scriptPath], {
        cwd: path.join(__dirname, '..'),
        detached: true,
        stdio: 'ignore'
    });
    
    child.on('error', (error) => {
        console.error('❌ 启动 Chrome 失败:', error);
        res.json({ success: false, error: error.message });
    });
    
    child.unref();
    
    setTimeout(() => {
        console.log('✅ Chrome 启动命令已发送');
        res.json({ success: true, message: 'Chrome 启动中...' });
    }, 500);
});

// 停止 Chrome 浏览器
app.post('/api/stop-chrome', (req, res) => {
    console.log('🛑 停止 Chrome 浏览器...');
    
    spawn('pkill', ['-f', 'playwright.*chrome'], {
        stdio: 'ignore'
    });
    
    setTimeout(() => {
        console.log('✅ Chrome 已停止');
        res.json({ success: true, message: 'Chrome 已停止' });
    }, 500);
});

// 检查 Chrome 状态
app.get('/api/chrome-status', (req, res) => {
    const ps = spawn('pgrep', ['-f', 'playwright.*chrome']);
    ps.on('close', (code) => {
        res.json({ running: code === 0 });
    });
});

app.listen(PORT, () => {
    console.log(`🌐 Web 服务器运行在 http://localhost:${PORT}`);
});
