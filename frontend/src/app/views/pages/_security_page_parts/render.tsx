import { useCallback, useEffect, useState } from "react"

import { securityApi } from "../../../../core/api/security_api"
import type {
  RoleInfo,
  SecuritySummary,
} from "../../../../core/contracts/security"
import { useI18n } from "../../../../core/i18n/i18n"
import {
  Badge,
  Drawer,
  EmptyState,
  IndustrialPage,
  KpiCard,
  KpiRow,
} from "../../../ui/industrial"

import type { SecurityPageRenderProps } from "./render.props";
// Auto-extracted render function for SecurityPage.

export function renderSecurityPage(props: SecurityPageRenderProps) {
  const { TONE, active, error, load, loading, roles, setActive, summary, t } = props;
  void TONE;
  return (

      <IndustrialPage
        title={t("security.title")}
        subtitle={t("security.subtitle")}
        actions={
          <button
            className="ind-btn"
            disabled={loading}
            onClick={() => void load()}
          >
            {loading ? "加载中…" : "刷新"}
          </button>
        }
      >
        {error && (
          <div
            style={{
              padding: "10px 14px",
              marginBottom: 14,
              borderRadius: 8,
              background: "rgba(239,133,133,.08)",
              border: "1px solid rgba(239,133,133,.3)",
              color: "var(--danger)",
              fontSize: 12,
            }}
          >
            {error}
          </div>
        )}

        <KpiRow>
          <KpiCard
            label="角色"
            value={summary?.roles ?? "—"}
          />
          <KpiCard
            label="权限点"
            value={summary?.permissions ?? "—"}
          />
          <KpiCard
            label="租户"
            value={summary?.tenants ?? 0}
            tone={(summary?.tenants ?? 0) > 0 ? "success" : "default"}
          />
          <KpiCard
            label="审计记录"
            value={summary?.audit_entries ?? 0}
            hint={summary?.note ?? undefined}
          />
        </KpiRow>

        <section>
          <h3
            style={{
              fontSize: 13,
              margin: "0 0 10px",
              color: "var(--text-soft)",
              fontWeight: 500,
            }}
          >
            角色定义（{roles.length}）
          </h3>
          {roles.length === 0 ? (
            <EmptyState title="暂无角色" icon="🔒" />
          ) : (
            <div className="ind-grid">
              {roles.map((r) => (
                <div
                  key={r.name}
                  className="ind-card"
                  onClick={() => setActive(r)}
                  style={{ cursor: "pointer" }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: 8,
                    }}
                  >
                    <div className="ind-card__title">{r.name}</div>
                    <Badge tone={TONE[r.name] ?? "muted"}>
                      {r.permissions.length} 权限
                    </Badge>
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      color: "var(--text-soft)",
                      marginBottom: 10,
                    }}
                  >
                    {r.description || "—"}
                  </div>
                  <div className="ind-card__tags">
                    {r.permissions.slice(0, 4).map((p) => (
                      <span key={p} className="ind-tag">
                        {p}
                      </span>
                    ))}
                    {r.permissions.length > 4 && (
                      <span className="ind-tag">
                        +{r.permissions.length - 4}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <Drawer
          open={active !== null}
          title={active?.name ?? ""}
          onClose={() => setActive(null)}
          footer={
            <button
              className="ind-btn"
              onClick={() => setActive(null)}
            >
              关闭
            </button>
          }
        >
          {active && (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--muted)",
                    textTransform: "uppercase",
                    marginBottom: 4,
                  }}
                >
                  角色名
                </div>
                <div style={{ fontFamily: "ui-monospace, monospace" }}>
                  {active.name}
                </div>
              </div>
              <div>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--muted)",
                    textTransform: "uppercase",
                    marginBottom: 4,
                  }}
                >
                  描述
                </div>
                <div>{active.description || "—"}</div>
              </div>
              <div>
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--muted)",
                    textTransform: "uppercase",
                    marginBottom: 8,
                  }}
                >
                  权限（{active.permissions.length}）
                </div>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 4,
                  }}
                >
                  {active.permissions.map((p) => (
                    <div
                      key={p}
                      style={{
                        padding: "4px 10px",
                        borderRadius: 6,
                        background: "var(--panel-2)",
                        fontFamily: "ui-monospace, monospace",
                        fontSize: 12,
                      }}
                    >
                      {p}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Drawer>
      </IndustrialPage>
  );
}
