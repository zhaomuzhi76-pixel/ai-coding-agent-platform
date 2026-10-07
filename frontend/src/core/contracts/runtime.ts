export interface RuntimeStatus {
  ready: boolean
  state: string
  detail?: string
}

export interface HealthResponse {
  status: string
}
