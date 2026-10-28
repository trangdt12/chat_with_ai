import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { ApiError } from "../api/client";
import { MeContext, useMe } from "./useMe";

type Area = "chat" | "admin" | "any";

/**
 * - Chưa đăng nhập → /login?next=…
 * - Trang chat: không thuộc nhóm nào → /no-access (admin không thuộc nhóm → /admin)
 * - Trang quản trị: không phải admin → / (hoặc /no-access nếu không thuộc nhóm)
 */
export function RequireAuth({ area, children }: { area: Area; children: ReactNode }) {
  const { data: me, isPending, error, refetch } = useMe();
  const location = useLocation();

  if (isPending) {
    return (
      <main className="center" aria-busy="true">
        <p className="muted">Đang tải…</p>
      </main>
    );
  }
  if (error && !(error instanceof ApiError && error.status === 401)) {
    return (
      <main className="center">
        <div className="stack" style={{ alignItems: "center" }}>
          <p>Không kết nối được máy chủ.</p>
          <button className="btn btn-secondary" type="button" onClick={() => refetch()}>
            Thử lại
          </button>
        </div>
      </main>
    );
  }
  if (!me) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?next=${next}`} replace />;
  }

  const hasGroup = me.doc_sets.length > 0;
  if (area === "chat" && !hasGroup) return <Navigate to={me.is_admin ? "/admin" : "/no-access"} replace />;
  if (area === "admin" && !me.is_admin) return <Navigate to={hasGroup ? "/" : "/no-access"} replace />;

  return <MeContext.Provider value={me}>{children}</MeContext.Provider>;
}
