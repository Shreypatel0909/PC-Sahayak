"""Configuration loading and validation.

- Non-secret settings come from a YAML file (config/config.yaml, falling back to
  config/config.example.yaml) and are validated with pydantic models.
- The secret (the Groq API key) comes from the environment / .env, or from
  Streamlit secrets (.streamlit/secrets.toml) at call time. It is never read
  from YAML and never logged.
- Relative paths resolve against the project root (the pc-helper/ folder).

Path overrides handy for tests:
    PC_HELPER_CONFIG, PC_HELPER_KB_DIR, PC_HELPER_INDEX_DIR, PC_HELPER_CONV_DIR
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# pc-helper/pc_helper/core/config.py -> parents[2] == pc-helper/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


# --------------------------------------------------------------------------- #
# Validated non-secret configuration (YAML)
# --------------------------------------------------------------------------- #
class ProjectConfig(BaseModel):
    name: str = "PC Helper & Troubleshooting"
    description: str = ""


class LLMRuntimeConfig(BaseModel):
    # Models hosted on Groq (preserved from the original prototype).
    text_model: str = "openai/gpt-oss-20b"
    vision_model: str = "qwen/qwen3.8-27b"
    temperature: float = 0.3
    # gpt-oss models spend part of this budget on hidden reasoning, so keep it generous.
    max_tokens: int = 4096
    request_timeout_seconds: int = 60
    use_rag: bool = True


class ChunkingConfig(BaseModel):
    chunk_size: int = 800
    chunk_overlap: int = 120


class RetrievalConfig(BaseModel):
    top_k: int = 5
    similarity_threshold: Optional[float] = None


class CitationsConfig(BaseModel):
    enabled: bool = True


class KnowledgeBaseConfig(BaseModel):
    markdown_directory: str = "knowledge_base"
    file_extensions: List[str] = Field(default_factory=lambda: [".md", ".markdown"])
    recursive_scan: bool = True
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    citations: CitationsConfig = Field(default_factory=CitationsConfig)


class EmbeddingsConfig(BaseModel):
    backend: str = "auto"  # auto | sentence-transformers | hashing
    model: str = "all-MiniLM-L6-v2"


class VectorIndexConfig(BaseModel):
    path: str = "data/index"


class ConversationConfig(BaseModel):
    max_history_messages: int = 20
    store_path: str = "data/conversations"
    uploads_path: str = "data/uploads"


class UIConfig(BaseModel):
    # Quick examples shown above the intake form; clicking one fills the issue box.
    starter_suggestions: List[str] = Field(default_factory=lambda: [
        "My laptop is running slowly",
        "My Wi-Fi is connected but the internet does not work",
        "My laptop gets too hot when gaming",
        "My C drive is almost full",
    ])


class LoggingConfig(BaseModel):
    level: str = "INFO"


class AppConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    llm: LLMRuntimeConfig = Field(default_factory=LLMRuntimeConfig)
    knowledge_base: KnowledgeBaseConfig = Field(default_factory=KnowledgeBaseConfig)
    embeddings: EmbeddingsConfig = Field(default_factory=EmbeddingsConfig)
    vector_index: VectorIndexConfig = Field(default_factory=VectorIndexConfig)
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


# --------------------------------------------------------------------------- #
# Secret (environment / Streamlit secrets)
# --------------------------------------------------------------------------- #
class LLMSecrets(BaseModel):
    provider: str = "groq"
    api_key: str = ""

    @property
    def is_configured(self) -> bool:
        key = self.api_key.strip().lower()
        return bool(key) and key not in {"your_api_key_here", "changeme"}


def _resolve_api_key() -> str:
    """Prefer env vars; fall back to Streamlit secrets if available."""
    key = os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY") or ""
    if key:
        return key
    try:  # Streamlit secrets (.streamlit/secrets.toml), only if streamlit is importable
        import streamlit as st  # type: ignore

        return st.secrets.get("GROQ_API_KEY", "")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return ""


def _load_llm_secrets() -> LLMSecrets:
    return LLMSecrets(provider=os.getenv("LLM_PROVIDER", "groq"), api_key=_resolve_api_key())


# --------------------------------------------------------------------------- #
# Combined settings with resolved paths
# --------------------------------------------------------------------------- #
class Settings:
    def __init__(self, config: AppConfig, llm: LLMSecrets):
        self.config = config
        self.llm = llm
        self.project_root = PROJECT_ROOT

    def _resolve(self, raw: str) -> Path:
        p = Path(raw)
        return p if p.is_absolute() else (self.project_root / p)

    @property
    def kb_dir(self) -> Path:
        return self._resolve(os.getenv("PC_HELPER_KB_DIR") or self.config.knowledge_base.markdown_directory)

    @property
    def index_dir(self) -> Path:
        return self._resolve(os.getenv("PC_HELPER_INDEX_DIR") or self.config.vector_index.path)

    @property
    def conversations_dir(self) -> Path:
        return self._resolve(os.getenv("PC_HELPER_CONV_DIR") or self.config.conversation.store_path)

    @property
    def uploads_dir(self) -> Path:
        return self._resolve(os.getenv("PC_HELPER_UPLOADS_DIR") or self.config.conversation.uploads_path)


def _config_path() -> Path:
    env_path = os.getenv("PC_HELPER_CONFIG")
    if env_path:
        return Path(env_path) if Path(env_path).is_absolute() else PROJECT_ROOT / env_path
    primary = PROJECT_ROOT / "config" / "config.yaml"
    return primary if primary.exists() else PROJECT_ROOT / "config" / "config.example.yaml"


def load_settings() -> Settings:
    path = _config_path()
    data = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    return Settings(config=AppConfig(**data), llm=_load_llm_secrets())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
