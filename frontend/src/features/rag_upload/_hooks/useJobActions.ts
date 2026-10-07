/**
 * 职责：job 取消/审核 API 客户端（独立文件，不改原有 hook）
 */
const BASE = "http://127.0.0.1:9022/api/rag/ingest/jobs";

// pending_review 是半终态：不算"进行中"，需要审核或取消
export const ACTIVE_STATES = new Set([
    "queued", "parsing", "chunking", "embedding", "indexing", "processing", "running"
]);
export const TERMINAL_STATES = new Set([
    "completed", "failed", "cancelled", "approved", "rejected"
]);

export function isActiveJob(status: string): boolean {
    return ACTIVE_STATES.has(status);
}
export function isPendingReview(status: string): boolean {
    return status === "pending_review";
}
export function isFinishedJob(status: string): boolean {
    return TERMINAL_STATES.has(status) || isPendingReview(status);
}

export async function cancelJob(jobId: string): Promise<boolean> {
    try {
        const r = await fetch(`${BASE}/${jobId}/cancel`, { method: "POST" });
        return r.ok;
    } catch (e) {
        console.warn("[cancel] 异常:", e);
        return false;
    }
}
export async function approveJob(jobId: string): Promise<boolean> {
    try {
        const r = await fetch(`${BASE}/${jobId}/approve`, { method: "POST" });
        return r.ok;
    } catch (e) {
        console.warn("[approve] 异常:", e);
        return false;
    }
}
