import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { changeRole, listMembers, removeMember } from "../../api/admin";
import type { Member, Role } from "../../api/types";
import { ROLE_LABELS, formatDate } from "../../format";
import { Icon } from "../Icon";
import { Modal } from "../Modal";
import { useToast } from "../Toasts";
import { AddMemberDialog } from "./AddMemberDialog";

export const membersKey = (dsid: string) => ["admin", "members", dsid] as const;

/** Màn 08: danh sách thành viên, đổi vai trò, thêm, gỡ (US-021). */
export function MembersTab({ docSetId, docSetName }: { docSetId: string; docSetName: string }) {
  const qc = useQueryClient();
  const toast = useToast();
  const members = useQuery({ queryKey: membersKey(docSetId), queryFn: () => listMembers(docSetId) });
  const [adding, setAdding] = useState(false);
  const [removing, setRemoving] = useState<Member | null>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: membersKey(docSetId) });
    qc.invalidateQueries({ queryKey: ["admin", "doc-sets"] });
  };

  const role = useMutation({
    mutationFn: ({ uid, role }: { uid: string; role: Role }) => changeRole(docSetId, uid, role),
    onSuccess: (m) => {
      refresh();
      toast(`Đã đổi vai trò của ${m.display_name} thành ${ROLE_LABELS[m.role]}. Đã ghi nhật ký.`, "success");
    },
    onError: () => toast("Không đổi được vai trò. Hãy thử lại.", "danger"),
  });

  const remove = useMutation({
    mutationFn: (m: Member) => removeMember(docSetId, m.user_id),
    onSuccess: (_, m) => {
      setRemoving(null);
      refresh();
      toast(
        `Đã gỡ ${m.display_name} khỏi nhóm. Quyền hết hiệu lực từ thao tác kế tiếp của người này. Đã ghi nhật ký.`,
        "success",
      );
    },
    onError: () => toast("Không gỡ được thành viên. Hãy thử lại.", "danger"),
  });

  const list = members.data ?? [];
  const managers = list.filter((m) => m.role === "manager").length;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Nhóm truy cập · {docSetName}</h1>
          <p className="muted">
            Chỉ thành viên trong nhóm mới xem và hỏi được tài liệu. Gỡ thành viên có hiệu lực ngay ở thao tác kế tiếp của
            họ.
          </p>
        </div>
        <button className="btn btn-primary" type="button" onClick={() => setAdding(true)}>
          <Icon name="plus" small />
          Thêm thành viên
        </button>
      </div>
      <div className="banner banner-info" style={{ marginBottom: "var(--sp-4)" }}>
        <Icon name="shield" />
        <div>
          Quản trị viên không có quyền xem hay hỏi nội dung tài liệu. Muốn xem, hãy tự thêm mình vào nhóm như một Thành
          viên; thao tác này được ghi nhật ký.
        </div>
      </div>

      {members.isPending ? (
        <div className="stack" aria-busy="true">
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      ) : members.isError ? (
        <p className="field-error">Không tải được danh sách thành viên.</p>
      ) : (
        <>
          <div className="table-wrap">
            <table className="table">
              <caption className="sr-only">Thành viên nhóm truy cập bộ tài liệu {docSetName}</caption>
              <thead>
                <tr>
                  <th scope="col">Thành viên</th>
                  <th scope="col">Email</th>
                  <th scope="col">Vai trò</th>
                  <th scope="col">Thêm lúc</th>
                  <th scope="col">
                    <span className="sr-only">Thao tác</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {list.map((m) => (
                  <tr key={m.user_id}>
                    <td>
                      <strong>{m.display_name}</strong>
                    </td>
                    <td>{m.email}</td>
                    <td>
                      <label className="sr-only" htmlFor={`role-${m.user_id}`}>
                        Vai trò của {m.display_name}
                      </label>
                      <select
                        id={`role-${m.user_id}`}
                        className="select"
                        style={{ minHeight: "var(--tap-min)", padding: "2px var(--sp-2)" }}
                        value={m.role}
                        disabled={role.isPending}
                        onChange={(e) => role.mutate({ uid: m.user_id, role: e.target.value as Role })}
                      >
                        <option value="member">{ROLE_LABELS.member}</option>
                        <option value="manager">{ROLE_LABELS.manager}</option>
                      </select>
                    </td>
                    <td className="muted">{formatDate(m.granted_at)}</td>
                    <td>
                      <button
                        className="btn btn-ghost btn-sm"
                        type="button"
                        aria-label={`Gỡ ${m.display_name} khỏi nhóm`}
                        onClick={() => setRemoving(m)}
                      >
                        <Icon name="x" small />
                        Gỡ
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="small muted" style={{ marginTop: "var(--sp-3)" }}>
            {list.length} thành viên · {managers} Quản lý bộ tài liệu
          </p>
        </>
      )}

      {adding && (
        <AddMemberDialog
          docSetId={docSetId}
          onClose={() => setAdding(false)}
          onAdded={(m) => {
            setAdding(false);
            refresh();
            toast(`Đã thêm ${m.display_name} vào nhóm với vai trò ${ROLE_LABELS[m.role]}. Đã ghi nhật ký.`, "success");
          }}
        />
      )}

      {removing && (
        <Modal
          titleId="rm-title"
          descriptionId="rm-desc"
          role="alertdialog"
          initialFocus={cancelRef}
          onClose={() => setRemoving(null)}
          onSubmit={() => remove.mutate(removing)}
        >
          <div className="dialog-header">
            <div className="dialog-icon danger">
              <Icon name="users" />
            </div>
            <div>
              <h2 id="rm-title">Gỡ {removing.display_name} khỏi nhóm?</h2>
              <p id="rm-desc" className="muted small">
                Người này sẽ không xem hay hỏi được tài liệu của bộ {docSetName} từ thao tác kế tiếp.
              </p>
            </div>
          </div>
          <div className="dialog-footer">
            <button ref={cancelRef} className="btn btn-secondary" type="button" onClick={() => setRemoving(null)}>
              Hủy
            </button>
            <button className="btn btn-danger" type="submit" disabled={remove.isPending}>
              Gỡ khỏi nhóm
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
