---
name: produce-product
description: 产品可剪辑素材视频制作。根据产品图片与可选 raw 实拍质感图，生成多版本 Seedance 场景化功能展示任务（英文 Prompt、9:16、15s、无配音无字幕、可含 PPT 式文字说明），将参考图转 base64 并提交到 Mock Gateway。适用于用户要求批量生成后期可剪素材、强调 raw 质感还原与 keyframes 功能场景表达的场景。
---

# 产品可剪辑素材视频制作 (produce-product)

## 概述

根据产品图片智能生成多场景功能展示任务（面向后期剪辑素材），并通过 Seedance Mock Gateway 批量投递。

### 完整工作流程

```text
1. 环境准备 → 2. ZAI 图片识别 → 3. 生成任务 → 4. 转换 base64 → 5. 提交任务 → 6. 监控生成
```

---

## 步骤 1：环境准备

### 1.1 检查 Mock Server

```bash
curl -s http://localhost:3456/
```

应返回包含：
- `name: Seedance 任务 Mock API`

### 1.2 启动 Mock Server

```bash
cd /Users/shane/.codex/skills/produce-product/Seedance2-Chrome-Extensions
node mock-server.js &
```

### 1.3 启动 Chrome + 扩展

```bash
cd /Users/shane/.codex/skills/produce-product
bash scripts/start-chrome.sh &
```

---

## 步骤 2：ZAI 图片识别

### 2.1 项目目录约定

```text
/path/to/project/
├── products/
│   ├── *.jpg|*.jpeg|*.png
│   └── ZAI_full_analysis_report.md   # 可选
├── keyframes/                        # 必需
└── raw/                              # 可选：实拍质感参考图（材质/触感/表面）
```

### 2.2 识别要求

- 先识别产品信息并写入 `products/ZAI_full_analysis_report.md`。
- 若无报告，脚本会用默认信息继续，但优先使用报告。

建议识别输出至少包含：
- 产品名称
- 产品类型
- 核心功能
- 图片用途概览

---

## 步骤 3：生成任务 JSON

### 3.1 生成命令

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/generate_tasks.py /path/to/project 10
```

- 第二个参数是版本数，按用户要求传入。
- 输出文件：`seedance_tasks_V*.json`。

### 3.2 生成规则

- Prompt 必须英文。
- 不使用 Hook-Body-CTA。
- 不要配音，不要字幕。
- 允许简洁的 PPT 式英文画面文字（overlay text）。
- 多版本时按识别结果和图片信息智能选图，输出不同场景下的功能展示。
- 多版本时优先覆盖识别结果中的不同功能侧面与场景侧面，避免版本内容同质化。
- `modelConfig` 固定为：
  - `aspectRatio: 9:16`
  - `duration: 15s`

### 3.3 参考图职责规则（保留并增强）

- `raw/` 为空：不引用 raw 图片，保持原流程。
- `raw/` 非空：每个版本引用最多 3 张 raw 图片作为质感锚点。
- `keyframes/`：用于功能与场景表达（构图、动作、使用上下文）。
- `raw/`：用于材质与触感还原（表面、纹理、光泽、细节）。
- Prompt 中必须：
  - 引用 keyframes 与 raw 图片（`(@xxx.jpg)`）
  - 明确区分 keyframes 与 raw 的用途优先级

---

## 步骤 4：转换为 base64

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/convert_to_base64_fixed.py /path/to/project
```

要求：
- 提交前 `referenceFiles` 必须是 base64 对象，不能是路径字符串。

---

## 步骤 5：提交任务到 Mock Server

```bash
cd /Users/shane/.codex/skills/produce-product
python3 scripts/submit_tasks.py /path/to/project
```

要求：
- 提交 payload 必须保留 `modelConfig`。
- 若丢失 `modelConfig`，扩展会回退默认值（`16:9 / 5s`）。

---

## 步骤 6：监控生成状态

```bash
curl -s http://localhost:3456/api/tasks | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Total:', d.get('total', 0))
for t in d.get('tasks', [])[-10:]:
    print(t.get('taskCode'), t.get('status'))
"
```

常见状态：
- `pending`
- `acked`
- `configuring`
- `generating`
- `completed`
- `failed`

---

## 核心脚本

- `scripts/generate_tasks.py`：生成多版本场景化任务（智能选图 + raw 质感引用逻辑）
- `scripts/convert_to_base64_fixed.py`：转换 `referenceFiles` 为 base64
- `scripts/submit_tasks.py`：批量提交任务到 `/api/tasks/push`
- `scripts/start-chrome.sh`：启动浏览器与扩展

---

## 重要规则

1. 按用户要求生成与提交指定数量版本，不自动增减。
2. 未经用户明确要求，不删除项目中的任务文件。
3. 发现参数异常（比如 5s、16:9）时，先修脚本再重跑，不手改大量 JSON。
4. 核心目标是产出高可剪辑素材：镜头模块化、场景差异化、便于后期拼接。
5. 当用户要求多个版本时，必须尽量提高版本多样性（功能重点、场景表达、选图组合、镜头风格）。

---

## 故障排查

### 1) 网关不可用

```bash
curl -s http://localhost:3456/
```

无响应就重启 `mock-server.js`。

### 2) 一直 `pending`

- 检查 `GET /` 里的 `sseClients` 是否大于 0。
- 若为 0，说明扩展未连接，重启 `scripts/start-chrome.sh` 并确认扩展在线。

### 3) 结果变成 `16:9 / 5s`

- 检查 `scripts/submit_tasks.py` 是否把 `modelConfig` 一并提交。
- 检查任务 JSON 是否为 `9:16 / 15s`。

### 4) 引用图缺失

- 检查 `keyframes/`、`raw/` 文件是否存在。
- 重新执行 `scripts/convert_to_base64_fixed.py /path/to/project`。
