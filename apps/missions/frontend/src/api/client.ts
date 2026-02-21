import axios from 'axios'
import type { Mission, MissionCreate, MissionUpdate, MissionFile } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Health check
export const getHealth = async () => {
  const response = await apiClient.get('/api/health')
  return response.data
}

// Mission endpoints
export const getMissions = async (): Promise<Mission[]> => {
  const response = await apiClient.get('/api/missions')
  return response.data
}

export const getMission = async (id: string): Promise<Mission> => {
  const response = await apiClient.get(`/api/missions/${id}`)
  return response.data
}

export const createMission = async (data: MissionCreate): Promise<Mission> => {
  const response = await apiClient.post('/api/missions', data)
  return response.data
}

export const updateMission = async (id: string, data: MissionUpdate): Promise<Mission> => {
  const response = await apiClient.put(`/api/missions/${id}`, data)
  return response.data
}

export const deleteMission = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/missions/${id}`)
}

// File endpoints
export const getMissionFiles = async (missionId: string): Promise<MissionFile[]> => {
  const response = await apiClient.get(`/api/missions/${missionId}/files`)
  return response.data
}

export const uploadFile = async (missionId: string, file: File): Promise<MissionFile> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post(`/api/missions/${missionId}/files`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const downloadFile = async (missionId: string, fileId: string): Promise<Blob> => {
  const response = await apiClient.get(`/api/missions/${missionId}/files/${fileId}`, {
    responseType: 'blob',
  })
  return response.data
}

export const deleteFile = async (missionId: string, fileId: string): Promise<void> => {
  await apiClient.delete(`/api/missions/${missionId}/files/${fileId}`)
}
