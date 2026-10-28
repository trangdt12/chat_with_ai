import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { addMember } from "../../api/admin";
import { ApiError } from "../../api/client";
import type { Member, Role } from "../../api/types";
import { Icon } from "../Icon";
import { Modal } from "../Modal";

const ROLE_OPTIONS: { value: Role; label: string }[] = [
  { value: "member", label: "Thành viên — xem, hỏi, tải từng file" },
  { value: "manager", label: "Quản lý bộ tài liệu — thêm quyền tải lô" },
];

const ERRORS: Record<string, string> = {
  USER_NOT_FOUND: "Không tìm thấy tài khoản này trong hệ thống. Kiểm tra lại email.",
  ALREADY_MEMBER: "Tài khoản này đã thuộc nhóm.",
};

export function AddMemberDialog({
  docSetId,
  onClose,
  onAdded,
}: {
  docSetId: string;
  onClose: () => void;
  onAdded: (m: Member) => void;
}) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("member");
  const add = useMutation({ mutationFn: () => addMember(docSetId, email.trim(), role), onSuccess: onAdded });

  const code = add.error instanceof ApiError ? add.error.code : null;
  const fieldError = code ? ERRORS[code] : null;

  return (
    <Modal titleId="add-title" onClose={onClose} onSubmit={() => email.trim() && add.mutate()}>
      <div className="dialog-header">
        <div>
          <h2 id="add-title">Thêm thành viên vào nhóm truy cập</h2>
          <p className="muted small">Tài khoản phải tồn tại trong hệ thống.</p>
        </div>
      </div>
      <div className="dialog-body">
        <div className="field">
          <label htmlFor="member-email">Email</label>
          <input
            id="member-email"
            className="input"
            type="email"
            autoComplete="off"
            value={email}
            aria-invalid={fieldError ? true : undefined}
            aria-describedby={fieldError ? "email-err" : undefined}
            onChange={(e) => {
              setEmail(e.target.value);
              if (add.isError) add.reset();
            }}
          />
          {fieldError && (
            <span id="email-err" className="field-error">
              <Icon name="alert" small />
              {fieldError}
            </span>
          )}
        </div>
        <fieldset className="field" style={{ border: 0, padding: 0, margin: 0 }}>
          <legend className="label">Vai trò</legend>
          {ROLE_OPTIONS.map((o) => (
            <label key={o.value} className="checkbox">
              <input
                type="radio"
                name="member-role"
                value={o.value}
                checked={role === o.value}
                onChange={() => setRole(o.value)}
              />
              <span>{o.label}</span>
            </label>
          ))}
        </fieldset>
        {add.isError && !fieldError && <p className="field-error">Không thêm được thành viên. Hãy thử lại.</p>}
      </div>
      <div className="dialog-footer">
        <button className="btn btn-secondary" type="button" onClick={onClose}>
          Hủy
        </button>
        <button className="btn btn-primary" type="submit" disabled={!email.trim() || add.isPending}>
          Thêm
        </button>
      </div>
    </Modal>
  );
}
