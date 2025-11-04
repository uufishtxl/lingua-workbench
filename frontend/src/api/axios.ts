// src/api.ts
import axios from 'axios';

// 1. 调用“工厂”，创建一个新实例
const apiClient = axios.create({

  // 2. 在这里“预先配置”好你的“暗号”
  baseURL: '/api'
  
  // 你还可以在这里预设“超时时间”等
  // timeout: 10000, 
});

// 3. 把这个“配置好”的实例导出去
export default apiClient;