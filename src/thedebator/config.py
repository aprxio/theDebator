"""Configuration helpers for theDebator."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class RetrievalConfig:
    chunk_size: int = 800
    chunk_overlap: int = 200
    persist_directory: str = "chroma_store"
    top_k: int = 3


@dataclass
class ModelsConfig:
    explainer: str = "llama3:8b"
    reviewer: str = "llama3:8b"


@dataclass
class PaperConfig:
    path: Path


@dataclass
class OutputConfig:
    path: Path = Path("discussion.md")


@dataclass
class AppConfig:
    backend: str = "ollama"
    model: str = "llama3:8b"
    models: ModelsConfig = field(default_factory=ModelsConfig)
    rounds: int = 3
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    paper: PaperConfig = field(default_factory=lambda: PaperConfig(path=Path("sample.pdf")))
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(path: Path) -> AppConfig:
    """Load configuration from YAML file."""
    with path.open("r", encoding="utf-8") as config_file:
        data: Dict[str, Any] = yaml.safe_load(config_file) or {}

    models_cfg = data.get("models", {})
    retrieval_cfg = data.get("retrieval", {})
    paper_cfg = data.get("paper", {})
    output_cfg = data.get("output", {})

    default_model = str(data.get("model", "llama3:8b"))
    models = ModelsConfig(
        explainer=str(models_cfg.get("explainer", default_model)),
        reviewer=str(models_cfg.get("reviewer", default_model)),
    )

    return AppConfig(
        backend=data.get("backend", "ollama"),
        model=default_model,
        models=models,
        rounds=int(data.get("rounds", 3)),
        retrieval=RetrievalConfig(
            chunk_size=int(retrieval_cfg.get("chunk_size", 800)),
            chunk_overlap=int(retrieval_cfg.get("chunk_overlap", 200)),
            persist_directory=str(retrieval_cfg.get("persist_directory", ".chroma")),
            top_k=int(retrieval_cfg.get("top_k", 3)),
        ),
        paper=PaperConfig(path=Path(paper_cfg.get("path", "sample.pdf"))),
        output=OutputConfig(path=Path(output_cfg.get("path", "discussion.md"))),
    )
