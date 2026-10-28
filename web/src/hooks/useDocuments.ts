import { useQuery } from "@tanstack/react-query";
import { listDocuments } from "../api/documents";
import type { DocumentOut } from "../api/types";
import { DOCUMENT_POLL_MS } from "../config";

export const documentsKey = (dsid: string) => ["documents", dsid] as const;

/** Có tài liệu đang chờ / đang xử lý → polling 3 s (AC-US005-1: cập nhật ít nhất mỗi 5 s); hết → dừng. */
export function pollInterval(docs: DocumentOut[] | undefined): number | false {
  return docs?.some((d) => d.status === "uploaded" || d.status === "processing") ? DOCUMENT_POLL_MS : false;
}

export function useDocuments(dsid: string) {
  const query = useQuery({
    queryKey: documentsKey(dsid),
    queryFn: () => listDocuments(dsid),
    refetchInterval: (q) => pollInterval(q.state.data),
  });
  const documents = query.data ?? [];
  return {
    ...query,
    documents,
    readyCount: documents.filter((d) => d.status === "ready").length,
    processingCount: documents.filter((d) => d.status === "uploaded" || d.status === "processing").length,
  };
}
