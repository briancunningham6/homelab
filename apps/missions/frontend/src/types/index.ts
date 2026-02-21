/**
 * Type definitions for Missions application
 */

export interface Mission {
  id: string
  name: string
  description: string
  goals: string
  category_id?: string
  llm_provider_id?: string
  model_override?: string
  check_interval: string
  status: string
  last_checked_at?: string
  next_check_at?: string
  created_at: string
  updated_at?: string
  file_count: number
  message_count: number
}

export interface MissionCreate {
  name: string
  description: string
  goals: string
  category_id?: string
  llm_provider_id?: string
  model_override?: string
  check_interval?: string
}

export interface Category {
  id: string
  name: string
  display_name: string
  color?: string
  icon?: string
  created_at: string
}

export interface LLMProvider {
  id: string
  name: string
  display_name: string
  default_model?: string
  is_enabled: boolean
  has_api_key: boolean
  created_at: string
}

export interface MissionFile {
  id: string
  mission_id: string
  filename: string
  original_name: string
  mime_type?: string
  size: number
  uploaded_at: string
  extracted_text?: string
}

export interface Message {
  id: string
  mission_id: string
  role: string
  content: string
  tool_name?: string
  input_tokens?: number
  output_tokens?: number
  model_used?: string
  created_at: string
}

export interface MissionUpdate {
  name?: string
  description?: string
  goals?: string
  category_id?: string
  llm_provider_id?: string
  model_override?: string
  check_interval?: string
  status?: string
}
