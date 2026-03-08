---
name: produce-product
description: 产品营销视频制作。根据产品图片，智能设计营销视频版本。适用于电商展示、产品宣传。
version: 2.1.0
---

# 产品营销视频制作 (produce-product)

## 概述

根据产品图片，智能分析并生成营销视频任务。

### 工作流程

```
检查环境 → 用户发产品图片 → ZAI 识别图片 → 生成 N 个版本 → 用户选择提交 → seedance_submit.py 提交
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

```bash
cd Seedance2-Chrome-Extensions

# 使用 Playwright 启动
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

---

## 使用方法

### 1. 准备产品图片

```
项目目录/
├── products/              # 产品图片
│   ├── *.jpg
│   └── ZAI_full_analysis_report.md  # 可选
└── keyframes/             # 参考图（复制产品图到这里）
```

### 2. 生成任务 JSON

```bash
cd scripts
python3 generate_tasks.py /path/to/project        # 默认 5 个版本
python3 generate_tasks.py /path/to/project 3     # 指定 3 个版本
```

### 3. 提交任务

**方式一：使用 seedance_submit.py（推荐）**

```bash
# 模拟提交（不真实生成）
python3 seedance_submit.py /path/to/project

# 真实提交
python3 seedance_submit.py /path/to/project --real
```

**方式二：手动提交**

如果手动提交，必须遵守：
- **prompt 必须是英文**
- **referenceFiles 必须是 base64 格式对象**

---

## 核心脚本

| 脚本 | 功能 |
|------|------|
| `generate_tasks.py` | 智能生成营销视频任务 JSON |
| `seedance_submit.py` | 提交任务到 Mock Server |
| `push_tasks.py` | 旧版推送脚本（已废弃） |

---

## 重要规则

1. **prompt 不能有中文** - 必须使用英文
2. **referenceFiles 必须是 base64 对象** - 不能是文件路径
3. **严格按用户指令生成版本数** - 用户说生成几个就几个
4. **用户选择提交哪个** - 不自动提交所有版本

---

## 示例

```bash
# 生成 3 个版本（不提交）
python3 generate_tasks.py ~/my-product 3

# 生成 5 个版本，然后手动提交 1 个
python3 generate_tasks.py ~/my-product 5
# 用户选择 V2，编辑 JSON 后手动提交
```

---

## 注意事项

1. **视频时长**：默认 15 秒，9:16 竖屏
2. **必须用 Playwright 启动 Chrome**：不能用普通的 Chrome
3. **prompt 和 referenceFiles 必须一致**
