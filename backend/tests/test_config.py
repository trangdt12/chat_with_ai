from app.config import Settings


def test_defaults_match_readme(monkeypatch):
    monkeypatch.delenv("RETRIEVAL_NOT_FOUND_TAU", raising=False)
    s = Settings(_env_file=None)
    assert s.llm_model == "claude-opus-5-5"
    assert s.upload_max_bytes == 20 * 1024 * 1024
    assert s.retrieval_not_found_tau == 0.35


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("RETRIEVAL_NOT_FOUND_TAU", "0.5")
    monkeypatch.setenv("UPLOAD_MAX_PAGES", "10")
    monkeypatch.setenv("LLM_FAKE", "1")
    s = Settings(_env_file=None)
    assert s.retrieval_not_found_tau == 0.5
    assert s.upload_max_pages == 10
    assert s.llm_fake is True
