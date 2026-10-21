from pydantic import BaseModel

from app.errors import AppError


class _Body(BaseModel):
    n: int


def _add_test_routes(app):
    @app.get("/boom-app")
    async def boom_app():
        raise AppError("FORBIDDEN", 403, "Không có quyền")

    @app.post("/typed")
    async def typed(body: _Body):
        return {"n": body.n}

    @app.get("/boom")
    async def boom():
        raise RuntimeError("bất ngờ")


async def test_app_error_shape(app, client):
    _add_test_routes(app)
    r = await client.get("/boom-app")
    assert r.status_code == 403
    assert r.json() == {"code": "FORBIDDEN", "message": "Không có quyền"}


async def test_validation_error_shape(app, client):
    _add_test_routes(app)
    r = await client.post("/typed", json={"n": "không phải số"})
    assert r.status_code == 422
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert "không phải số" not in r.text


async def test_unhandled_error_is_internal(app, client):
    _add_test_routes(app)
    r = await client.get("/boom")
    assert r.status_code == 500
    assert r.json()["code"] == "INTERNAL"
