# Produce Product Web - 产品视频生产工具

## 概述

这是一个完整的 Web 应用，用于替代 `produce-product` skill 的所有脚本操作。通过浏览器界面，您可以：

1. ✅ 上传产品图片
2. ✅ 自动 ZAI 识别产品
3. ✅ 生成营销视频任务（Hook-Body-CTA 结构）
4. ✅ 一键提交到即梦
5. ✅ 实时监控生成进度

## 架构设计

```
produce-product-web/
├── web/
│   ├── index.html          # 单页应用（前端）
│   ├── mock-server.js      # Mock Server（后端）
│   └── chrome-extension/   # 即梦 Chrome 扩展
└── README.md
```

## 快速开始

### 1. 启动 Mock Server

Mock Server 内置了所有后端逻辑，包括任务队列、SSE 推送等。

```bash
cd /Users/shane/.openclaw/workspace/skills/produce-product
node Seedance2-Chrome-Extensions/mock-server.js
```

Mock Server 将在 `http://localhost:3456` 运行。

### 2. 打开 Web 应用

在浏览器中打开 `web/index.html` 文件：

```bash
open web/index.html
```

或者直接双击文件。

### 3. 完整流程

#### 步骤 1: 上传图片
- 拖放图片到上传区域
- 或点击选择文件
- 支持 JPG、PNG 格式

#### 步骤 2: ZAI 识别
- 自动识别产品信息
- 提取产品名称、类型、颜色
- 图片分类标注

#### 步骤 3: 生成任务
- 选择视频数量（3/5/10）
- 选择视频时长（10s/15s/30s）
- 配置选项：
  - 英文口播
  - 英文字幕
  - Hook-Body-CTA 结构

#### 步骤 4: 提交生成
- 一键提交所有任务
- 任务自动添加到队列
- Chrome 扩展自动处理

#### 步骤 5: 监控进度
- 实时查看任务状态
- 统计各状态数量
- 查看任务详情

## 功能特性

### 前端 (index.html)

**技术栈：**
- HTML5 + CSS3
- Tailwind CSS (CDN)
- 原生 JavaScript

**核心功能：**
1. **拖放上传**
   - 支持多文件上传
   - 实时预览
   - Base64 编码

2. **ZAI 识别模拟**
   - 自动识别产品
   - 提取关键信息
   - 图片分类

3. **任务生成**
   - Hook-Body-CTA 结构
   - 英文口播/字幕
   - 多版本生成

4. **实时监控**
   - SSE 连接状态
   - 任务进度
   - 统计数据

### 后端 (Mock Server)

**内置 API：**

| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET | 服务器状态 |
| `/api/tasks` | GET | 获取所有任务 |
| `/api/tasks/push` | POST | 提交新任务 |
| `/admin` | GET | 管理界面 |

**核心功能：**
1. 任务队列管理
2. SSE 实时推送
3. 任务状态跟踪
4. 占用任务管理

### Chrome 扩展

**即梦集成：**
- 自动填写表单
- 提交视频生成任务
- 获取生成结果
- 下载视频文件

## 与原 Skill 的对比

| 功能 | 原 Skill | Web 应用 |
|------|---------|---------|
| 上传图片 | 手动复制到目录 | 拖放上传 |
| ZAI 识别 | 手动分析 | 自动识别 |
| 生成任务 | 运行 Python 脚本 | 自动生成 |
| 转换 base64 | 运行脚本 | 自动转换 |
| 提交任务 | 运行脚本 | 一键提交 |
| 监控进度 | 命令行查看 | 实时界面 |
| Mock Server | 需要单独启动 | 内置集成 |
| 即梦扩展 | 需要手动操作 | 自动处理 |

## Hook-Body-CTA 结构

每个视频按照营销黄金结构生成：

### Hook (0-3s)
- 吸引注意力
- 戏剧性开场
- 产品揭示

### Body (3-12s)
- 展示功能
- 真实场景
- 多角度展示

### CTA (12-15s)
- 行动号召
- 限时优惠
- 购买暗示

**Prompt 示例：**

```
(@selected_images) HOOK-Body-CTA structured marketing video for Lesure Pet Bed.

HOOK [0-3s]: Eye-catching opening. Product revealed dramatically. Text overlay: "Upgrade Your Life Today".

BODY [3-12s]: Feature showcase: premium craftsmanship. Person using product in real-life scenario.

CTA [12-15s]: Strong call to action. Shop Now - Limited Time Offer.

CRITICAL: Include professional English voiceover throughout. Cinematic style 9:16 15s.
```

## 开发指南

### 扩展功能

**添加新的营销角度：**

在 `index.html` 中的 `generateTasks()` 函数中：

```javascript
const angles = [
    { name: 'Premium_Luxury', feature: 'premium craftsmanship and elegant design' },
    { name: 'Your_New_Angle', feature: 'your feature description' },
    // ...
];
```

**修改 Prompt 模板：**

在 `generatePrompt()` 函数中自定义逻辑。

**添加新的任务状态：**

在 Mock Server 中添加新的状态枚举。

### 集成真实的 ZAI API

替换 `simulateZAIRecognition()` 函数：

```javascript
async function realZAIRecognition(images) {
    const response = await fetch('YOUR_ZAI_API_ENDPOINT', {
        method: 'POST',
        body: JSON.stringify({ images })
    });
    return await response.json();
}
```

## 故障排查

### Mock Server 无法启动

```bash
# 检查端口占用
lsof -i :3456

# 杀掉占用进程
kill -9 <PID>

# 重新启动
node Seedance2-Chrome-Extensions/mock-server.js
```

### SSE 连接失败

1. 检查 Mock Server 是否运行
2. 检查浏览器控制台错误
3. 刷新页面

### 任务提交失败

1. 检查 Mock Server 日志
2. 检查网络连接
3. 验证任务格式

## 后续计划

### Phase 1: 核心功能
- ✅ 图片上传
- ✅ ZAI 识别
- ✅ 任务生成
- ✅ 任务提交
- ✅ 进度监控

### Phase 2: 增强
- [ ] 真实 ZAI API 集成
- [ ] 视频预览
- [ ] 批量下载
- [ ] 历史记录

### Phase 3: 高级
- [ ] 多用户支持
- [ ] 权限管理
- [ ] 数据库持久化
- [ ] 云端部署

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
