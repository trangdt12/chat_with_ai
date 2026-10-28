import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { ApiError, setAuthHandlers } from "./api/client";
import { saveDraft } from "./auth/draftStore";
import { RequireAuth } from "./auth/RequireAuth";
import { ME_KEY } from "./auth/useMe";
import { ToastProvider } from "./components/Toasts";
import { AdminPage } from "./pages/AdminPage";
import { ChatPage } from "./pages/ChatPage";
import { LoginPage } from "./pages/LoginPage";
import { NoAccessPage } from "./pages/NoAccessPage";

export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Lỗi nghiệp vụ (4xx) không thử lại; lỗi mạng thử lại 2 lần.
        retry: (count, err) => !(err instanceof ApiError && err.status < 500) && count < 2,
        refetchOnWindowFocus: false,
      },
    },
  });
}

/** Nối handler 401/403 của apiFetch với router. */
function AuthBridge() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  useEffect(() => {
    setAuthHandlers({
      onUnauthenticated: () => {
        const hadSession = qc.getQueryData(ME_KEY) != null;
        saveDraft();
        qc.clear();
        const next = encodeURIComponent(window.location.pathname);
        navigate(`/login?${hadSession ? "expired=1&" : ""}next=${next}`, { replace: true });
      },
      onForbidden: () => {
        qc.invalidateQueries({ queryKey: ME_KEY });
        navigate("/no-access?revoked=1", { replace: true });
      },
    });
    return () => setAuthHandlers({});
  }, [navigate, qc]);

  return null;
}

export function App() {
  const [queryClient] = useState(makeQueryClient);
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <AuthBridge />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <RequireAuth area="chat">
                  <ChatPage />
                </RequireAuth>
              }
            />
            <Route
              path="/admin"
              element={
                <RequireAuth area="admin">
                  <AdminPage />
                </RequireAuth>
              }
            />
            <Route
              path="/no-access"
              element={
                <RequireAuth area="any">
                  <NoAccessPage />
                </RequireAuth>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
