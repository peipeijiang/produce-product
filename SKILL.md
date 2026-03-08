---
name: produce-product
description: 产品营销视频制作。根据产品图片，智能设计 3-5 个版本的 15s 营销视频。适用于电商展示、产品宣传。
version: 2.0.0
---

# 产品营销视频制作 (produce-product)

## 概述

根据产品图片，智能分析并生成营销视频任务。

### 工作流程

```
检查环境 → 用户发产品图片 → ZAI 识别图片 → 生成 3-5 个版本 → 推送任务 → 浏览器自动生成
```

---

## 环境检查

### 1. 检查 Mock Server

```bash
curl -s http://localhost:3456/api/config | jq '.success'
```

返回 `true` 表示运行中

### 2. 检查/启动 Mock Server（如未运行）

```bash
cd Seedance2-Chrome-Extensions
node mock-server.js &
```

### 3. 检查/启动 Chrome + 扩展

Chrome 必须通过以下方式启动（带扩展）：

```bash
cd Seedance2-Chrome-Extensions

# 方式一：使用 Playwright
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
  console.log('Page loaded. Browser running...');
  await new Promise(() => {});
})();
"
```

启动后会：
1. 打开即梦AI页面
2. 自动连接 Mock Server (localhost:3456)
3. 侧边面板自动展开，接收任务

---

## 使用方法

### 1. 准备产品图片

```
项目目录/
├── products/              # 产品图片
│   ├── *.jpg
│   └── ZAI_full_analysis_report.md  # 可选
└── keyframes/           # 精选参考图（自动复制）
```

### 2. 运行脚本

```bash
cd scripts
python3 generate_tasks.py /path/to/project
python3 push_tasks.py /path/to/project
```

---

## 核心脚本

| 脚本 | 功能 |
|------|------|
| `generate_tasks.py` | 智能生成营销视频任务 |
| `push_tasks.py` | 推送任务到 Mock Server |

---

## 注意事项

1. **必须用 Playwright 启动 Chrome**：不能用普通的 Chrome，必须加载扩展
2. **prompt 和 referenceFiles 必须一致**：生成的 JSON 中 prompt 引用的图片必须在 referenceFiles 中
3. **视频时长**：默认 15 秒，9:16 竖屏
