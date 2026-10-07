/**
 * 职责：为 useJobPolling 的 autoApprove 加去重 + 熔断
 * 原则：不改原 hook 实现，只做包装。同一个 job 只 approve 一次。
 */
import { useRef, useCallback } from 'react';

const MAX_PER_JOB = 1;            // 单 job 最多尝试 1 次
const MAX_TOTAL = 20;             // 本会话全局熔断
const COOLDOWN_MS = 10000;        // 失败后 10 秒冷却
const APPROVE_URL = (id: string) =>
    `http://127.0.0.1:9022/api/rag/ingest/jobs/${id}/approve`;

export function useRagJobDedup() {
    const attempted = useRef<Map<string, number>>(new Map());
    const total = useRef(0);
    const last = useRef(0);

    const shouldApprove = useCallback((jobId: string): boolean => {
        const now = Date.now();
        if (total.current >= MAX_TOTAL) return false;
        if (now - last.current < COOLDOWN_MS) return false;
        if ((attempted.current.get(jobId) ?? 0) >= MAX_PER_JOB) return false;
        return true;
    }, []);

    const approve = useCallback(async (jobId: string): Promise<boolean> => {
        attempted.current.set(jobId, (attempted.current.get(jobId) ?? 0) + 1);
        total.current += 1;
        last.current = Date.now();
        try {
            const r = await fetch(APPROVE_URL(jobId), { method: 'POST' });
            if (!r.ok) {
                console.warn(`[dedup] ${jobId} approve HTTP ${r.status}，进入 ${COOLDOWN_MS/1000}s 冷却`);
                return false;
            }
            return true;
        } catch (e) {
            console.warn(`[dedup] ${jobId} approve 异常:`, e);
            return false;
        }
    }, []);

    return { shouldApprove, approve };
}
