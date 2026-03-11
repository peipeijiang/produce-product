---
name: produce-product
description: 产品营销视频制作。根据产品图片，智能设计营销视频版本。适用于电商展示、产品宣传。
version: 2.4.0
---

# 产品营销视频制作 (produce-product)

## 概述

根据产品图片，智能分析并生成营销视频任务。支持多版本自动化视频制作。

### 完整工作流程

```
1. 环境准备 → 2. ZAI 图片识别 → 3. 生成任务 → 4. 转换 base64 → 5. 提交任务 → 6. 监控生成
```

---

## 步骤 1：环境准备

### 1.1 检查 Mock Server

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

### 1.2 启动 Mock Server

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product/Seedance2-Chrome-Extensions
node mock-server.js &
```

### 1.3 启动 Chrome + 扩展（一键启动）

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product
bash start-chrome.sh &
```

这会自动：
- 启动 Chrome 浏览器
- 加载 Seedance 扩展
- 打开即梦网站 https://jimeng.jianying.com/ai-tool/image/generate

---

## 步骤 2：ZAI 图片识别

### 2.1 准备产品图片

```bash
# 项目目录结构
projects/PV-002-戒指_product/
├── products/
│   ├── *.jpg                  # 产品图片
│   └── ZAI_full_analysis_report.md  # ZAI 识别报告（自动生成）
└── keyframes/                 # 参考图（后续自动创建）
```

**重要：**
- 将产品图片放入 `products/` 目录
- 支持格式：.jpg, .jpeg, .png

### 2.2 使用 ZAI 识别产品

**方法 A：通过 MCP Server**

如果已配置 ZAI MCP Server，可以使用：

```bash
# 调用 ZAI 识别
mcp call zai-mcp-server__analyze_image --image /path/to/project/products/image.jpg
```

**方法 B：通过 OpenClaw 工具**

使用 `image` 工具分析产品图片：

```python
from openclaw import image

# 分析第一张图片
result = image.analyze(
    image="/path/to/project/products/image1.jpg",
    prompt="分析这个产品，识别产品名称、类型、颜色、功能等"
)

# 生成识别报告
with open("/path/to/project/products/ZAI_full_analysis_report.md", "w") as f:
    f.write(result)
```

**方法 C：通过对话**

发送产品图片到对话，并要求识别：

```
请识别这个产品，生成以下格式的分析报告：

## 产品基本信息

- 产品名称: [中文]
- 产品类型: [中文]
- 可选颜色: [列表]
- 核心功能: [列表]

## 图片分类汇总

| 文件 | 类型 | 颜色 | 场景/用途 |
|------|------|------|-----------|
```

然后将识别结果保存到 `products/ZAI_full_analysis_report.md`。

### 2.3 ZAI 报告格式示例

识别完成后，`ZAI_full_analysis_report.md` 应包含：

```markdown
# JELLY BELLES 智能戒指 - ZAI 图片识别报告

## 产品基本信息

- **产品名称**: JELLY BELLES 智能戒指
- **产品类型**: 智能穿戴设备 - 智能戒指
- **可选颜色**: 金色、黑色、银色 (3种配色)
- **可选尺寸**: 8、9、10、11、12 (5种尺寸)
- **电池续航**: 5-7天

## 图片分类汇总

| 文件 | 类型 | 颜色 | 场景/用途 |
|------|------|------|-----------|
| ring-01_part_01.jpg | 产品照片 | 黑/金 | 手部佩戴展示 |
| ring-01_part_03.jpg | 产品照片 | 金/银/黑 | 三色产品静物 |
| ring-01_part_15.jpg | 产品照片 | 金色 | 睡眠监测佩戴 |
```

---

## 步骤 3：生成任务 JSON

### 3.1 生成任务

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product

# 生成 5 个版本（默认）
python3 scripts/generate_tasks.py /Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-002-戒指_product

# 生成 3 个版本
python3 scripts/generate_tasks.py /Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-002-戒指_product 3
```

### 3.2 自动生成的内容

脚本会自动：
1. 解析 ZAI 报告（如果存在）
2. 翻译产品名称为英文
3. 选择不同的营销角度：
   - **V1_Premium_Luxury** - 奢华品质
   - **V2_Smart_Features** - 智能功能
   - **V3_Lifestyle_Daily** - 日常生活
   - **V4_Performance_Quality** - 性能质量
   - **V5_Best_Value** - 最佳价值

4. 每个版本按照 **Hook-Body-CTA 结构**生成 15s prompt：
   - **Hook (0-3s)**: 吸引注意力
   - **Body (3-12s)**: 展示功能和优势
   - **CTA (12-15s)**: 行动号召

5. 包含英文口播和字幕

### 3.3 生成的文件

```
seedance_tasks_V1_Premium_Luxury.json
seedance_tasks_V2_Smart_Features.json
seedance_tasks_V3_Lifestyle_Daily.json
seedance_tasks_V4_Performance_Quality.json
seedance_tasks_V5_Best_Value.json
```

---

## 步骤 4：转换为 base64 格式

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product
python3 convert_to_base64_fixed.py
```

这会将所有任务 JSON 中的 `referenceFiles` 从文件路径转换为 base64 编码格式。

---

## 步骤 5：提交任务到 Mock Server

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product
python3 submit_tasks.py
```

这会自动：
- 读取所有 `seedance_tasks_*.json` 文件
- 提交到 Mock Server API (`/api/tasks/push`)
- 显示提交结果

---

## 步骤 6：监控生成状态

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
| `scripts/generate_tasks.py` | 智能生成多版本任务 JSON（Hook-Body-CTA 结构）|
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

### 7. Prompt 结构：Hook-Body-CTA
- **Hook (0-3s)**: 吸引注意力，戏剧性开场
- **Body (3-12s)**: 展示功能和优势，真实使用场景
- **CTA (12-15s)**: 行动号召，强烈购买暗示
- ✅ 每个版本 15 秒
- ✅ 包含英文口播和字幕

### 8. ZAI 识别是必需步骤
- ✅ 在生成任务前必须先进行 ZAI 图片识别
- ✅ 识别报告用于翻译产品名、选择营销角度
- ✅ 如果没有 ZAI 报告，会使用默认信息

---

## 完整示例

### 示例：JELLY BELLES Smart Ring - 5 个版本视频

```bash
# 1. 环境准备
cd /Users/shane/.openclaw/workspace/skills/produce-product
bash start-chrome.sh &

# 2. ZAI 图片识别
# 通过对话发送产品图片，要求识别
# 识别结果保存到 products/ZAI_full_analysis_report.md

# 3. 生成任务 JSON（5 个版本）
python3 scripts/generate_tasks.py /Users/shane/Downloads/Micro-Drama-Skills-main/projects/PV-002-戒指_product

# 4. 转换为 base64
python3 convert_to_base64_fixed.py

# 5. 提交任务
python3 submit_tasks.py

# 6. 监控状态
curl -s http://localhost:3456/api/tasks | jq '.tasks[-5:]'
```

**自动生成的 5 个营销角度：**

1. **V1_Premium_Luxury** - 奢华品质（15 秒）
2. **V2_Smart_Features** - 智能功能（15 秒）
3. **V3_Lifestyle_Daily** - 日常生活（15 秒）
4. **V4_Performance_Quality** - 性能质量（15 秒）
5. **V5_Best_Value** - 最佳价值（15 秒）

**每个视频都包含：**
- ✅ Hook-Body-CTA 结构
- ✅ 英文口播 (English voiceover)
- ✅ 英文字幕 (English subtitles)
- ✅ 9:16 竖屏格式
- ✅ 15 秒时长

---

## 营销角度说明

脚本会自动选择以下营销角度：

| 版本 | 营销角度 | 重点 |
|------|---------|------|
| V1 | Premium Luxury | 高端品质、优雅设计 |
| V2 | Smart Features | 智能功能、创新技术 |
| V3 | Lifestyle Daily | 日常生活、无缝集成 |
| V4 | Performance Quality | 性能表现、可靠性 |
| V5 | Best Value | 性价比、超值优惠 |

如果用户有具体场景指示，脚本会根据指示生成。如果没有指示，默认使用以上角度。

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

# 如果不存在，脚本会自动从 products/ 复制
# 确保产品图片在 products/ 目录
```

### 问题 5：生成的版本不符合预期

```bash
# 重新生成指定数量的版本
python3 scripts/generate_tasks.py /path/to/project 3  # 生成 3 个版本
```

### 问题 6：ZAI 报告未生成

```bash
# 检查 products/ 目录
ls /path/to/project/products/

# 确保 ZAI 识别结果已保存
cat /path/to/project/products/ZAI_full_analysis_report.md
```

---

## 更新日志

### v2.4.0
- **修复：添加 ZAI 图片识别步骤**
  - 在"环境准备"和"生成任务"之间插入"ZAI 图片识别"
  - 完整工作流程：6 步
  - 添加 ZAI 识别方法和示例
  - 添加 ZAI 报告格式说明

### v2.3.0
- **重大更新：移除场景脚本依赖**
  - 简化工作流程：直接根据产品图片生成任务
  - 自动按照 Hook-Body-CTA 结构生成 15s prompt
  - 自动选择 5 个不同营销角度
  - 删除场景相关脚本（generate_ring_scenarios.py）
  - 更新文档，移除场景脚本说明

### v2.2.0
- 添加完整工作流程说明
- 新增场景脚本模板（已废弃）

### v2.1.1
- 添加重要规则说明（教训总结）

### v2.1.0
- 修复 prompt 中文问题
- 添加 seedance_submit.py
- 更新 SKILL.md
