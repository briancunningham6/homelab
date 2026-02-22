import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as api from '../api/client'
import type { MissionCreate, MissionUpdate, SuggestedActionCreate, SuggestedActionUpdate } from '../types'

// Query keys
export const missionKeys = {
  all: ['missions'] as const,
  lists: () => [...missionKeys.all, 'list'] as const,
  list: () => [...missionKeys.lists()] as const,
  details: () => [...missionKeys.all, 'detail'] as const,
  detail: (id: string) => [...missionKeys.details(), id] as const,
  files: (id: string) => [...missionKeys.all, 'files', id] as const,
  suggestedActions: (id: string) => [...missionKeys.all, 'suggested-actions', id] as const,
}

// Get all missions
export const useMissions = () => {
  return useQuery({
    queryKey: missionKeys.list(),
    queryFn: api.getMissions,
  })
}

// Get single mission
export const useMission = (id: string) => {
  return useQuery({
    queryKey: missionKeys.detail(id),
    queryFn: () => api.getMission(id),
    enabled: !!id,
  })
}

// Create mission
export const useCreateMission = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: MissionCreate) => api.createMission(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: missionKeys.list() })
    },
  })
}

// Update mission
export const useUpdateMission = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: MissionUpdate }) =>
      api.updateMission(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: missionKeys.detail(variables.id) })
      queryClient.invalidateQueries({ queryKey: missionKeys.list() })
    },
  })
}

// Delete mission
export const useDeleteMission = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => api.deleteMission(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: missionKeys.list() })
    },
  })
}

// Get mission files
export const useMissionFiles = (missionId: string) => {
  return useQuery({
    queryKey: missionKeys.files(missionId),
    queryFn: () => api.getMissionFiles(missionId),
    enabled: !!missionId,
  })
}

// Upload file
export const useUploadFile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ missionId, file }: { missionId: string; file: File }) =>
      api.uploadFile(missionId, file),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: missionKeys.files(variables.missionId) })
      queryClient.invalidateQueries({ queryKey: missionKeys.detail(variables.missionId) })
    },
  })
}

// Delete file
export const useDeleteFile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ missionId, fileId }: { missionId: string; fileId: string }) =>
      api.deleteFile(missionId, fileId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: missionKeys.files(variables.missionId) })
      queryClient.invalidateQueries({ queryKey: missionKeys.detail(variables.missionId) })
    },
  })
}

// Get suggested actions
export const useSuggestedActions = (missionId: string, status?: string) => {
  return useQuery({
    queryKey: [...missionKeys.suggestedActions(missionId), status],
    queryFn: () => api.getSuggestedActions(missionId, status),
    enabled: !!missionId,
  })
}

// Create suggested action
export const useCreateSuggestedAction = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ missionId, data }: { missionId: string; data: SuggestedActionCreate }) =>
      api.createSuggestedAction(missionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: missionKeys.suggestedActions(variables.missionId) })
    },
  })
}

// Update suggested action
export const useUpdateSuggestedAction = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ missionId, actionId, data }: { missionId: string; actionId: string; data: SuggestedActionUpdate }) =>
      api.updateSuggestedAction(missionId, actionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: missionKeys.suggestedActions(variables.missionId) })
    },
  })
}

// Delete suggested action
export const useDeleteSuggestedAction = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ missionId, actionId }: { missionId: string; actionId: string }) =>
      api.deleteSuggestedAction(missionId, actionId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: missionKeys.suggestedActions(variables.missionId) })
    },
  })
}
