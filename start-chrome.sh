#!/bin/bash
# 一键启动 Chrome + Seedance 扩展

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

echo "✅ 启动 Chrome + 扩展..."

# 启动浏览器
node -e "
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const extPath = path.resolve('.');
  const userDataDir = path.resolve('./playwright/user-data');
  
  const ctx = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      '--disable-extensions-except=' + extPath,
      '--load-extension=' + extPath,
      '--no-first-run',
      '--disable-blink-features=AutomationControlled',
    ],
    viewport: { width: 1440, height: 900 },
    ignoreDefaultArgs: ['--disable-extensions'],
  });
  
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto('https://jimeng.jianying.com/ai-tool/image/generate');
  console.log('✅ 浏览器已启动');
  
  await new Promise(() => {});
})();
"
