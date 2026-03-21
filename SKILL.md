---
name: produce-product
description: 产品可剪辑素材视频制作。根据产品图片与可选 raw 实拍质感图，生成多版本 Seedance 生活化功能展示任务（英文 Prompt、9:16、15s、无配音、无字幕、无任何画面文字），画面统一为 TikTok 带货主播日常使用风格；优先用智谱 GLM-4.6V-FlashX 识别 `products/` 图片并生成结构化报告，再基于识别结果智能选图和设计 prompt。raw 用于质感还原主参考，keyframes 与图片识别结果仅用于功能和场景 idea。Prompt 除引用图片名外禁止出现中文。适用于用户要求批量生成后期可剪素材、强调真实生活化展示、并需要转换 base64 后提交到 Seedance Mock Gateway 的场景。
---

# 产品可剪辑素材视频制作 (produce-product)

## 概述

根据产品图片智能生成多版本功能展示任务（面向后期剪辑素材），并通过 Seedance Mock Gateway 批量投递。所有版本统一为生活化 TikTok 带货主播日常使用展示风格。

### 完整工作流程

```text
1. 环境准备 → 2. ZAI 图片识别 → 3. 生成任务 → 4. 转换 base64 → 5. 提交任务 → 6. 监控生成
```

---

## 步骤 1：环境准备

### 1.0 首次运行先安装依赖

```bash
cd /Users/shane/.codex/skills/produce-product
bash install.sh
```

- 首次运行，或 `scripts/start-chrome.sh` 提示依赖缺失时，先执行安装脚本。
- 若仅生成 JSON 而不启动浏览器扩展，可跳过 Playwright 启动，但提交到本地 Mock Gateway 前仍需保证服务已启动。

### 1.1 检查 Mock Server

```bash
curl -s http://localhost:3456/
```

应返回包含：
- `name: Seedance 任务 Mock API`
- 若无响应，后续生成与提交步骤都不要继续，必须先启动服务。

### 1.2 启动 Mock Server

```bash
cd /Users/shane/.codex/skills/produce-product/Seedance2-Chrome-Extensions
node mock-server.js &
```

- 每次跑 skill 时，都先做 `1.1` 和 `1.2`，确认 `3456` 端口可访问后再进行图片识别、生成任务、转换 base64、提交任务。

### 1.3 启动 Chrome + 扩展

```bash
cd /Users/shane/.codex/skills/produce-product
bash scripts/start-chrome.sh &
```

- 若出现 `依赖未安装，请先运行 install.sh`，回到步骤 `1.0`。

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

- 优先调用智谱清言图片识别模型 `GLM-4.6V-FlashX` 分析 `products/` 图片，并写入 `products/ZAI_full_analysis_report.md`。
- 推荐命令：

```bash
cd /Users/shane/.codex/skills/produce-product
ZHIPU_API_KEY=your_key python3 scripts/analyze_products_glm.py /path/to/project
```

- 若无报告且环境变量 `ZHIPU_API_KEY` 已设置，`scripts/generate_tasks.py` 会先自动尝试识别。
- 若识别失败，脚本会用默认信息继续，但优先使用真实识别报告。

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
- Prompt 除 `(@图片名)` 引用片段外，正文禁止出现中文。
- 不使用 Hook-Body-CTA。
- 不要配音，不要字幕，不要任何画面文字。
- 多版本时按识别结果和图片信息智能选图，确保场景设计与参考图用途一致，避免 `scene` 与 `scenario` 冲突。
- 多版本时优先覆盖识别结果中的不同功能侧面与场景侧面，避免版本内容同质化。
- 全部版本必须是生活化画面，不做棚拍广告风；画面语法贴近 TikTok 带货主播日常使用展示。
- 保持同一版本为同一场景、同一物理空间，但允许 2 到 4 个自然镜头切换，服务后期剪辑素材。
- 过滤识别噪声词（如纯数字、文件后缀、无语义 token），避免生成 `01`、`part`、`jpg` 这类无意义文案。
- 禁止为单个产品（如某一个戒指项目）做硬编码适配；规则必须保持跨品类通用。
- `modelConfig` 固定为：
  - `aspectRatio: 9:16`
  - `duration: 15s`

### 3.3 参考图职责规则（保留并增强）

- `raw/` 为空：不引用 raw 图片，保持原流程。
- `raw/` 非空：每个版本引用最多 3 张 raw 图片作为质感锚点。
- `keyframes/`：仅用于功能和场景 idea（构图与功能灵感）。
- `raw/`：用于材质与触感还原（表面、纹理、光泽、细节）且为最终视觉质感主参考。
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
6. 所有版本必须保持 TikTok 带货主播生活化表达：自然日常使用、弱广告腔、强真实感。
7. Prompt 文本必须英文可读、语义清晰；除图片引用名外不得包含中文或无意义噪声词。
8. 单个版本必须保持同一空间内的镜头覆盖，不允许跨空间跳场景，但允许同场景内多角度切换。
9. 任何优化都应以“通用抽取/通用过滤/通用生成”为原则，不允许绑定特定产品名或特定项目文件。

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
