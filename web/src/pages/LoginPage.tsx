import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { apiFetch, jsonBody } from "../api/client";
import type { DevUser } from "../api/types";
import { Icon } from "../components/Icon";

/** Chỉ cho quay về đường dẫn nội bộ, tránh open redirect qua ?next=. */
export function safeNext(next: string | null): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/login")) return "/";
  return next;
}

export function LoginPage() {
  const [params] = useSearchParams();
  const expired = params.get("expired") === "1";
  const next = safeNext(params.get("next"));
  const qc = useQueryClient();
  const navigate = useNavigate();

  const users = useQuery({
    queryKey: ["dev-users"],
    queryFn: () => apiFetch<DevUser[]>("/auth/dev-users", {}, { handleAuth: false }),
  });

  const login = useMutation({
    mutationFn: (email: string) =>
      apiFetch<void>("/auth/login", { method: "POST", ...jsonBody({ email }) }, { handleAuth: false }),
    onSuccess: () => {
      qc.clear();
      navigate(next, { replace: true });
    },
  });

  return (
    <main className="login">
      <section className="card login-card" aria-labelledby="login-title">
        <div className="card-body">
          <div className="login-brand">
            <div className="brand-mark" aria-hidden="true">
              CW
            </div>
            <div>
              <h1 id="login-title">Chat với tài liệu</h1>
              <p className="muted small">Hỏi đáp có dẫn nguồn trên tài liệu dự án</p>
            </div>
          </div>

          {expired && (
            <div className="banner banner-warning" role="status">
              <Icon name="clock" />
              <div>
                <strong className="banner-title">Phiên đăng nhập đã hết hạn</strong>
                Câu hỏi bạn đang gõ đã được giữ lại và sẽ hiện lại sau khi đăng nhập.
              </div>
            </div>
          )}

          {(login.isError || users.isError) && (
            <div className="banner banner-danger" role="alert">
              <Icon name="alert" />
              <div>
                <strong className="banner-title">Không đăng nhập được</strong>
                {users.isError ? "Không tải được danh sách tài khoản." : "Vui lòng thử lại."}
              </div>
            </div>
          )}

          <div className="stack">
            <div className="row">
              <span className="badge badge-info">Đăng nhập thử nghiệm</span>
            </div>
            <p>Chọn một tài khoản mẫu để tiếp tục. Bản thử nghiệm không dùng mật khẩu.</p>
            {users.isPending && <div className="skeleton" style={{ height: 48 }} />}
            <ul className="dev-users">
              {users.data?.map((u) => (
                <li key={u.email}>
                  <button
                    className="btn btn-secondary"
                    type="button"
                    disabled={login.isPending}
                    onClick={() => login.mutate(u.email)}
                  >
                    {u.display_name}
                    <span className="user-email small muted">{u.email}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="login-foot">
            <Icon name="lock" small />
            <p>Câu trả lời chỉ dựa trên tài liệu đã tải lên, luôn đối chiếu nguồn trước khi gửi cho đối tác.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
