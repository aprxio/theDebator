from pathlib import Path

from thedebator.config import load_config


def test_load_config_defaults(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("{}", encoding="utf-8")

    config = load_config(config_path)

    assert config.backend == "ollama"
    assert config.rounds == 3
    assert config.retrieval.top_k == 3
    assert config.models.explainer == "llama3:8b"
    assert config.models.reviewer == "llama3:8b"


def test_load_config_models_override(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
models:
  explainer: llama3:8b
  reviewer: llama3:70b
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.models.explainer == "llama3:8b"
    assert config.models.reviewer == "llama3:70b"
    # Legacy attribute mirrors explainer for backward compatibility
    assert config.model == "llama3:8b"
