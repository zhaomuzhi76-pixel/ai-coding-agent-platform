export interface RoleInfo {
  name: string
  permissions: string[]
  description: string
}

export interface SecuritySummary {
  roles: number
  permissions: number
  tenants: number
  audit_entries: number
  denials: number
  note?: string
}

export interface CheckResult {
  allowed: boolean
  reason: string
  matched_role: string
  permission: string
}
