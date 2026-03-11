---
name: produce-product
description: 产品营销视频制作。根据产品图片，智能设计营销视频版本。适用于电商展示、产品宣传。
version: 2.2.0
---

# 产品营销视频制作 (produce-product)

## 概述

根据产品图片，智能分析并生成营销视频任务。支持多场景、多版本的自动化视频制作。

### 完整工作流程

```
1. 环境准备 → 2. 场景设计 → 3. 生成任务 → 4. 转换 base64 → 5. 提交任务 → 6. 监控生成
```

---

## 环境准备

### 1. 检查 Mock Server

```bash
# 检查 Mock Server 是否运行
curl -s http://localhost:3456/
```

应返回：
```json
{
  "name": "Seedance 任务 Mock API",
  "version": "3.2.0"
}
```

### 2. 启动 Mock Server

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product/Seedance2-Chrome-Extensions
node mock-server.js &
```

### 3. 启动 Chrome + 扩展（一键启动）

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product
bash start-chrome.sh &
```

这会自动：
- 启动 Chrome 浏览器
- 加载 Seedance 扩展
- 打开即梦网站 https://jimeng.jianying.com/ai-tool/image/generate

---

## 使用方法

### 方式一：快速开始（使用场景脚本）

#### 步骤 1：准备产品目录

```bash
# 项目目录结构
projects/PV-002-戒指_product/
├── products/
│   ├── *.jpg                  # 产品图片
│   └── ZAI_full_analysis_report.md
├── keyframes/                 # 参考图（自动创建）
└── scenarios/                 # 场景描述（可选）
    ├── v1-sleep-health.md
    ├── v2-fitness-athlete.md
    ├── v3-gesture-control.md
    ├── v4-health-tracker.md
    └── v5-waterproof-life.md
```

#### 步骤 2：准备场景脚本

为每个使用场景创建 Markdown 文件（可选，但推荐）：

```markdown
# Scenario 1: Sleep Health Monitoring

## Video Config
- **Duration**: 10s
- **Aspect Ratio**: 9:16
- **Model**: Seedance 2.0 Fast
- **Language**: English

## Scene Breakdown
- Scene 1 (0-3s): [描述]
- Scene 2 (3-7s): [描述]
- Scene 3 (7-10s): [描述]

## Voiceover Script
"完整的英文口播脚本..."

## Subtitles
```
字幕文本1
字幕文本2
```

## Reference Images
- image1.jpg (场景描述)
- image2.jpg (场景描述)
- image3.jpg (场景描述)
```

#### 步骤 3：生成任务 JSON

**方法 A：使用通用脚本（推荐）**

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product

# 使用场景脚本生成任务
python3 generate_ring_scenarios_fixed.py
```

这会生成 5 个场景的任务 JSON：
- `seedance_tasks_V1_SLEEP.json`
- `seedance_tasks_V2_FITNESS.json`
- `seedance_tasks_V3_GESTURE.json`
- `seedance_tasks_V4_HEALTH.json`
- `seedance_tasks_V5_WATERPROOF.json`

**方法 B：使用通用脚本**

```bash
# 生成 N 个版本
python3 scripts/generate_tasks.py /path/to/project 5
```

#### 步骤 4：转换为 base64 格式

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product
python3 convert_to_base64_fixed.py
```

这会将所有任务 JSON 中的 `referenceFiles` 从文件路径转换为 base64 编码格式。

#### 步骤 5：提交任务到 Mock Server

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product
python3 submit_tasks.py
```

这会自动：
- 读取所有 `seedance_tasks_V*.json` 文件
- 提交到 Mock Server API (`/api/tasks/push`)
- 显示提交结果

#### 步骤 6：监控生成状态

```bash
# 查看所有任务
curl -s http://localhost:3456/api/tasks | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(f'Total: {d[\"total\"]}')
for task in d['tasks'][-5:]:
    print(f\"  {task['taskCode']}: {task['status']}\")
"
```

任务状态：
- `pending` - 等待处理
- `acked` - 已被扩展接收
- `configuring` - 配置中
- `generating` - 生成中
- `completed` - 已完成
- `failed` - 失败

---

## 核心脚本

| 脚本 | 功能 |
|------|------|
| `start-chrome.sh` | 一键启动 Chrome + Seedance 扩展 |
| `generate_ring_scenarios_fixed.py` | 根据场景脚本生成任务 JSON |
| `convert_to_base64_fixed.py` | 转换 referenceFiles 为 base64 |
| `submit_tasks.py` | 批量提交任务到 Mock Server |

---

## ⚠️ 重要规则（教训总结）

### 1. Prompt 必须是英文
- ❌ 不能出现任何中文（包括产品名）
- ✅ 所有中文产品名需转换为英文
- ✅ 口播脚本和字幕必须是英文

### 2. Reference Mode 保持中文
- ✅ `"referenceMode": "全能参考"` 可以是中文

### 3. 严格按用户指令生成版本数
- 用户说生成几个就生成几个
- 不自动生成更多版本

### 4. 提交前确认用户意图
- 用户说提交几个就提交几个
- 不自动提交所有版本

### 5. Reference Files 必须是 base64 对象
- ❌ 不能是文件路径（如 `"keyframes/image.jpg"`）
- ✅ 必须是 base64 编码的对象：
  ```json
  {
    "fileName": "image.jpg",
    "base64": "/9j/4AAQSkZJRgABAQ..."
  }
  ```

### 6. 图片文件必须存在
- 确保 `keyframes/` 目录中包含所有引用的图片
- 使用 `ls keyframes/` 检查可用图片

### 7. 确保场景描述完整
- 每个场景应包含：场景分解、口播脚本、字幕、参考图片
- Prompt 应明确要求英文口播和字幕

---

## 完整示例

### 示例：JELLY BELLES Smart Ring - 5 个场景视频

```bash
# 1. 环境准备
cd /Users/shane/.openclaw/workspace/skills/produce-product
bash start-chrome.sh &

# 2. 生成任务 JSON
python3 generate_ring_scenarios_fixed.py

# 3. 转换为 base64
python3 convert_to_base64_fixed.py

# 4. 提交任务
python3 submit_tasks.py

# 5. 监控状态
curl -s http://localhost:3456/api/tasks | jq '.tasks[-5:]'
```

**生成的 5 个场景：**

1. **V1_SLEEP** - 睡眠健康监测（10 秒）
2. **V2_FITNESS** - 健身运动员伴侣（10 秒）
3. **V3_GESTURE** - 智能手势控制（10 秒）
4. **V4_HEALTH** - 实时健康追踪（10 秒）
5. **V5_WATERPROOF** - 防水生活（10 秒）

---

## 管理页面

- **Mock Server 管理页**：http://localhost:3456/admin
- **即梦网站**：https://jimeng.jianying.com/ai-tool/image/generate

---

## 故障排查

### 问题 1：Mock Server 无法连接

```bash
# 检查 Mock Server 是否运行
curl http://localhost:3456/

# 重新启动
cd /Users/shane/.openclaw/workspace/skills/produce-product/Seedance2-Chrome-Extensions
node mock-server.js &
```

### 问题 2：Chrome 扩展未连接

```bash
# 检查 SSE 连接数
curl -s http://localhost:3456/ | jq '.sseClients'

# 重启 Chrome
bash start-chrome.sh &
```

### 问题 3：任务一直 pending

```bash
# 检查任务状态
curl http://localhost:3456/api/tasks | jq '.tasks[-1]'

# 检查 SSE 客户端
curl http://localhost:3456/ | jq '.sseClients'
```

### 问题 4：图片文件不存在

```bash
# 检查 keyframes 目录
ls /path/to/project/keyframes/

# 复制图片到 keyframes
cp /path/to/source/*.jpg /path/to/project/keyframes/
```

---

## 更新日志

### v2.2.0
- 添加完整工作流程说明
- 新增 `generate_ring_scenarios_fixed.py` 脚本
- 新增 `convert_to_base64_fixed.py` 脚本
- 新增 `submit_tasks.py` 脚本
- 更新环境准备步骤
- 添加场景脚本模板

### v2.1.1
- 添加重要规则说明（教训总结）

### v2.1.0
- 修复 prompt 中文问题
- 添加 seedance_submit.py
- 更新 SKILL.md
