# produce-product

产品可剪辑素材视频自动化工具。

## 功能

- 根据 `keyframes/` 与可选 `raw/` 自动生成多版本 15s 场景化功能展示任务
- 多版本按图片与识别结果智能选图，覆盖不同使用场景
- Prompt 为英文，`9:16`、`15s`
- 默认无配音、无字幕，可包含简洁 PPT 式画面文字说明
- 批量转 base64 并提交到 Seedance Mock Gateway

## 快速开始

### 1. 启动 Mock Server

```bash
cd Seedance2-Chrome-Extensions
node mock-server.js &
```

### 2. 启动 Chrome + 扩展

```bash
cd /Users/shane/.codex/skills/produce-product
bash scripts/start-chrome.sh &
```

### 3. 准备项目目录

```text
/path/to/project/
├── products/
│   └── ZAI_full_analysis_report.md   # 可选
├── keyframes/                        # 必需：功能和场景参考
└── raw/                              # 可选：质感和材质参考
```

### 4. 生成多版本任务

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/generate_tasks.py /path/to/project 10
```

### 5. 转换引用图为 base64

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/convert_to_base64_fixed.py /path/to/project
```

### 6. 提交任务

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/submit_tasks.py /path/to/project
```

## 关键约束

- `keyframes/` 优先表达功能与场景。
- `raw/` 优先表达材质、表面和触感。
- 目标是产出高可剪辑素材：镜头模块化、场景差异化、便于后期拼接。
- 不生成配音与字幕。

## 主要脚本

- `scripts/generate_tasks.py`：生成多版本场景化任务
- `scripts/convert_to_base64_fixed.py`：将 `referenceFiles` 转成 base64
- `scripts/submit_tasks.py`：提交任务到 `/api/tasks/push`
- `scripts/start-chrome.sh`：启动浏览器与扩展
