# produce-product

产品营销视频自动化制作工具。

## 功能

- 根据产品图片自动生成 15s 营销视频
- 智能设计 3-5 个版本（奢华展示、功能展示、生活方式）
- 批量推送到 Seedance（ 即梦AI）
- 浏览器插件自动执行生成

## 准备工作

### 1. 安装基础环境

```bash
# Node.js (18+)
# 下载: https://nodejs.org

# Python (3.8+)
# macOS: brew install python3
# Windows: https://www.python.org
```

### 2. 克隆项目

```bash
git clone https://github.com/peipeijiang/produce-product.git
cd produce-product
```

### 3. 一键安装依赖

```bash
chmod +x install.sh
./install.sh
```

这会安装：
- npm 依赖
- Playwright Chromium
- Python 依赖

### 4. 登录即梦AI（重要！）

首次使用需要登录即梦AI账号，session 会保存到浏览器：

```bash
cd Seedance2-Chrome-Extensions
npm run login
```

这会打开 Chrome，登录你的即梦账号后关闭浏览器。

### 5. ZAI 图片识别（可选）

ZAI 用于分析产品图片。确保 OpenClaw 已配置 ZAI key。

## 快速开始

### 步骤 1：启动 Mock Server

```bash
cd Seedance2-Chrome-Extensions
node mock-server.js &
```

### 步骤 2：启动 Chrome + 扩展

```bash
# 方式一：一键启动
chmod +x start-chrome.sh
./start-chrome.sh

# 方式二：手动启动
cd Seedance2-Chrome-Extensions
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
  await new Promise(() => {});
})();
"
```

启动后会：
1. 打开即梦AI页面
2. 加载 Seedance 扩展
3. 侧边面板自动展开，连接 Mock Server

### 步骤 3：准备产品

创建产品目录：

```
my-product/
└── products/
    ├── product1.jpg
    ├── product2.jpg
    └── ...
```

### 步骤 4：生成视频任务

```bash
python3 scripts/generate_tasks.py /path/to/my-product
```

这会：
1. 读取 products/ 目录的图片
2. 生成 3 个版本的任务 JSON
3. 保存到 `seedance_tasks_*.json`

### 步骤 5：推送任务

```bash
python3 scripts/push_tasks.py /path/to/my-product
```

任务会推送到 Mock Server，浏览器插件自动接收并执行。

## 目录结构

```
produce-product/
├── SKILL.md                    # OpenClaw Skill 说明
├── README.md                    # 本文件
├── install.sh                   # 一键安装脚本
├── start-chrome.sh              # 一键启动 Chrome
├── scripts/
│   ├── generate_tasks.py       # 生成视频任务
│   └── push_tasks.py           # 推送任务
└── Seedance2-Chrome-Extensions/
    ├── mock-server.js           # Mock 服务器
    ├── node_modules/           # npm 依赖
    └── playwright/              # 浏览器数据
```

## 常见问题

### Q: 浏览器没登录？
A: 运行 `npm run login` 重新登录

### Q: Mock Server 没启动？
A: `cd Seedance2-Chrome-Extensions && node mock-server.js &`

### Q: 扩展没加载？
A: 确保用 Playwright 启动浏览器（见步骤2）

### Q: ZAI key 怎么配置？
A: 在 OpenClaw 配置中添加 ZAI/智谱 API key

## 技术栈

- Node.js + npm
- Python 3.8+
- Playwright Chromium
- Seedance2 Chrome 扩展
- OpenClaw (ZAI 图片识别)

## 许可证

MIT
