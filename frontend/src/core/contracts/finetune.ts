export interface RecipeInfo {
  name: string
  description: string
}

export interface RecipeDetail extends RecipeInfo {
  config: Record<string, unknown>
}

export interface FinetuneRun {
  id: string
  method: string
  base_model: string
  epochs: number
  samples: number
  status: string
  progress: number
  loss: number
  saved_to: string
}

export interface FinetuneSummary {
  recipes: number
  runs: number
  statuses: Record<string, number>
}


// ─── 任务管理（L2）───

export interface JobSpec {
  recipe_name: string
  base_model: string
  dataset_path: string
  output_dir: string
  job_name: string
  description: string
  tags: string[]
}

export interface JobRecord {
  job_id: string
  spec: JobSpec
  state: "pending" | "running" | "succeeded" | "failed" | "cancelled"
  created_at: number
  updated_at: number
  started_at: number
  finished_at: number
  progress: number
  current_step: number
  total_steps: number
  loss: number
  saved_to: string
  error: string
  elapsed_sec: number
  metadata: Record<string, unknown>
}

export interface JobEvent {
  event_id: string
  job_id: string
  event_type: string
  payload: Record<string, unknown>
  created_at: number
}

export interface SubmitJobPayload {
  recipe_name: string
  base_model: string
  dataset_path: string
  output_dir?: string
  job_name?: string
  description?: string
  tags?: string[]
}


// ─── 数据集（D4-L2）───

export interface DatasetUpdatePayload {
  name?: string
  description?: string
  tags?: string[]
}

export interface DatasetSpec {
  dataset_id: string
  name: string
  path: string
  format: string
  description: string
  sample_count: number
  size_bytes: number
  created_at: number
  tags: string[]
}

export interface ValidationIssue {
  line_no: number
  level: "error" | "warning"
  message: string
}

export interface DatasetPreviewItem {
  line_no: number
  user: string
  assistant: string
  has_system: boolean
  history_turns: number
}

export interface DatasetValidationReport {
  ok: boolean
  path: string
  sample_count: number
  valid_count?: number
  size_bytes: number
  error_count: number
  warning_count: number
  issues: ValidationIssue[]
  preview: DatasetPreviewItem[]
}

export interface DatasetStats {
  name: string
  version: string
  datasets: number
  total_samples: number
  total_bytes: number
  dir: string
}


// ─── Adapter 部署（D5-L2）───

export interface AdapterSpec {
  adapter_id: string
  name: string
  base_model: string
  adapter_path: string
  method: "lora" | "prefix"
  target: "ollama" | "peft_merged"
  merge_mode: "adapter_only" | "merged"
  ollama_model_name: string
  source_job_id: string
  size_bytes: number
  created_at: number
  description: string
  tags: string[]
}

export interface DeployPlan {
  adapter_id: string
  model_name: string
  modelfile_text: string
  modelfile_path: string
  command: string[]
  timeout_sec: number
}

export interface DeployStep {
  name: string
  ok: boolean
  elapsed_sec: number
  message: string
}

export interface DeployResult {
  ok: boolean
  adapter_id: string
  model_name: string
  returncode: number
  stdout: string
  stderr: string
  elapsed_sec: number
  error: string
  steps?: DeployStep[]
  log_tail?: string[]
}

export interface MountedAdapter {
  adapter_id: string
  model_name: string
  provider: string
  base_model: string
  mounted_at: number
}

// ─── 环境检测（D）───

export interface EnvPackage {
  name: string
  installed: boolean
  version: string
  error: string
}

export interface EnvGpu {
  available: boolean
  name: string
  vram_total_mb: number
  vram_free_mb: number
  compute_capability: string
  cuda_version: string
  error: string
}

export interface EnvReport {
  ready_for_training: boolean
  packages: EnvPackage[]
  gpu: EnvGpu
  ollama_available: boolean
  suggestions: string[]
  warnings: string[]
}
