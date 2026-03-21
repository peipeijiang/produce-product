# produce-product

[English](./README.md) | [简体中文](./README.zh-CN.md)

`produce-product` is a Codex skill for turning product images into multiple Seedance-ready editable video tasks for short-form commerce content.

## What It Does

This skill is designed for workflows that need:

- multiple `15s` `9:16` variants
- English prompts
- no voiceover, no subtitles, and no on-screen text
- realistic TikTok-style daily-use scenes
- optional product analysis with `GLM-4.6V-FlashX`
- base64 conversion and batch submission to a local Seedance mock gateway

Given a project folder, the skill can:

1. Analyze `products/` images and generate `ZAI_full_analysis_report.md`
2. Generate multiple `seedance_tasks_V*.json` task files
3. Convert `referenceFiles` into base64 objects
4. Submit tasks to the local Seedance mock server
5. Monitor states such as `pending`, `acked`, `configuring`, `generating`, and `completed`

## Project Layout

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

Expected input project structure:

```text
/path/to/project/
├── products/
│   ├── *.jpg|*.jpeg|*.png
│   └── ZAI_full_analysis_report.md
├── keyframes/
└── raw/
```

## Quick Start

### 1. Install dependencies

```bash
cd /Users/shane/.codex/skills/produce-product
bash install.sh
```

### 2. Start the local mock server

```bash
cd /Users/shane/.codex/skills/produce-product/Seedance2-Chrome-Extensions
node mock-server.js
```

### 3. Optionally start Chrome with the extension

```bash
cd /Users/shane/.codex/skills/produce-product
bash scripts/start-chrome.sh
```

### 4. Analyze product images

```bash
cd /Users/shane/.codex/skills/produce-product
ZHIPU_API_KEY=your_key python3 scripts/analyze_products_glm.py /path/to/project
```

### 5. Generate task JSON files

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/generate_tasks.py /path/to/project 5
```

### 6. Convert references to base64

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/convert_to_base64_fixed.py /path/to/project
```

### 7. Submit tasks

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/submit_tasks.py /path/to/project
```

## Output Rules

- Keep the prompt body in English.
- Allow image reference tags such as `(@image.jpg)`.
- Keep each version in one physical setting.
- Allow only natural same-scene angle changes.
- Preserve `modelConfig` with `aspectRatio: 9:16` and `duration: 15s`.
- Prefer lifestyle, creator-style, daily-use scenes over polished studio ads.

## Notes

- Full Codex-facing operational instructions live in [SKILL.md](./SKILL.md).
- This `README.md` is primarily for GitHub visitors and collaborators.
