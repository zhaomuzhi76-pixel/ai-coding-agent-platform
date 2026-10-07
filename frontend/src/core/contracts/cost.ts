export interface BucketStats {
  calls: number
  success: number
  errors: number
  input_tokens: number
  output_tokens: number
  cost: number
  latency_p50: number
  latency_p95: number
  latency_max: number
  latency_avg: number
}

export interface ModelBucket extends BucketStats {
  provider: string
  is_local: boolean
}

export interface CostStats {
  total: BucketStats
  online: BucketStats & { providers: string[] }
  local: BucketStats & { providers: string[] }
  by_model: Record<string, ModelBucket>
  by_provider: Record<string, BucketStats>
  by_role: Record<string, BucketStats>
  by_day: Record<string, BucketStats>
  record_count: number
}
