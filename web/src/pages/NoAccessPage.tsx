import { useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AppHeader } from "../components/AppHeader";
import { Icon } from "../components/Icon";
import { useToast } from "../components/Toasts";
import { ME_KEY, useCurrentMe } from "../auth/useMe";

/** Màn 11. Không hiển thị tên bộ tài liệu hay tên file (AC-US013-1). */
export function NoAccessPage() {
  const me = useCurrentMe();
  const [params] = useSearchParams();
  const revoked = params.get("revoked") === "1";
  const qc = useQueryClient();
  const navigate = useNavigate();
  const toast = useToast();

  async function copyEmail() {
    try {
      await navigator.clipboard.writeText(me.email);
      toast("Đã sao chép email của bạn.", "success");
    } catch {
      toast(`Không sao chép được. Email của bạn: ${me.email}`, "danger");
    }
  }

  async function reload() {
    await qc.invalidateQueries({ queryKey: ME_KEY });
    navigate("/", { replace: true });
  }

  return (
    <div className="app">
      <AppHeader showAdminLink={false} />
      <main className="center" id="main">
        <section className="card err-card" aria-labelledby="err-title">
          <div className="card-body">
            <div className="err-icon">
              <Icon name="lock" />
            </div>
            {revoked ? (
              <>
                <h1 id="err-title">Quyền truy cập của bạn đã thay đổi</h1>
                <p className="muted">
                  Bạn không còn quyền xem hoặc hỏi về bộ tài liệu này. Nếu đây là nhầm lẫn, hãy liên hệ Trưởng nhóm BD.
                </p>
              </>
            ) : (
              <>
                <h1 id="err-title">Bạn chưa có quyền truy cập bộ tài liệu nào</h1>
                <p className="muted">
                  Tài khoản của bạn đã đăng nhập thành công, nhưng chưa được thêm vào nhóm truy cập của bộ tài liệu dự án.
                </p>
              </>
            )}
            <ol className="next-steps">
              <li>
                Liên hệ <strong>Trưởng nhóm BD</strong> để xác nhận bạn cần quyền truy cập.
              </li>
              <li>
                Trưởng nhóm gửi yêu cầu tới <strong>quản trị viên</strong> để thêm bạn vào nhóm.
              </li>
              <li>Sau khi được thêm, bấm Tải lại. Không cần đăng nhập lại.</li>
            </ol>
            <div className="row">
              <button className="btn btn-secondary" type="button" onClick={copyEmail}>
                <Icon name="copy" small />
                Sao chép email của tôi
              </button>
              <button className="btn btn-primary" type="button" onClick={reload}>
                Tải lại
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
