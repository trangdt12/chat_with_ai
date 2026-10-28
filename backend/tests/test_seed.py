from sqlalchemy import func, select

from app.models import DocSet, Membership, User
from app.seed import SEED_USERS, reset, seed


async def _counts(db) -> tuple[int, int, int]:
    return (
        await db.scalar(select(func.count()).select_from(User)),
        await db.scalar(select(func.count()).select_from(DocSet)),
        await db.scalar(select(func.count()).select_from(Membership)),
    )


async def test_seed_idempotent(db):
    await seed(db)
    first = await _counts(db)
    await seed(db)
    assert await _counts(db) == first == (len(SEED_USERS), 1, 3)

    rows = await db.execute(select(User.email, Membership.role).join(Membership, Membership.user_id == User.id))
    roles = dict(rows.all())
    assert roles == {"lan@demo.local": "member", "minh@demo.local": "manager", "anh@demo.local": "member"}
    hung = await db.scalar(select(User).where(User.email == "hung@demo.local"))
    assert hung.is_admin


async def test_seed_reset_clears_data(db):
    await seed(db)
    db.add(User(email="extra@test.local", display_name="Extra"))
    await db.commit()

    await reset(db)
    await seed(db)
    assert (await _counts(db))[0] == len(SEED_USERS)
