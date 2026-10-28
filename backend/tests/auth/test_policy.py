import uuid

import pytest
from sqlalchemy import delete

from app.auth.policy import AccessContext, can_admin, can_batch_upload, can_use_content, can_view_metadata
from app.models import Membership

DS = uuid.uuid4()

# email → (memberships, is_admin, kỳ vọng (use_content, batch_upload, view_metadata, admin))
TRUTH = {
    "lan@demo.local": ({DS: "member"}, False, (True, False, True, False)),
    "minh@demo.local": ({DS: "manager"}, False, (True, True, True, False)),
    "hung@demo.local": ({}, True, (False, False, True, True)),
    "tuan@demo.local": ({}, False, (False, False, False, False)),
}


@pytest.mark.parametrize("email", TRUTH)
def test_policy_truth_table(email):
    memberships, is_admin, expected = TRUTH[email]
    ctx = AccessContext(user_id=uuid.uuid4(), is_admin=is_admin, memberships=memberships, session_id_hash="x")
    got = (can_use_content(ctx, DS), can_batch_upload(ctx, DS), can_view_metadata(ctx, DS), can_admin(ctx))
    assert got == expected


def test_admin_who_is_also_member_has_both():
    ctx = AccessContext(user_id=uuid.uuid4(), is_admin=True, memberships={DS: "member"}, session_id_hash="x")
    assert can_use_content(ctx, DS) and can_admin(ctx)


async def test_outsider_forbidden_by_require_member(app, login_as, seeded):
    from fastapi import Depends

    from app.auth.deps import require_member

    @app.get("/api/v1/_probe/{dsid}")
    async def probe(ctx=Depends(require_member)):
        return {"ok": True}

    tuan = await login_as("tuan@demo.local")
    r = await tuan.get(f"/api/v1/_probe/{seeded.doc_set_id}")
    assert r.status_code == 403
    assert r.json()["code"] == "FORBIDDEN"
    assert "Dự án X" not in r.text

    lan = await login_as("lan@demo.local")
    assert (await lan.get(f"/api/v1/_probe/{seeded.doc_set_id}")).status_code == 200


async def test_revoke_effective_next_request(app, db, login_as, seeded):
    from fastapi import Depends

    from app.auth.deps import require_member

    @app.get("/api/v1/_probe/{dsid}")
    async def probe(ctx=Depends(require_member)):
        return {"ok": True}

    lan = await login_as("lan@demo.local")
    url = f"/api/v1/_probe/{seeded.doc_set_id}"
    assert (await lan.get(url)).status_code == 200

    await db.execute(delete(Membership).where(Membership.user_id == seeded.users["lan@demo.local"]))
    await db.commit()
    assert (await lan.get(url)).status_code == 403
