import axios from 'axios';

const BASE_URL = 'http://localhost:3457';
const MOCK_SERVER_URL = 'http://localhost:3456';

// Chrome 控制接口
export const chromeAPI = {
  async start(): Promise<{ success: boolean; message: string }> {
    const response = await axios.post(`${BASE_URL}/api/start-chrome`);
    return response.data;
  },

  async stop(): Promise<{ success: boolean; message: string }> {
    const response = await axios.post(`${BASE_URL}/api/stop-chrome`);
    return response.data;
  },

  async getStatus(): Promise<{ running: boolean }> {
    const response = await axios.get(`${BASE_URL}/api/chrome-status`);
    return response.data;
  }
};

// Mock Server 接口
export const mockServerAPI = {
  async submitTask(task: any): Promise<any> {
    const response = await axios.post(`${MOCK_SERVER_URL}/api/tasks/push`, task);
    return response.data;
  },

  async getTasks(): Promise<any> {
    const response = await axios.get(`${MOCK_SERVER_URL}/api/tasks`);
    return response.data;
  },

  async getStatus(): Promise<any> {
    const response = await axios.get(`${MOCK_SERVER_URL}/`);
    return response.data;
  }
};

// 定时任务接口
export const scheduleAPI = {
  async create(schedule: any): Promise<any> {
    // TODO: 实现后端存储
    return { success: true, schedule };
  },

  async getAll(): Promise<any[]> {
    // TODO: 从数据库获取
    return [];
  }
};
