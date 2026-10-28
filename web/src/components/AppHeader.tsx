import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiFetch } from "../api/client";
import { useCurrentMe } from "../auth/useMe";
import { Icon } from "./Icon";

type Props = {
  docSetName?: string;
  /** Logo dẫn về đâu; trang quản trị trỏ về /admin để không có lối tắt tới nội dung (AC-US021-5). */
  homeHref?: string;
  showAdminLink?: boolean;
  /** Nút mở ngăn kéo thanh tài liệu (768–1279px). */
  leading?: ReactNode;
};

export function AppHeader({ docSetName, homeHref = "/", showAdminLink = true, leading }: Props) {
  const me = useCurrentMe();
  const qc = useQueryClient();
  const navigate = useNavigate();

  const logout = useMutation({
    mutationFn: () => apiFetch<void>("/auth/logout", { method: "POST" }, { handleAuth: false }),
    onSettled: () => {
      qc.clear();
      navigate("/login", { replace: true });
    },
  });

  return (
    <header className="topbar">
      {leading}
      <Link className="brand" to={homeHref}>
        <span className="brand-mark" aria-hidden="true">
          CW
        </span>
        Chat với tài liệu
      </Link>
      {docSetName && (
        <span className="docset-name">
          <Icon name="folder" small />
          {docSetName}
        </span>
      )}
      <span className="topbar-spacer" />
      {showAdminLink && me.is_admin && (
        <Link className="btn btn-ghost btn-sm" to="/admin">
          <Icon name="shield" small />
          Quản trị
        </Link>
      )}
      <span className="user-menu">
        <span className="avatar" aria-hidden="true">
          {initial(me.display_name)}
        </span>
        {me.display_name}
      </span>
      <button className="btn btn-secondary btn-sm" type="button" onClick={() => logout.mutate()} disabled={logout.isPending}>
        Đăng xuất
      </button>
    </header>
  );
}

function initial(name: string): string {
  const parts = name.trim().split(/\s+/);
  return (parts[parts.length - 1]?.[0] ?? "?").toUpperCase();
}
