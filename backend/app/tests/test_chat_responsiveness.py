import asyncio
import threading
import uuid
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.routes import chat
from app.db.models import Conversation, Repository
from app.db.session import Base, get_db
from app.services.chat_memory import AssembledContext, ContextAssembler, ProgressiveContextManager


def _slow_assembler(monkeypatch):
    started, release, finished = threading.Event(), threading.Event(), threading.Event()

    def assemble(self, repo, conversation, message, limit=16):
        started.set()
        try:
            if not release.wait(timeout=2):
                raise AssertionError("Chat preparation blocked the event loop")
            return AssembledContext("test context", [], [], {})
        finally:
            finished.set()

    monkeypatch.setattr(ContextAssembler, "assemble", assemble)
    return started, release, finished


async def _wait_started(started):
    for _ in range(100):
        if started.is_set():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("Context preparation did not start")


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/api/chat", "/api/chat/stream"])
async def test_health_responds_while_chat_retrieval_is_blocked(monkeypatch, path):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = Session(engine)
    repo = Repository(owner="acme", name="responsiveness", full_name="acme/responsiveness")
    db.add(repo)
    db.flush()
    conversation = Conversation(repo_id=repo.id, title="Test")
    db.add(conversation)
    db.commit()
    repo_id, conversation_id = str(repo.id), str(conversation.id)
    started, release, finished = _slow_assembler(monkeypatch)

    async def ensure_headroom(self, *args):
        return {"attempted": False}

    async def seal(self, **kwargs):
        return None

    class Agent:
        async def run(self, *args):
            return {"answer": "ok", "route": "direct_answer", "tool_calls": [], "citations": []}

        async def run_stream(self, *args):
            yield {"event": "final", "data": await self.run()}

    monkeypatch.setattr(chat.ProgressiveContextManager, "ensure_headroom", ensure_headroom)
    monkeypatch.setattr(chat.SessionSealer, "seal", seal)
    monkeypatch.setattr(chat.EvidenceStore, "rebuild_repo", lambda *args: None)
    monkeypatch.setattr(chat, "ChatAgent", Agent)
    monkeypatch.setattr(chat, "_build_conversation_tools", lambda *args: {})
    monkeypatch.setattr(chat, "_skill_runtime_context", lambda: {})

    app = FastAPI()
    app.include_router(chat.router, prefix="/api/chat")
    app.dependency_overrides[get_db] = lambda: db

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            pending = asyncio.create_task(client.post(path, json={
                "repo_id": repo_id, "conversation_id": conversation_id, "message": "hello",
            }))
            try:
                await _wait_started(started)
                response = await asyncio.wait_for(client.get("/health"), timeout=0.5)
                assert response.json() == {"status": "ok"}
                assert not finished.is_set(), "Health responded only after retrieval finished"
            finally:
                release.set()
                response = await pending
            assert response.status_code == 200
            assert '"route":"error"' not in response.text
            assert "ok" in response.text
            assert db.query(chat.ChatMessage).filter_by(conversation_id=conversation.id).count() == 2
    finally:
        db.close()
        engine.dispose()


@pytest.mark.asyncio
async def test_headroom_retrieval_keeps_event_loop_responsive(monkeypatch):
    started, release, finished = _slow_assembler(monkeypatch)
    manager = ProgressiveContextManager(db=None)
    monkeypatch.setattr(manager, "_raw_segment_tokens", lambda *args: 0)
    scope = SimpleNamespace(id=uuid.uuid4())
    pending = asyncio.create_task(manager.ensure_headroom(scope, scope, "hello"))
    try:
        await _wait_started(started)
        assert not finished.is_set(), "Headroom retrieval blocked the event loop"
    finally:
        release.set()
        result = await pending
    assert result["attempted"] is False
