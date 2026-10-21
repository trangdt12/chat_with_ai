from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Mọi ngưỡng của hệ thống. Biến môi trường cùng tên viết hoa ghi đè giá trị mặc định."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://cwd:cwd@db:5432/cwd"
    files_dir: str = "/data/files"

    anthropic_api_key: str = ""
    llm_model: str = "claude-opus-5-5"
    llm_max_tokens: int = 4000
    embed_model: str = "BAAI/bge-m3"

    upload_max_bytes: int = 20 * 1024 * 1024
    upload_max_pages: int = 200
    doc_set_max_documents: int = 50

    chunk_max_chars: int = 1800
    chunk_block_max_chars: int = 300

    retrieval_top_k_branch: int = 30
    retrieval_top_k: int = 10
    retrieval_max_per_doc: int = 4
    retrieval_not_found_tau: float = 0.35

    history_turns: int = 6
    question_max_chars: int = 2000
    session_idle_hours: int = 8
    worker_poll_seconds: float = 2

    llm_fake: bool = False
    embed_fake: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
