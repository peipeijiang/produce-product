// mock-server.js - 模拟任务 API 服务器 v3.2 (pipeline status broadcast)
// 用于测试扩展的任务获取和执行流程
// 启动: node mock-server.js
// 管理页: http://localhost:3456/admin  (模拟推送任务)
//
// 接口:
//   GET  /api/tasks/pending?clientId=xxx  - 获取并占用待处理任务
//   POST /api/tasks/ack                   - 确认接收任务
//   POST /api/tasks/status                - 更新任务状态
//   GET  /api/tasks/release?taskCode=xxx  - 释放占用的任务
//   DELETE /api/tasks/:taskCode           - 删除任务 (可选删除关联文件)
//   GET  /api/events?clientId=xxx         - SSE 长连接（服务器推送新任务通知）
//   POST /api/tasks/push                  - 推送新任务 (支持图片+提示词+realSubmit)
//   GET  /api/config                      - 获取配置信息
//   GET  /admin                           - 任务管理页面

const http = require('http');
const zlib = require('zlib');
const fs = require('fs');
const path = require('path');

const PORT = 3456;
const MAX_BODY_SIZE = 200 * 1024 * 1024; // 200MB (支持视频上传)
const UPLOADS_DIR = path.join(__dirname, 'uploads');
const DATA_DIR = path.join(__dirname, 'data');
const TASKS_JSON = path.join(DATA_DIR, 'tasks.json');
const FILES_JSON = path.join(DATA_DIR, 'files.json');

// 确保目录存在
if (!fs.existsSync(UPLOADS_DIR)) fs.mkdirSync(UPLOADS_DIR, { recursive: true });
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

// 文件存储: fileId → { fileId, taskCode, quality, filename, mimeType, size, uploadedAt, originalUrl, filePath }
const fileStore = new Map();
let fileIdCounter = 0;

// ============================================================
// 生成测试用 512x512 PNG 图片 (使用 zlib, 无需 canvas)
// ============================================================
function generateTestPNG(width, height, r, g, b) {
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

  function crc32(buf) {
    let crc = 0xFFFFFFFF;
    const table = [];
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
      table[n] = c;
    }
    for (let i = 0; i < buf.length; i++) crc = table[(crc ^ buf[i]) & 0xFF] ^ (crc >>> 8);
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }

  function makeChunk(type, data) {
    const typeB = Buffer.from(type, 'ascii');
    const lenB = Buffer.alloc(4);
    lenB.writeUInt32BE(data.length, 0);
    const crcInput = Buffer.concat([typeB, data]);
    const crcB = Buffer.alloc(4);
    crcB.writeUInt32BE(crc32(crcInput), 0);
    return Buffer.concat([lenB, typeB, data, crcB]);
  }

  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(width, 0);
  ihdr.writeUInt32BE(height, 4);
  ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;

  const rawRow = Buffer.alloc(1 + width * 3);
  rawRow[0] = 0;
  for (let x = 0; x < width; x++) {
    rawRow[1 + x * 3] = r;
    rawRow[1 + x * 3 + 1] = g;
    rawRow[1 + x * 3 + 2] = b;
  }
  const rawData = Buffer.concat(Array(height).fill(rawRow));
  const compressed = zlib.deflateSync(rawData);
  const iend = Buffer.alloc(0);

  return Buffer.concat([
    signature,
    makeChunk('IHDR', ihdr),
    makeChunk('IDAT', compressed),
    makeChunk('IEND', iend),
  ]);
}

function makeTestImageBase64(r, g, b) {
  const png = generateTestPNG(512, 512, r, g, b);
  return 'data:image/png;base64,' + png.toString('base64');
}

// ============================================================
// 持久化任务存储
// ============================================================
let taskIdCounter = 0;
const SESSION_ID = Date.now().toString(36).slice(-4); // 每次启动唯一后缀

// 任务池: taskCode → task object (持久)
const taskStore = new Map();

// --- 持久化: 从磁盘加载/保存 ---
function saveTaskStore() {
  try {
    const arr = Array.from(taskStore.values());
    fs.writeFileSync(TASKS_JSON, JSON.stringify(arr, null, 2), 'utf-8');
  } catch (e) { console.error('保存 tasks.json 失败:', e.message); }
}
function saveFileStore() {
  try {
    const arr = Array.from(fileStore.values());
    fs.writeFileSync(FILES_JSON, JSON.stringify(arr, null, 2), 'utf-8');
  } catch (e) { console.error('保存 files.json 失败:', e.message); }
}
function loadPersistedData() {
  // 加载任务
  if (fs.existsSync(TASKS_JSON)) {
    try {
      const arr = JSON.parse(fs.readFileSync(TASKS_JSON, 'utf-8'));
      for (const task of arr) {
        taskStore.set(task.taskCode, task);
      }
      // 恢复 taskIdCounter
      const maxId = arr.reduce((max, t) => {
        const m = t.taskCode?.match(/(\d+)$/);
        return m ? Math.max(max, parseInt(m[1], 10)) : max;
      }, 0);
      if (maxId > taskIdCounter) taskIdCounter = maxId;
      console.log(`  📂 从磁盘恢复 ${arr.length} 个任务`);
    } catch (e) { console.error('加载 tasks.json 失败:', e.message); }
  }
  // 加载文件元数据
  if (fs.existsSync(FILES_JSON)) {
    try {
      const arr = JSON.parse(fs.readFileSync(FILES_JSON, 'utf-8'));
      for (const meta of arr) {
        // 只加载文件仍然存在的记录
        if (fs.existsSync(meta.filePath)) {
          fileStore.set(meta.fileId, meta);
        }
      }
      // 恢复 fileIdCounter
      const maxFid = arr.reduce((max, f) => {
        const m = f.fileId?.match(/(\d+)$/);
        return m ? Math.max(max, parseInt(m[1], 10)) : max;
      }, 0);
      if (maxFid > fileIdCounter) fileIdCounter = maxFid;
      console.log(`  📂 从磁盘恢复 ${fileStore.size} 个文件记录`);
    } catch (e) { console.error('加载 files.json 失败:', e.message); }
  }
}

// 占用状态: taskCode → { clientId, occupiedAt }
const occupiedTasks = new Map();
const OCCUPY_TTL_MS = 24 * 60 * 60 * 1000; // 1天自动释放

// SSE 连接管理
const sseClients = new Map(); // clientId → res

function generateTaskCode() {
  taskIdCounter++;
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
  const seq = String(taskIdCounter).padStart(3, '0');
  return `SD-${dateStr}-${SESSION_ID}-${seq}`;
}

/**
 * 检查任务是否被占用（未过期）
 * @param {string} taskCode
 * @param {string} excludeClientId - 该 clientId 自身占用的不算
 */
function isOccupied(taskCode, excludeClientId) {
  const occ = occupiedTasks.get(taskCode);
  if (!occ) return false;
  if (Date.now() - new Date(occ.occupiedAt).getTime() > OCCUPY_TTL_MS) {
    occupiedTasks.delete(taskCode);
    console.log(`  ⏰ 任务 ${taskCode} 占用已过期，自动释放`);
    return false;
  }
  if (excludeClientId && occ.clientId === excludeClientId) return false;
  return true;
}

/**
 * 占用指定任务到指定 clientId
 */
function occupyTask(taskCode, clientId) {
  occupiedTasks.set(taskCode, {
    clientId,
    occupiedAt: new Date().toISOString(),
  });
}

/**
 * 广播 SSE 事件给所有连接的客户端
 */
function broadcastSSE(event, data, excludeClientId) {
  const payload = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const [cid, res] of sseClients) {
    if (cid === excludeClientId) continue;
    try { res.write(payload); } catch (_) { /* ignore */ }
  }
}

/**
 * 添加任务到任务池
 */
function addTask(taskData) {
  const taskCode = generateTaskCode();
  const task = {
    taskCode,
    createdAt: new Date().toISOString(),
    priority: taskData.priority || 1,
    tags: taskData.tags || [],
    description: taskData.description || '',
    modelConfig: taskData.modelConfig || {
      model: 'Seedance 2.0 Fast',
      referenceMode: '全能参考',
      aspectRatio: '16:9',
      duration: '5s',
    },
    referenceFiles: taskData.referenceFiles || [],
    prompt: taskData.prompt || '',
    realSubmit: taskData.realSubmit === true,
    // 服务端状态
    status: 'pending',
    occupiedBy: null,
    ackedAt: null,
    completedAt: null,
    error: null,
  };
  taskStore.set(taskCode, task);
  saveTaskStore();
  return task;
}

/**
 * 获取可领取的待处理任务
 */
function getPendingTasks(clientId) {
  const result = [];
  for (const [code, task] of taskStore) {
    if (task.status !== 'pending' && task.status !== 'occupied') continue;
    if (isOccupied(code, clientId)) continue;
    result.push(task);
  }
  return result;
}

// ============================================================
// 初始化预制测试数据
// ============================================================
function initPresetTasks() {
  addTask({
    priority: 1,
    tags: ['portrait', 'dance'],
    description: '女孩跳舞测试视频',
    modelConfig: {
      model: 'Seedance 2.0 Fast',
      referenceMode: '全能参考',
      aspectRatio: '16:9',
      duration: '4s',
    },
    referenceFiles: [
      { fileName: 'girl-dance-ref1.png', base64: makeTestImageBase64(200, 100, 100), fileType: 'image/png' },
      { fileName: 'girl-dance-ref2.png', base64: makeTestImageBase64(100, 200, 100), fileType: 'image/png' },
    ],
    prompt: '一个穿红色裙子的女孩 (@图片1) 在舞台上优雅地跳舞 (@图片2)',
    realSubmit: false,
  });

  addTask({
    priority: 2,
    tags: ['landscape', 'nature'],
    description: '风景延时摄影',
    modelConfig: {
      model: 'Seedance 2.0 Fast',
      referenceMode: '全能参考',
      aspectRatio: '16:9',
      duration: '4s',
    },
    referenceFiles: [
      { fileName: 'mountain-view.png', base64: makeTestImageBase64(80, 130, 200), fileType: 'image/png' },
    ],
    prompt: '壮丽的山脉日出延时摄影 (@图片1) 云海翻涌光影变幻',
    realSubmit: false,
  });

  addTask({
    priority: 3,
    tags: ['product', 'commercial'],
    description: '产品展示旋转',
    modelConfig: {
      model: 'Seedance 2.0 Fast',
      referenceMode: '全能参考',
      aspectRatio: '1:1',
      duration: '4s',
    },
    referenceFiles: [
      { fileName: 'product-front.png', base64: makeTestImageBase64(240, 240, 240), fileType: 'image/png' },
    ],
    prompt: '精致的产品在白色背景上缓慢旋转展示 (@图片1)',
    realSubmit: false,
  });

  console.log(`  📦 已初始化 ${taskStore.size} 个预制任务`);
}

// ============================================================
// HTTP 工具
// ============================================================
function parseBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', chunk => {
      size += chunk.length;
      if (size > MAX_BODY_SIZE) {
        reject(new Error('请求体超过 50MB 限制'));
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      try {
        const body = Buffer.concat(chunks).toString('utf-8');
        resolve(body ? JSON.parse(body) : {});
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

function sendJSON(res, data, statusCode = 200) {
  const body = JSON.stringify(data, null, 2);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  });
  res.end(body);
}

function sendHTML(res, html) {
  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
  });
  res.end(html);
}

// ============================================================
// Multipart 解析器 (纯 Node.js, 无外部依赖)
// ============================================================
function parseMultipart(req) {
  return new Promise((resolve, reject) => {
    const contentType = req.headers['content-type'] || '';
    const match = contentType.match(/boundary=(?:"([^"]+)"|([^;]+))/);
    if (!match) {
      reject(new Error('Missing boundary in Content-Type'));
      return;
    }
    const boundary = match[1] || match[2];
    const chunks = [];
    let size = 0;

    req.on('data', chunk => {
      size += chunk.length;
      if (size > MAX_BODY_SIZE) {
        reject(new Error(`文件超过 ${MAX_BODY_SIZE / 1024 / 1024}MB 限制`));
        return;
      }
      chunks.push(chunk);
    });

    req.on('end', () => {
      try {
        const buffer = Buffer.concat(chunks);
        const parts = {};
        const boundaryBuf = Buffer.from('--' + boundary);
        const endBuf = Buffer.from('--' + boundary + '--');

        // Split by boundary
        let pos = 0;
        const sections = [];
        while (pos < buffer.length) {
          const idx = buffer.indexOf(boundaryBuf, pos);
          if (idx === -1) break;
          if (sections.length > 0) {
            // content between previous boundary and this one (strip trailing \r\n)
            let end = idx;
            if (end >= 2 && buffer[end - 2] === 13 && buffer[end - 1] === 10) end -= 2;
            sections[sections.length - 1].end = end;
          }
          const start = idx + boundaryBuf.length;
          // Skip \r\n after boundary
          const afterBoundary = start + 2 <= buffer.length ? start + 2 : start;
          sections.push({ start: afterBoundary, end: buffer.length });
          pos = afterBoundary;
          // Check if this is the end boundary
          if (buffer.indexOf(endBuf, idx) === idx) break;
        }

        for (const section of sections) {
          const data = buffer.slice(section.start, section.end);
          // Find header/body separator (\r\n\r\n)
          const sepIdx = data.indexOf('\r\n\r\n');
          if (sepIdx === -1) continue;
          const headerStr = data.slice(0, sepIdx).toString('utf-8');
          const body = data.slice(sepIdx + 4);

          const nameMatch = headerStr.match(/name="([^"]+)"/);
          if (!nameMatch) continue;
          const name = nameMatch[1];
          const filenameMatch = headerStr.match(/filename="([^"]+)"/);

          if (filenameMatch) {
            // File field
            const contentTypeMatch = headerStr.match(/Content-Type:\s*(.+)/i);
            parts[name] = {
              filename: filenameMatch[1],
              contentType: contentTypeMatch ? contentTypeMatch[1].trim() : 'application/octet-stream',
              data: body,
            };
          } else {
            // Text field
            parts[name] = body.toString('utf-8');
          }
        }

        resolve(parts);
      } catch (e) {
        reject(e);
      }
    });

    req.on('error', reject);
  });
}

// ============================================================
// HTTP 路由
// ============================================================
const server = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    });
    res.end();
    return;
  }

  const url = new URL(req.url, `http://localhost:${PORT}`);
  const pathname = url.pathname;

  if (pathname !== '/api/events') {
    console.log(`[${new Date().toLocaleTimeString()}] ${req.method} ${pathname}`);
  }

  try {
    // ===== SSE 长连接 =====
    if (req.method === 'GET' && pathname === '/api/events') {
      const clientId = url.searchParams.get('clientId') || 'anon-' + Date.now();
      console.log(`  📡 SSE 客户端连接: ${clientId}`);

      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
      });
      res.write(`event: connected\ndata: ${JSON.stringify({ clientId, time: new Date().toISOString() })}\n\n`);
      sseClients.set(clientId, res);

      const heartbeat = setInterval(() => {
        try { res.write(`: heartbeat\n\n`); } catch (_) { /* ignore */ }
      }, 15000);

      req.on('close', () => {
        clearInterval(heartbeat);
        sseClients.delete(clientId);
        console.log(`  📡 SSE 客户端断开: ${clientId} (在线: ${sseClients.size})`);
      });
      return;
    }

    // ===== 获取并占用待处理任务 =====
    if (req.method === 'GET' && pathname === '/api/tasks/pending') {
      const clientId = url.searchParams.get('clientId') || 'unknown';
      const pendingTasks = getPendingTasks(clientId);

      // 占用每个任务 (taskCode → clientId)
      if (pendingTasks.length > 0 && clientId !== 'unknown') {
        for (const task of pendingTasks) {
          occupyTask(task.taskCode, clientId);
          task.status = 'occupied';
          task.occupiedBy = clientId;
        }
        saveTaskStore();
        console.log(`  🔒 ${clientId} 占用 ${pendingTasks.length} 个任务: ${pendingTasks.map(t => t.taskCode).join(', ')}`);
      }

      // 返回客户端数据
      const clientTasks = pendingTasks.map(t => ({
        taskCode: t.taskCode,
        createdAt: t.createdAt,
        priority: t.priority,
        tags: t.tags,
        description: t.description,
        modelConfig: t.modelConfig,
        referenceFiles: t.referenceFiles,
        prompt: t.prompt,
        realSubmit: t.realSubmit,
      }));

      sendJSON(res, {
        success: true,
        total: clientTasks.length,
        tasks: clientTasks,
        occupiedBy: clientId,
      });
      return;
    }

    // ===== 确认接收任务 =====
    if (req.method === 'POST' && pathname === '/api/tasks/ack') {
      const body = await parseBody(req);
      const { taskCodes } = body;
      if (Array.isArray(taskCodes)) {
        for (const code of taskCodes) {
          const task = taskStore.get(code);
          if (task) {
            task.status = 'acked';
            task.ackedAt = new Date().toISOString();
          }
        }
        console.log(`  ✅ 确认任务: ${taskCodes.join(', ')}`);
        saveTaskStore();
      }
      sendJSON(res, { success: true, acknowledged: taskCodes || [] });
      return;
    }

    // ===== 释放占用 =====
    if (req.method === 'GET' && pathname === '/api/tasks/release') {
      const taskCode = url.searchParams.get('taskCode');
      if (taskCode && occupiedTasks.has(taskCode)) {
        const occ = occupiedTasks.get(taskCode);
        occupiedTasks.delete(taskCode);
        const task = taskStore.get(taskCode);
        if (task && (task.status === 'occupied' || task.status === 'acked')) {
          task.status = 'pending';
          task.occupiedBy = null;
        }
        console.log(`  🔓 释放任务 ${taskCode} (原占用: ${occ.clientId})`);
        broadcastSSE('task-released', { taskCode });
        saveTaskStore();
      }
      sendJSON(res, { success: true, taskCode, released: true });
      return;
    }

    // ===== 删除任务 =====
    if (req.method === 'DELETE' && pathname.startsWith('/api/tasks/')) {
      const taskCode = decodeURIComponent(pathname.slice('/api/tasks/'.length)).trim();
      if (!taskCode || taskCode.includes('/')) {
        sendJSON(res, { success: false, error: '无效的任务编号' }, 400);
        return;
      }

      const task = taskStore.get(taskCode);
      if (!task) {
        sendJSON(res, { success: false, error: `任务不存在: ${taskCode}` }, 404);
        return;
      }

      const deleteFilesParam = String(url.searchParams.get('deleteFiles') || '').toLowerCase();
      const deleteFiles = deleteFilesParam === '1' || deleteFilesParam === 'true' || deleteFilesParam === 'yes';
      let deletedFiles = 0;

      taskStore.delete(taskCode);
      occupiedTasks.delete(taskCode);

      if (deleteFiles) {
        const fileIdsToDelete = [];
        for (const [fileId, meta] of fileStore) {
          if (meta.taskCode === taskCode) fileIdsToDelete.push(fileId);
        }
        for (const fileId of fileIdsToDelete) {
          const meta = fileStore.get(fileId);
          if (!meta) continue;
          if (meta.filePath && fs.existsSync(meta.filePath)) {
            try { fs.unlinkSync(meta.filePath); } catch (e) { console.warn(`删除文件失败 ${meta.filePath}:`, e.message); }
          }
          fileStore.delete(fileId);
          deletedFiles++;
        }
        saveFileStore();
      }

      saveTaskStore();
      console.log(`  🗑️ 删除任务 ${taskCode} (状态: ${task.status}${deleteFiles ? `, 删除文件: ${deletedFiles}` : ''})`);
      broadcastSSE('task-deleted', {
        taskCode,
        deleteFiles,
        deletedFiles,
        time: new Date().toISOString(),
      });

      sendJSON(res, { success: true, taskCode, deleted: true, deleteFiles, deletedFiles });
      return;
    }

    // ===== 更新任务状态 =====
    if (req.method === 'POST' && pathname === '/api/tasks/status') {
      const body = await parseBody(req);
      const { taskCode, status, error, completedAt, updatedAt } = body;
      console.log(`  任务状态更新: ${taskCode} → ${status}${error ? ' (' + error + ')' : ''}`);

      const task = taskStore.get(taskCode);
      if (task) {
        task.status = status;
        if (error) task.error = error;
        if (completedAt) task.completedAt = completedAt;
        if (updatedAt) task.updatedAt = updatedAt;
      }
      if (status === 'completed' || status === 'failed') {
        occupiedTasks.delete(taskCode);
      }
      saveTaskStore();

      // 广播状态更新给所有 SSE 客户端
      broadcastSSE('task-status', {
        taskCode,
        status,
        error: error || null,
        time: new Date().toISOString(),
      });

      sendJSON(res, { success: true, taskCode, status });
      return;
    }

    // ===== 获取配置 =====
    if (req.method === 'GET' && pathname === '/api/config') {
      sendJSON(res, {
        success: true,
        config: {
          maxConcurrent: 1,
          taskDelay: 3,
          autoExecute: false,
          apiBaseUrl: `http://localhost:${PORT}`,
        },
      });
      return;
    }

    // ===== 推送新任务 =====
    if (req.method === 'POST' && pathname === '/api/tasks/push') {
      const body = await parseBody(req);
      const tasks = body.tasks || [body];
      const pushed = [];

      for (const t of tasks) {
        const task = addTask({
          description: t.description || '',
          prompt: t.prompt || '',
          tags: t.tags || [],
          priority: t.priority || 1,
          modelConfig: t.modelConfig || undefined,
          referenceFiles: t.referenceFiles || [],
          realSubmit: t.realSubmit === true,
        });
        pushed.push(task.taskCode);
        console.log(`  📥 创建任务 ${task.taskCode}: "${(task.prompt || '').substring(0, 40)}" (realSubmit: ${task.realSubmit})`);
      }

      broadcastSSE('new-tasks', {
        count: pushed.length,
        taskCodes: pushed,
        message: `有 ${pushed.length} 个新任务待领取`,
        time: new Date().toISOString(),
      });
      console.log(`  📤 推送 ${pushed.length} 个任务, 通知 ${sseClients.size} 个 SSE 客户端`);

      sendJSON(res, { success: true, taskCodes: pushed, notified: sseClients.size });
      return;
    }

    // ===== 文件上传 =====
    if (req.method === 'POST' && pathname === '/api/files/upload') {
      const parts = await parseMultipart(req);
      const taskCode = parts.taskCode || 'unknown';
      const quality = parts.quality || 'standard';
      const mimeType = parts.mimeType || 'video/mp4';
      const originalUrl = parts.originalUrl || '';
      const filePart = parts.file;

      if (!filePart || !filePart.data || filePart.data.length === 0) {
        sendJSON(res, { success: false, error: '未提供文件' }, 400);
        return;
      }

      fileIdCounter++;
      const fileId = `F${String(fileIdCounter).padStart(4, '0')}`;
      const ext = (filePart.filename || '').split('.').pop() || 'mp4';
      const safeFilename = `${taskCode}_${quality}_${fileId}.${ext}`;
      const filePath = path.join(UPLOADS_DIR, safeFilename);

      fs.writeFileSync(filePath, filePart.data);

      // 从 taskStore 中关联任务的原始参数
      const taskInfo = taskStore.get(taskCode);
      const meta = {
        fileId,
        taskCode,
        quality,
        filename: safeFilename,
        originalFilename: filePart.filename || safeFilename,
        mimeType: filePart.contentType || mimeType,
        size: filePart.data.length,
        uploadedAt: new Date().toISOString(),
        originalUrl,
        filePath,
        // 关联任务元数据
        taskDescription: taskInfo?.description || '',
        taskPrompt: taskInfo?.prompt || '',
        taskTags: taskInfo?.tags || [],
        taskModelConfig: taskInfo?.modelConfig || null,
        taskRealSubmit: taskInfo?.realSubmit || false,
        taskCreatedAt: taskInfo?.createdAt || '',
      };
      fileStore.set(fileId, meta);
      saveFileStore();

      console.log(`  📁 文件上传: ${safeFilename} (${quality}, ${Math.round(meta.size / 1024)}KB) ← ${taskCode}`);
      sendJSON(res, {
        success: true,
        fileId,
        filename: safeFilename,
        size: meta.size,
        quality,
        taskCode,
      });
      return;
    }

    // ===== 文件列表 (按任务号查询, 支持 tags 过滤) =====
    if (req.method === 'GET' && pathname === '/api/files') {
      const filterTaskCode = url.searchParams.get('taskCode');
      const filterTags = url.searchParams.get('tags'); // 逗号分隔多标签
      const filterTagSet = filterTags ? new Set(filterTags.split(',').map(t => t.trim()).filter(Boolean)) : null;

      // 收集所有唯一标签 (用于前端标签选择器)
      const allTagsSet = new Set();

      const files = [];
      for (const [, meta] of fileStore) {
        if (filterTaskCode && meta.taskCode !== filterTaskCode) continue;

        // 动态从 taskStore 补全缺失的任务元数据 (兼容旧数据)
        let taskDescription = meta.taskDescription || '';
        let taskPrompt = meta.taskPrompt || '';
        let taskTags = meta.taskTags || [];
        let taskModelConfig = meta.taskModelConfig || null;
        let taskRealSubmit = meta.taskRealSubmit || false;
        let taskCreatedAt = meta.taskCreatedAt || '';

        if (!taskDescription && !taskPrompt && taskTags.length === 0 && !taskModelConfig) {
          const taskInfo = taskStore.get(meta.taskCode);
          if (taskInfo) {
            taskDescription = taskInfo.description || '';
            taskPrompt = taskInfo.prompt || '';
            taskTags = taskInfo.tags || [];
            taskModelConfig = taskInfo.modelConfig || null;
            taskRealSubmit = taskInfo.realSubmit || false;
            taskCreatedAt = taskInfo.createdAt || '';
            // 回写到 fileStore 以持久化
            meta.taskDescription = taskDescription;
            meta.taskPrompt = taskPrompt;
            meta.taskTags = taskTags;
            meta.taskModelConfig = taskModelConfig;
            meta.taskRealSubmit = taskRealSubmit;
            meta.taskCreatedAt = taskCreatedAt;
          }
        }

        // 收集所有标签
        for (const tag of taskTags) allTagsSet.add(tag);

        // 按标签过滤 (取交集: 文件必须包含所有选中的标签)
        if (filterTagSet && filterTagSet.size > 0) {
          const fileTags = new Set(taskTags);
          let allMatch = true;
          for (const ft of filterTagSet) {
            if (!fileTags.has(ft)) { allMatch = false; break; }
          }
          if (!allMatch) continue;
        }

        files.push({
          fileId: meta.fileId,
          taskCode: meta.taskCode,
          quality: meta.quality,
          filename: meta.filename,
          mimeType: meta.mimeType,
          size: meta.size,
          uploadedAt: meta.uploadedAt,
          taskDescription,
          taskPrompt,
          taskTags,
          taskModelConfig,
          taskRealSubmit,
          taskCreatedAt,
        });
      }

      // 如果有回写, 保存一次
      saveFileStore();

      // 按任务号分组
      const grouped = {};
      for (const f of files) {
        if (!grouped[f.taskCode]) grouped[f.taskCode] = [];
        grouped[f.taskCode].push(f);
      }
      sendJSON(res, {
        success: true,
        files,
        grouped,
        total: files.length,
        allTags: Array.from(allTagsSet).sort(),
      });
      return;
    }

    // ===== 提供文件下载/预览 =====
    if (req.method === 'GET' && pathname.startsWith('/api/files/')) {
      const fileId = pathname.split('/').pop();
      const meta = fileStore.get(fileId);
      if (!meta || !fs.existsSync(meta.filePath)) {
        sendJSON(res, { success: false, error: '文件不存在' }, 404);
        return;
      }
      const stat = fs.statSync(meta.filePath);
      res.writeHead(200, {
        'Content-Type': meta.mimeType || 'application/octet-stream',
        'Content-Length': stat.size,
        'Content-Disposition': `inline; filename="${encodeURIComponent(meta.filename)}"`,
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'public, max-age=3600',
      });
      fs.createReadStream(meta.filePath).pipe(res);
      return;
    }

    // ===== 文件预览页面 =====
    if (req.method === 'GET' && pathname === '/files') {
      const filesHtmlPath = path.join(__dirname, 'files.html');
      if (fs.existsSync(filesHtmlPath)) {
        const html = fs.readFileSync(filesHtmlPath, 'utf-8');
        sendHTML(res, html);
      } else {
        sendHTML(res, '<h1>files.html not found</h1>');
      }
      return;
    }

    // ===== 获取所有任务列表 =====
    if (req.method === 'GET' && pathname === '/api/tasks') {
      const allTasks = [];
      for (const [code, task] of taskStore) {
        allTasks.push({
          taskCode: task.taskCode,
          description: task.description,
          prompt: (task.prompt || '').substring(0, 60),
          status: task.status,
          realSubmit: task.realSubmit,
          occupiedBy: task.occupiedBy,
          createdAt: task.createdAt,
          referenceFileCount: (task.referenceFiles || []).length,
        });
      }
      sendJSON(res, { success: true, tasks: allTasks, total: allTasks.length });
      return;
    }

    // ===== 管理页面 =====
    if (req.method === 'GET' && pathname === '/admin') {
      const adminHtmlPath = path.join(__dirname, 'admin.html');
      if (fs.existsSync(adminHtmlPath)) {
        const html = fs.readFileSync(adminHtmlPath, 'utf-8');
        sendHTML(res, html);
      } else {
        sendHTML(res, '<h1>admin.html not found</h1>');
      }
      return;
    }

    // ===== 欢迎页 =====
    if (req.method === 'GET' && pathname === '/') {
      const taskSummary = {};
      for (const [, task] of taskStore) {
        taskSummary[task.status] = (taskSummary[task.status] || 0) + 1;
      }
      sendJSON(res, {
        name: 'Seedance 任务 Mock API',
        version: '3.2.0',
        endpoints: [
          'GET  /api/events?clientId=xxx     - SSE 长连接',
          'GET  /api/tasks/pending?clientId=  - 获取并占用待处理任务',
          'POST /api/tasks/ack               - 确认接收任务',
          'POST /api/tasks/status            - 更新任务状态',
          'GET  /api/tasks/release?taskCode=  - 释放占用',
          'DELETE /api/tasks/:taskCode       - 删除任务',
          'POST /api/tasks/push              - 推送新任务',
          'GET  /api/tasks                   - 查看所有任务',
          'GET  /api/config                  - 配置',
          'GET  /admin                       - 管理页面',
          'POST /api/files/upload            - 上传视频文件',
          'GET  /api/files                   - 文件列表',
          'GET  /api/files/:fileId           - 文件下载/预览',
          'GET  /files                       - 文件预览页面',
        ],
        sseClients: sseClients.size,
        taskStore: { total: taskStore.size, ...taskSummary },
        occupiedTasks: Object.fromEntries(occupiedTasks),
      });
      return;
    }

    sendJSON(res, { success: false, error: 'Not Found' }, 404);
  } catch (err) {
    console.error('请求处理错误:', err);
    sendJSON(res, { success: false, error: err.message }, 500);
  }
});

// ============================================================
// 启动
// ============================================================
// 从磁盘加载持久化数据
loadPersistedData();
// initPresetTasks();  // 不再自动创建预制任务，需要时通过 admin 页面手动添加

server.listen(PORT, () => {
  console.log(`\n🚀 Seedance Mock API Server v3.2 已启动`);
  console.log(`   地址: http://localhost:${PORT}`);
  console.log(`   管理: http://localhost:${PORT}/admin`);
  console.log(`   文件: http://localhost:${PORT}/files`);
  console.log(`   SSE:  http://localhost:${PORT}/api/events?clientId=test`);
  console.log(`   任务: http://localhost:${PORT}/api/tasks/pending?clientId=test`);
  console.log(`   推送: POST http://localhost:${PORT}/api/tasks/push`);
  console.log(`   列表: http://localhost:${PORT}/api/tasks`);
  console.log(`   上传: POST http://localhost:${PORT}/api/files/upload\n`);
});
