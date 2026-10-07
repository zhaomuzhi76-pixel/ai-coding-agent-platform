import { useCallback, useEffect, useState } from "react"

import { securityApi } from "../../../core/api/security_api"
import type {
  RoleInfo,
  SecuritySummary,
} from "../../../core/contracts/security"
import { useI18n } from "../../../core/i18n/i18n"
import {
  Badge,
  Drawer,
  EmptyState,
  IndustrialPage,
  KpiCard,
  KpiRow,
} from "../../ui/industrial"

import { renderSecurityPage } from "./_security_page_parts/render";

const TONE: Record<string, "success" | "info" | "muted" | "warning"> = {
  admin: "success",
  developer: "info",
  reviewer: "info",
  viewer: "muted",
  service: "warning",
}

export function SecurityPage() {
  const { t } = useI18n()
  const [summary, setSummary] = useState<SecuritySummary | null>(null)
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [active, setActive] = useState<RoleInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [s, r] = await Promise.all([
        securityApi.summary(),
        securityApi.roles(),
      ])
      setSummary(s)
      setRoles(r.roles)
      setError(null)
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return renderSecurityPage({ TONE, active, error, load, loading, roles, setActive, summary, t });
}
