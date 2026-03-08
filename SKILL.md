---
name: produce-product
description: 产品营销视频制作。根据产品图片，智能设计营销视频版本。适用于电商展示、产品宣传。
version: 2.1.1
---

# 产品营销视频制作 (produce-product)

## 概述

根据产品图片，智能分析并生成营销视频任务。

### 工作流程

```
检查环境 → 用户发产品图片 → ZAI 识别图片 → 生成 N 个版本 → 用户选择提交 → 提交
```

---

## 环境检查

### 1. 检查 Mock Server

```bash
curl -s http://localhost:3456/api/config | jq '.success'
```

### 2. 启动 Mock Server

```bash
cd Seedance2-Chrome-Extensions
node mock-server.js &
```

### 3. 启动 Chrome + 扩展

```bash
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

---

## 使用方法

### 1. 准备产品图片

```
项目目录/
├── products/              # 产品图片
│   ├── *.jpg
│   └── ZAI_full_analysis_report.md
└── keyframes/             # 参考图
```

### 2. 生成任务 JSON

```bash
python3 scripts/generate_tasks.py /path/to/project 5
```

### 3. 提交任务

**手动提交（推荐）：**

```bash
python3 scripts/seedance_submit.py /path/to/project --real
```

---

## 核心脚本

| 脚本 | 功能 |
|------|------|
| `generate_tasks.py` | 生成营销视频任务 JSON |
| `seedance_submit.py` | 提交任务到 Mock Server |

---

## ⚠️ 重要规则（教训总结）

1. **prompt 必须是英文**
   - ❌ 不能出现任何中文（包括产品名）
   - ✅ 所有中文产品名需转换为英文

2. **referenceMode 保持中文**
   - ✅ "全能参考" 可以是中文

3. **严格按用户指令生成版本数**
   - 用户说生成几个就生成几个
   - 不自动生成更多

4. **提交前确认用户意图**
   - 用户说提交几个就提交几个
   - 不自动提交所有

5. **referenceFiles 必须是 base64 对象**
   - ❌ 不能是文件路径
   - ✅ 必须是 base64 编码的对象

---

## 示例

```bash
# 生成 3 个版本
python3 generate_tasks.py ~/my-product 3

# 真实提交
python3 seedance_submit.py ~/my-product --real
```

---

## 更新日志

### v2.1.1
- 添加重要规则说明（教训总结）

### v2.1.0
- 修复 prompt 中文问题
- 添加 seedance_submit.py
- 更新 SKILL.md
