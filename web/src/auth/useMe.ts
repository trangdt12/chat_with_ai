import { useQuery } from "@tanstack/react-query";
import { createContext, useContext } from "react";
import { apiFetch } from "../api/client";
import type { DocSetRef, Me } from "../api/types";

export const ME_KEY = ["me"] as const;

export function useMe() {
  return useQuery({
    queryKey: ME_KEY,
    // RequireAuth tự điều hướng khi 401 nên không dùng handler chung
    queryFn: () => apiFetch<Me>("/me", {}, { handleAuth: false }),
    retry: false,
    staleTime: 30_000,
  });
}

export const MeContext = createContext<Me | null>(null);

/** Người dùng hiện tại; chỉ dùng bên trong <RequireAuth>. */
export function useCurrentMe(): Me {
  const me = useContext(MeContext);
  if (!me) throw new Error("useCurrentMe phải nằm trong <RequireAuth>");
  return me;
}

/** Bộ tài liệu đang làm việc: bản thử nghiệm dùng bộ đầu tiên người dùng thuộc về. */
export function useActiveDocSet(): DocSetRef | null {
  return useCurrentMe().doc_sets[0] ?? null;
}
