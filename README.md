# produce-product

`produce-product` 是一个 Codex skill，用于把产品图片转换成适合短视频电商场景的多版本 Seedance 可剪辑任务。

`produce-product` is a Codex skill for turning product images into multiple Seedance-ready editable video tasks for short-form commerce content.

## 功能概览 | What It Does

适合以下工作流：

This skill is designed for workflows that need:

- 多个 `15s`、`9:16` 版本
- multiple `15s` `9:16` variants
- 英文 Prompt
- English prompts
- 无配音、无字幕、无画面文字
- no voiceover, no subtitles, and no on-screen text
- 生活化、TikTok 风格的真实日常使用场景
- realistic TikTok-style daily-use scenes
- 可选的 `GLM-4.6V-FlashX` 产品图识别
- optional product analysis with `GLM-4.6V-FlashX`
- base64 转换与本地 Seedance mock gateway 批量提交
- base64 conversion and batch submission to a local Seedance mock gateway

给定一个产品项目目录后，这个 skill 可以：

Given a project folder, the skill can:

1. 分析 `products/` 图片并生成 `ZAI_full_analysis_report.md`
2. Analyze `products/` images and generate `ZAI_full_analysis_report.md`
3. 生成多个 `seedance_tasks_V*.json` 任务文件
4. Generate multiple `seedance_tasks_V*.json` task files
5. 将 `referenceFiles` 转换成 base64 对象
6. Convert `referenceFiles` into base64 objects
7. 提交任务到本地 Seedance mock server
8. Submit tasks to the local Seedance mock server
9. 监控 `pending`、`acked`、`configuring`、`generating`、`completed` 等状态
10. Monitor states such as `pending`, `acked`, `configuring`, `generating`, and `completed`

## 目录结构 | Project Layout

```text
produce-product/
├── SKILL.md
├── README.md
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

Expected input project structure:

```text
/path/to/project/
├── products/
│   ├── *.jpg|*.jpeg|*.png
│   └── ZAI_full_analysis_report.md
├── keyframes/
└── raw/
```

## 快速开始 | Quick Start

### 1. 安装依赖 | Install dependencies

```bash
cd /Users/shane/.codex/skills/produce-product
bash install.sh
```

### 2. 启动本地 mock server | Start the local mock server

```bash
cd /Users/shane/.codex/skills/produce-product/Seedance2-Chrome-Extensions
node mock-server.js
```

### 3. 可选：启动带扩展的 Chrome | Optionally start Chrome with the extension

```bash
cd /Users/shane/.codex/skills/produce-product
bash scripts/start-chrome.sh
```

### 4. 分析产品图片 | Analyze product images

```bash
cd /Users/shane/.codex/skills/produce-product
ZHIPU_API_KEY=your_key python3 scripts/analyze_products_glm.py /path/to/project
```

### 5. 生成任务 JSON | Generate task JSON files

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/generate_tasks.py /path/to/project 5
```

### 6. 转换引用图为 base64 | Convert references to base64

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/convert_to_base64_fixed.py /path/to/project
```

### 7. 提交任务 | Submit tasks

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/submit_tasks.py /path/to/project
```

## 输出规则 | Output Rules

- Prompt 正文保持英文。
- Keep the prompt body in English.
- 允许 `(@image.jpg)` 这类图片引用标记。
- Allow image reference tags such as `(@image.jpg)`.
- 每个版本保持单一物理空间。
- Keep each version in one physical setting.
- 只允许同场景内的自然镜头切换。
- Allow only natural same-scene angle changes.
- 保留 `modelConfig`，其中 `aspectRatio: 9:16`、`duration: 15s`。
- Preserve `modelConfig` with `aspectRatio: 9:16` and `duration: 15s`.
- 优先生活化、达人口播感、日常使用场景，不做棚拍广告风。
- Prefer lifestyle, creator-style, daily-use scenes over polished studio ads.

## 说明 | Notes

- 面向 Codex 的完整操作说明在 [SKILL.md](./SKILL.md)。
- Full Codex-facing operational instructions live in [SKILL.md](./SKILL.md).
- 这个 `README.md` 主要给 GitHub 访客和协作者阅读。
- This `README.md` is primarily for GitHub visitors and collaborators.
