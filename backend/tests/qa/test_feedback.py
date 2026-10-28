import uuid

from sqlalchemy import select

from app.models import Conversation, Feedback, Turn


async def _turn(db, seeded, status="completed", owner="lan@demo.local") -> Turn:
    conv = Conversation(user_id=seeded.users[owner], doc_set_id=seeded.doc_set_id)
    db.add(conv)
    await db.flush()
    turn = Turn(conversation_id=conv.id, turn_index=0, question="q", answer="a", answer_type="answered", status=status)
    db.add(turn)
    await db.commit()
    return turn


async def test_feedback_upsert_replaces_previous(db, login_as, seeded):
    turn = await _turn(db, seeded)
    lan = await login_as("lan@demo.local")
    url = f"/api/v1/messages/{turn.id}/feedback"

    r = await lan.put(url, json={"rating": "up", "reason": "wrong"})
    assert r.status_code == 200
    assert r.json() == {"turn_id": str(turn.id), "rating": "up", "reason": None}  # up bỏ qua reason

    r = await lan.put(url, json={"rating": "down", "reason": "missing"})
    assert r.json()["rating"] == "down"
    rows = (await db.scalars(select(Feedback).where(Feedback.turn_id == turn.id))).all()
    assert [(f.rating, f.reason) for f in rows] == [("down", "missing")]


async def test_feedback_other_user_forbidden(db, login_as, seeded):
    turn = await _turn(db, seeded)
    minh = await login_as("minh@demo.local")
    r = await minh.put(f"/api/v1/messages/{turn.id}/feedback", json={"rating": "up"})
    assert r.status_code == 403


async def test_feedback_not_completed_turn(db, login_as, seeded):
    for status in ("stopped", "incomplete"):
        turn = await _turn(db, seeded, status=status)
        lan = await login_as("lan@demo.local")
        r = await lan.put(f"/api/v1/messages/{turn.id}/feedback", json={"rating": "up"})
        assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"


async def test_feedback_unknown_message_and_bad_body(login_as, seeded):
    lan = await login_as("lan@demo.local")
    r = await lan.put(f"/api/v1/messages/{uuid.uuid4()}/feedback", json={"rating": "up"})
    assert r.status_code == 404
    r = await lan.put(f"/api/v1/messages/{uuid.uuid4()}/feedback", json={"rating": "meh"})
    assert r.status_code == 422


async def test_feedback_requires_login(client, seeded):
    r = await client.put(f"/api/v1/messages/{uuid.uuid4()}/feedback", json={"rating": "up"})
    assert r.status_code == 401
