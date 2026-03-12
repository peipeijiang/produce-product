import { useState, useEffect } from 'react'
import { mockServerAPI } from './lib/api'
import { getMarketingAngles, generateTaskJson } from './lib/prompt-generator'
import type { MarketingAngle, Material, Task, MockServerTasksResponse } from './lib/types'
import './App.css'

function App() {
  const [productName, setProductName] = useState('')
  const [productId, setProductId] = useState('')
  const [materials, setMaterials] = useState<Material[]>([])
  const [selectedAngles, setSelectedAngles] = useState<Set<string>>(new Set())
  const [duration, setDuration] = useState(12)
  const [enableVoiceover, setEnableVoiceover] = useState(true)
  const [enableSubtitles, setEnableSubtitles] = useState(true)
  const [enableHookCta, setEnableHookCta] = useState(true)
  const [mockServerStatus, setMockServerStatus] = useState<{ name: string; version: string; sseClients: number } | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // 检查服务器状态
  useEffect(() => {
    checkServers()
    const interval = setInterval(checkServers, 5000)
    return () => clearInterval(interval)
  }, [])

  // 轮询任务状态
  useEffect(() => {
    if (mockServerStatus) {
      fetchTasks()
      const interval = setInterval(fetchTasks, 3000)
      return () => clearInterval(interval)
    }
  }, [mockServerStatus])

  async function checkServers() {
    try {
      const mockStatus = await mockServerAPI.getStatus()
      setMockServerStatus(mockStatus)
    } catch (error) {
      console.log('Mock Server not running')
      setMockServerStatus(null)
    }
  }

  async function fetchTasks() {
    try {
      const response: MockServerTasksResponse = await mockServerAPI.getTasks()
      setTasks(response.tasks)
    } catch (error) {
      console.error('Failed to fetch tasks:', error)
    }
  }

  function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const files = event.target.files
    if (!files) return

    Array.from(files).forEach((file) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const base64 = e.target?.result as string
        const newMaterial: Material = {
          id: `material-${Date.now()}-${Math.random()}`,
          name: file.name,
          base64,
          preview: base64
        }
        setMaterials((prev) => [...prev, newMaterial])
      }
      reader.readAsDataURL(file)
    })
  }

  function handleRemoveMaterial(id: string) {
    setMaterials((prev) => prev.filter((m) => m.id !== id))
  }

  function handleAngleToggle(angleName: string) {
    setSelectedAngles((prev) => {
      const next = new Set(prev)
      if (next.has(angleName)) {
        next.delete(angleName)
      } else {
        next.add(angleName)
      }
      return next
    })
  }

  function showMessage(type: 'success' | 'error', text: string) {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 5000)
  }

  async function handleSubmit() {
    if (!productName || !productId || materials.length === 0 || selectedAngles.size === 0) {
      showMessage('error', '请填写所有必填项')
      return
    }

    try {
      setLoading(true)
      const angles = getMarketingAngles().filter((a) => selectedAngles.has(a.name))

      for (const angle of angles) {
        const taskJson = generateTaskJson(
          productId,
          productName,
          angle,
          duration,
          {
            enableVoiceover,
            enableSubtitles,
            enableHookCta
          }
        )

        await mockServerAPI.submitTask(taskJson)
      }

      showMessage('success', `已提交 ${selectedAngles.size} 个视频任务`)
      setSelectedAngles(new Set())
      await fetchTasks()
    } catch (error) {
      showMessage('error', '提交任务失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎬 产品营销视频制作</h1>
        <div className="server-status">
          <div className={`status-indicator ${mockServerStatus ? 'online' : 'offline'}`}>
            Mock Server: {mockServerStatus ? '在线' : '离线'}
          </div>
        </div>
      </header>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <main className="app-main">
        <div className="section">
          <h2>📦 产品信息</h2>
          <div className="form-group">
            <label>产品名称 *</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              placeholder="例如: Premium Wireless Headphones"
            />
          </div>
          <div className="form-group">
            <label>产品 ID *</label>
            <input
              type="text"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              placeholder="例如: WH-1000XM5"
            />
          </div>
        </div>

        <div className="section">
          <h2>🖼️ 上传产品图片 *</h2>
          <div className="upload-area">
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileUpload}
              id="file-upload"
            />
            <label htmlFor="file-upload" className="upload-button">
              点击选择图片或拖拽上传
            </label>
          </div>
          <div className="materials-grid">
            {materials.map((material) => (
              <div key={material.id} className="material-item">
                <img src={material.preview} alt={material.name} />
                <button
                  className="remove-button"
                  onClick={() => handleRemoveMaterial(material.id)}
                >
                  ×
                </button>
                <div className="material-name">{material.name}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="section">
          <h2>🎯 选择营销角度 *</h2>
          <div className="angles-grid">
            {getMarketingAngles().map((angle) => (
              <div
                key={angle.name}
                className={`angle-card ${selectedAngles.has(angle.name) ? 'selected' : ''}`}
                onClick={() => handleAngleToggle(angle.name)}
              >
                <div className="angle-name">{angle.name.replace(/_/g, ' ')}</div>
                <div className="angle-feature">{angle.feature}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="section">
          <h2>⚙️ 视频配置</h2>
          <div className="form-group">
            <label>视频时长 (秒) *</label>
            <input
              type="number"
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              min="4"
              max="12"
            />
          </div>
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={enableVoiceover}
                onChange={(e) => setEnableVoiceover(e.target.checked)}
              />
              启用语音解说
            </label>
            <label>
              <input
                type="checkbox"
                checked={enableSubtitles}
                onChange={(e) => setEnableSubtitles(e.target.checked)}
              />
              启用字幕
            </label>
            <label>
              <input
                type="checkbox"
                checked={enableHookCta}
                onChange={(e) => setEnableHookCta(e.target.checked)}
              />
              Hook-Body-CTA 结构
            </label>
          </div>
        </div>

        <div className="section">
          <button
            className="submit-button"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? '生成中...' : '🚀 生成视频任务'}
          </button>
        </div>

        {tasks.length > 0 && (
          <div className="section">
            <h2>📋 任务列表</h2>
            <div className="tasks-list">
              {tasks.map((task) => (
                <div key={task.id} className="task-card">
                  <div className="task-header">
                    <span className="task-code">{task.taskCode}</span>
                    <span className={`task-status ${task.status}`}>
                      {task.status}
                    </span>
                  </div>
                  <div className="task-description">{task.description}</div>
                  <div className="task-details">
                    <span>{task.modelConfig.duration}s</span>
                    <span>{task.modelConfig.aspectRatio}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
