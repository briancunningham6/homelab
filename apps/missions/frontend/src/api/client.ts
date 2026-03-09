import axios from 'axios'
import type {
  Mission,
  MissionCreate,
  MissionUpdate,
  MissionFile,
  SuggestedAction,
  SuggestedActionCreate,
  SuggestedActionUpdate,
  MissionTask,
  TaskCreate,
  TaskUpdate,
  TaskReorderItem,
} from '../types'

// Use same-origin API path in browser (proxied by Vite/Caddy)
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Health check
export const getHealth = async () => {
  const response = await apiClient.get('/health')
  return response.data
}

// Mission endpoints
export const getMissions = async (): Promise<Mission[]> => {
  const response = await apiClient.get('/missions/')
  return response.data
}

export const getMission = async (id: string): Promise<Mission> => {
  const response = await apiClient.get(`/missions/${id}`)
  return response.data
}

export const createMission = async (data: MissionCreate): Promise<Mission> => {
  const response = await apiClient.post('/missions/', data)
  return response.data
}

export const updateMission = async (id: string, data: MissionUpdate): Promise<Mission> => {
  const response = await apiClient.put(`/missions/${id}`, data)
  return response.data
}

export const deleteMission = async (id: string): Promise<void> => {
  await apiClient.delete(`/missions/${id}`)
}

// File endpoints
export const getMissionFiles = async (missionId: string): Promise<MissionFile[]> => {
  const response = await apiClient.get(`/missions/${missionId}/files`)
  return response.data
}

export const uploadFile = async (missionId: string, file: File): Promise<MissionFile> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post(`/missions/${missionId}/files`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const downloadFile = async (missionId: string, fileId: string): Promise<Blob> => {
  const response = await apiClient.get(`/missions/${missionId}/files/${fileId}`, {
    responseType: 'blob',
  })
  return response.data
}

export const deleteFile = async (missionId: string, fileId: string): Promise<void> => {
  await apiClient.delete(`/missions/${missionId}/files/${fileId}`)
}

// Suggested Actions
export const getSuggestedActions = async (missionId: string, status?: string): Promise<SuggestedAction[]> => {
  const params = status ? { status } : {}
  const response = await apiClient.get(`/missions/${missionId}/suggested-actions`, { params })
  return response.data
}

export const createSuggestedAction = async (
  missionId: string,
  data: SuggestedActionCreate
): Promise<SuggestedAction> => {
  const response = await apiClient.post(`/missions/${missionId}/suggested-actions`, data)
  return response.data
}

export const updateSuggestedAction = async (
  missionId: string,
  actionId: string,
  data: SuggestedActionUpdate
): Promise<SuggestedAction> => {
  const response = await apiClient.patch(`/missions/${missionId}/suggested-actions/${actionId}`, data)
  return response.data
}

export const deleteSuggestedAction = async (missionId: string, actionId: string): Promise<void> => {
  await apiClient.delete(`/missions/${missionId}/suggested-actions/${actionId}`)
}

// Tasks
export const getTasks = async (missionId: string): Promise<MissionTask[]> => {
  const response = await apiClient.get(`/missions/${missionId}/tasks/`)
  return response.data
}

export const createTask = async (missionId: string, data: TaskCreate): Promise<MissionTask> => {
  const response = await apiClient.post(`/missions/${missionId}/tasks/`, data)
  return response.data
}

export const updateTask = async (missionId: string, taskId: string, data: TaskUpdate): Promise<MissionTask> => {
  const response = await apiClient.patch(`/missions/${missionId}/tasks/${taskId}`, data)
  return response.data
}

export const deleteTask = async (missionId: string, taskId: string): Promise<void> => {
  await apiClient.delete(`/missions/${missionId}/tasks/${taskId}`)
}

export const reorderTasks = async (missionId: string, items: TaskReorderItem[]): Promise<void> => {
  await apiClient.post(`/missions/${missionId}/tasks/reorder`, items)
}
