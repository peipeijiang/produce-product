# produce-product

[English](./README.md) | [简体中文](./README.zh-CN.md)

`produce-product` 是一个 Codex skill，用于把产品图片转换成适合短视频电商场景的多版本 Seedance 可剪辑任务。

## 功能概览

这个 skill 适合以下工作流：

- 生成多个 `15s`、`9:16` 版本
- 使用英文 Prompt
- 无配音、无字幕、无画面文字
- 生活化、TikTok 风格的真实日常使用场景
- 可选的 `GLM-4.6V-FlashX` 产品图识别
- base64 转换与本地 Seedance mock gateway 批量提交

给定一个产品项目目录后，这个 skill 可以：

1. 分析 `products/` 图片并生成 `ZAI_full_analysis_report.md`
2. 生成多个 `seedance_tasks_V*.json` 任务文件
3. 将 `referenceFiles` 转换成 base64 对象
4. 提交任务到本地 Seedance mock server
5. 监控 `pending`、`acked`、`configuring`、`generating`、`completed` 等状态

## 目录结构

```text
produce-product/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── agents/
│   └── openai.yaml
├── scripts/
│   ├── analyze_products_glm.py
│   ├── generate_tasks.py
│   ├── convert_to_base64_fixed.py
│   ├── submit_tasks.py
│   └── start-chrome.sh
├── Seedance2-Chrome-Extensions/
│   ├── mock-server.js
│   └── ...
└── install.sh
```

期望的输入项目结构：

```text
/path/to/project/
├── products/
│   ├── *.jpg|*.jpeg|*.png
│   └── ZAI_full_analysis_report.md
├── keyframes/
└── raw/
```

## 快速开始

### 1. 安装依赖

```bash
cd /Users/shane/.codex/skills/produce-product
bash install.sh
```

### 2. 启动本地 mock server

```bash
cd /Users/shane/.codex/skills/produce-product/Seedance2-Chrome-Extensions
node mock-server.js
```

### 3. 可选：启动带扩展的 Chrome

```bash
cd /Users/shane/.codex/skills/produce-product
bash scripts/start-chrome.sh
```

### 4. 分析产品图片

```bash
cd /Users/shane/.codex/skills/produce-product
ZHIPU_API_KEY=your_key python3 scripts/analyze_products_glm.py /path/to/project
```

### 5. 生成任务 JSON

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/generate_tasks.py /path/to/project 5
```

### 6. 转换引用图为 base64

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/convert_to_base64_fixed.py /path/to/project
```

### 7. 提交任务

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/submit_tasks.py /path/to/project
```

## 输出规则

- Prompt 正文保持英文。
- 允许 `(@image.jpg)` 这类图片引用标记。
- 每个版本保持单一物理空间。
- 只允许同场景内的自然镜头切换。
- 保留 `modelConfig`，其中 `aspectRatio: 9:16`、`duration: 15s`。
- 优先生活化、达人口播感、日常使用场景，不做棚拍广告风。

## 说明

- 面向 Codex 的完整操作说明在 [SKILL.md](./SKILL.md)。
- 这个 `README.zh-CN.md` 主要给 GitHub 访客和协作者阅读。
