import { request } from "../http/http_client"

interface Envelope<T> {
  ok: boolean
  data?: T
  error?: { code: string; message: string }
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const payload = await request<Envelope<T>>(path, init)
  if (!payload.ok || payload.data === undefined) {
    throw new Error(
      payload.error
        ? `${payload.error.code}: ${payload.error.message}`
        : "unknown error",
    )
  }
  return payload.data
}

export interface RagStatus {
  count: number
  collection: string
  vector_path: string
  embedding: { base_url: string; model: string }
  reranker: {
    url: string
    enabled: boolean
    health: {
      ok: boolean; status?: number; error?: string
      mode?: "http" | "local"
      models?: string[]; count?: number
    }
  }
}

export interface RagHit {
  chunk_id: string
  text: string
  score: number
  source: string
  source_path: string
  line_no: number
  role: string
}

export interface RagQueryResult {
  query: string
  count: number
  hits: RagHit[]
}

export const ragApi = {
  status(): Promise<RagStatus> {
    return call<RagStatus>("/rag/status")
  },
  count(): Promise<number> {
    return call<number>("/rag/count")
  },
  indexTexts(
    texts: string[], source = "inline",
  ): Promise<{ indexed: number }> {
    return call("/rag/index/texts", {
      method: "POST",
      body: JSON.stringify({ texts, source }),
    })
  },
  indexDataset(
    datasetPath: string, datasetId = "",
  ): Promise<{ indexed: number }> {
    return call("/rag/index/dataset", {
      method: "POST",
      body: JSON.stringify({
        dataset_path: datasetPath,
        dataset_id: datasetId,
      }),
    })
  },
  query(
    q: string, topK = 5, useRerank?: boolean,
  ): Promise<RagQueryResult> {
    return call<RagQueryResult>("/rag/query", {
      method: "POST",
      body: JSON.stringify({
        query: q,
        top_k: topK,
        use_rerank: useRerank,
      }),
    })
  },
  clear(): Promise<{ cleared: boolean }> {
    return call("/rag/clear", { method: "POST" })
  },
  finetuneDatasets(): Promise<{
    datasets: Array<{
      dataset_id: string
      name: string
      path: string
      sample_count: number
      size_bytes: number
      created_at: number
    }>
    count: number
  }> {
    return call("/rag/finetune-datasets")
  },
  multimodalIndex(body: {
    items?: Array<{ text: string; images?: Array<Record<string, unknown>>;
                    source?: string; line_no?: number;
                    metadata?: Record<string, unknown> }>
    text?: string
    images?: Array<Record<string, unknown>>
    source?: string
    line_no?: number
  }): Promise<{ indexed: number; chunks: number; skipped: number;
                batches: number; errors: string[] }> {
    return call("/rag/multimodal/index", {
      method: "POST", body: JSON.stringify(body),
    })
  },
  multimodalSearch(body: {
    query: string
    limit?: number
    rerank?: boolean
    rerank_top_k?: number
  }): Promise<{
    query: string
    candidates: number
    reranked: boolean
    hits: Array<{
      chunk_id: string
      text: string
      score: number
      source: string
      line_no: number
      role: string
      images: Array<{ id: string; mime: string; source: string;
                      url?: string; b64?: string; alt_text?: string }>
    }>
  }> {
    return call("/rag/multimodal/search", {
      method: "POST", body: JSON.stringify(body),
    })
  },
  indexAllFinetune(): Promise<{
    dataset_count: number
    total_indexed: number
    skipped: number
    failed: number
    collection_total: number
    results: Array<{
      dataset_id: string
      name: string
      status: string
      indexed?: number
      reason?: string
      error?: string
    }>
  }> {
    return call("/rag/index/all-finetune-datasets", { method: "POST" })
  },
}
