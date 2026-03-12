// 项目类型定义

export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  materials: Material[];
  taskPlans: TaskPlan[];
}

export interface Material {
  id: string;
  name: string;
  base64: string;
  preview: string;
}

export interface TaskPlan {
  id: string;
  name: string;
  videoCount: number;
  duration: number;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  tasks: Task[];
}

export interface Task {
  id: string;
  taskCode: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  description: string;
  prompt: string;
  modelConfig: {
    model: string;
    referenceMode: string;
    aspectRatio: string;
    duration: number;
  };
  referenceFiles: {
    fileName: string;
    base64: string;
  }[];
  occupiedBy?: string;
}

export interface Schedule {
  id: string;
  name: string;
  projectId: string;
  projectName: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  time: string;
  nextRun: string;
  active: boolean;
}

export interface PlaywrightState {
  running: boolean;
  url?: string;
}

// Mock Server API 类型
export interface MockServerStatus {
  name: string;
  version: string;
  sseClients: number;
}

export interface MockServerTasksResponse {
  total: number;
  tasks: Task[];
}

// 营销角度
export interface MarketingAngle {
  name: string;
  feature: string;
}
