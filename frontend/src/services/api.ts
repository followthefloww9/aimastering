import axios from 'axios';
import { Track, MasteringSettings, TaskStatus, UploadResponse, MasteringSession } from '../types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for uploads
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const trackAPI = {
  // Upload track
  upload: async (file: File, onProgress?: (progress: number) => void): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/api/tracks/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 300000, // 5 minutes for large uploads
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  // Get track info
  getTrack: async (trackId: number): Promise<Track> => {
    const response = await api.get(`/api/tracks/${trackId}`);
    return response.data;
  },

  // Get track analysis
  getAnalysis: async (trackId: number) => {
    const response = await api.get(`/api/tracks/${trackId}/analysis`);
    return response.data;
  },

  // Apply mastering
  master: async (trackId: number, settings: MasteringSettings) => {
    const response = await api.post(`/api/tracks/${trackId}/master`, settings);
    return response.data;
  },

  // Get genre preset
  getPreset: async (trackId: number, genre: string) => {
    const response = await api.get(`/api/tracks/${trackId}/preset/${genre}`);
    return response.data;
  },

  // Download original
  downloadOriginal: (trackId: number): string => {
    return `/api/tracks/${trackId}/download`;
  },

  // Download mastered
  downloadMastered: (trackId: number, sessionId?: number): string => {
    const params = sessionId ? `?session_id=${sessionId}` : '';
    return `/api/tracks/${trackId}/download/mastered${params}`;
  },

  // Get mastering sessions
  getSessions: async (trackId: number): Promise<{ track_id: number; sessions: MasteringSession[] }> => {
    const response = await api.get(`/api/tracks/${trackId}/sessions`);
    return response.data;
  },

  // Delete track
  delete: async (trackId: number) => {
    const response = await api.delete(`/api/tracks/${trackId}`);
    return response.data;
  },
};

export const chatAPI = {
  // Send chat message
  sendMessage: async (trackId: number, message: string, currentSettings: MasteringSettings, applyChanges = true) => {
    const response = await api.post('/api/chat/mastering', {
      track_id: trackId,
      message,
      current_settings: currentSettings,
      apply_changes: applyChanges,
    });
    return response.data;
  },

  // Get AI suggestions
  getSuggestions: async (trackId: number) => {
    const response = await api.post(`/api/chat/suggest?track_id=${trackId}`);
    return response.data;
  },

  // Get chat examples
  getExamples: async () => {
    const response = await api.get('/api/chat/examples');
    return response.data;
  },
};

export const taskAPI = {
  // Get task status
  getStatus: async (taskId: string): Promise<TaskStatus> => {
    const response = await api.get(`/api/tasks/${taskId}`);
    return response.data;
  },

  // Cancel task
  cancel: async (taskId: string) => {
    const response = await api.delete(`/api/tasks/${taskId}`);
    return response.data;
  },

  // Get active tasks
  getActive: async () => {
    const response = await api.get('/api/tasks/');
    return response.data;
  },
};

export const healthAPI = {
  // Health check
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
