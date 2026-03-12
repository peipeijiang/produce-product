#!/bin/bash
# 一键启动 Chrome + Seedance 扩展（带反检测）

cd "$(dirname "$0")/Seedance2-Chrome-Extensions"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "❌ 依赖未安装，请先运行 install.sh"
    exit 1
fi

# 检查 Mock Server
if ! curl -s http://localhost:3456/api/config > /dev/null 2>&1; then
    echo "⚠️ Mock Server 未运行，正在启动..."
    node mock-server.js &
    sleep 2
fi

echo "✅ 启动 Chrome + 扩展（反检测模式）..."

# 启动浏览器
node -e "
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const extPath = path.resolve('.');
  const userDataDir = path.resolve('./playwright/user-data');
  
  // 反检测启动参数
  const antiDetectArgs = [
    '--disable-extensions-except=' + extPath,
    '--load-extension=' + extPath,
    '--no-first-run',
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor',
    '--start-maximized',
    '--disable-infobars',
    '--disable-notifications',
    '--disable-popup-blocking',
    '--disable-translate',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-background-networking',
    '--disable-sync',
    '--metrics-recording-only',
    '--no-report-upload',
    '--disable-domain-reliability',
    '--disable-component-extensions-with-background-pages',
    '--disable-ipc-flooding-protection',
    '--disable-features=CalculateNativeWinOcclusion',
    '--disable-backgrounding-occluded-windows',
    '--force-device-scale-factor=',
    '--enable-features=NetworkService,NetworkServiceInProcess',
    '--flag-switches-begin',
    '--disable-site-isolation-trials',
    '--flag-switches-end',
    '--use-fake-ui-for-media-stream',
    '--use-fake-device-for-media-stream',
    '--disable-default-apps',
    '--disable-features=VizDisplayCompositor'
  ];
  
  const ctx = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: antiDetectArgs,
    viewport: { width: 1920, height: 1080 },
    ignoreDefaultArgs: ['--disable-extensions'],
    locale: 'zh-CN',
    timezoneId: 'Asia/Shanghai',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
  });
  
  const page = ctx.pages()[0] || await ctx.newPage();
  
  // 设置 navigator.webdriver 为 false
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', {
      get: () => false
    });
  });
  
  // 访问即梦网站
  await page.goto('https://jimeng.jianying.com/ai-tool/image/generate', {
    waitUntil: 'networkidle',
    timeout: 30000
  });
  
  console.log('✅ 浏览器已启动（反检测模式）');
  
  // 保持进程运行
  await new Promise(() => {});
})();
"
