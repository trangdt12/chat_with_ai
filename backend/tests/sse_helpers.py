"""Dựng môi trường hỏi đáp cho test API: FakeLlmClient + FakeEmbedder thay qua dependency_overrides."""

import json

import httpx

from app.ingestion.embeddings import FakeEmbedder
from app.qa.llm import FakeLlmClient
from app.qa.router import embedder_dep, llm_dep, registry_dep
from app.qa.streams import StreamRegistry

QUESTION = "Thời hạn thanh toán là bao lâu?"


def parse_sse(body: str) -> list[tuple[str, dict]]:
    events = []
    for frame in body.replace("\r\n", "\n").split("\n\n"):
        name, data = None, []
        for line in frame.split("\n"):
            if line.startswith(":") or not line:
                continue
            key, _, value = line.partition(":")
            value = value[1:] if value.startswith(" ") else value
            if key == "event":
                name = value
            elif key == "data":
                data.append(value)
        if name:
            events.append((name, json.loads("\n".join(data))))
    return events


class SpyEmbedder(FakeEmbedder):
    def __init__(self):
        self.queries: list[str] = []

    def embed_query(self, text):
        self.queries.append(text)
        return super().embed_query(text)


class Env:
    def __init__(self, app, db, seeded, lan):
        self.app, self.db, self.seeded, self.lan = app, db, seeded, lan
        self.llm = FakeLlmClient(delay=0.01)
        self.embedder = SpyEmbedder()
        self.registry = StreamRegistry()
        app.dependency_overrides[llm_dep] = lambda: self.llm
        app.dependency_overrides[embedder_dep] = lambda: self.embedder
        app.dependency_overrides[registry_dep] = lambda: self.registry

    async def conversation(self, client=None) -> str:
        r = await (client or self.lan).post(f"/api/v1/doc-sets/{self.seeded.doc_set_id}/conversations")
        assert r.status_code == 201, r.text
        return r.json()["conversation_id"]

    async def ask(self, cid: str, question: str = QUESTION, client=None) -> httpx.Response:
        return await (client or self.lan).post(f"/api/v1/conversations/{cid}/messages", json={"question": question})

    async def ask_events(self, cid: str, question: str = QUESTION, client=None) -> list[tuple[str, dict]]:
        r = await self.ask(cid, question, client)
        assert r.status_code == 200, r.text
        assert r.headers["content-type"].startswith("text/event-stream")
        return parse_sse(r.text)
