"""Command-line interface for theDebator."""

from pathlib import Path

import click

from thedebator.agents import ExplainerAgent, ReviewerAgent
from thedebator.backends import OllamaBackend
from thedebator.config import AppConfig, load_config
from thedebator.conversation import Conversation
from thedebator.retrieval import PDFIngestor, VectorStore


@click.group()
def cli() -> None:
    """Run theDebator CLI."""


@cli.command()
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), default=Path("config.yaml"))
def ingest(config_path: Path) -> None:
    """Ingest the PDF into the vector store."""
    app_config = load_config(config_path)
    pdf = PDFIngestor(app_config.paper.path)
    store = VectorStore(Path(app_config.retrieval.persist_directory))
    store.reset()
    count = store.upsert(
        pdf.iter_chunks(app_config.retrieval.chunk_size, app_config.retrieval.chunk_overlap)
    )
    click.echo(f"Ingestion complete. Stored {count} chunks in collection '{store.collection_name}'.")


@cli.command()
@click.argument("topic")
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), default=Path("config.yaml"))
def debate(topic: str, config_path: Path) -> None:
    """Run the debate and output markdown."""
    app_config: AppConfig = load_config(config_path)
    explainer_model = app_config.models.explainer
    reviewer_model = app_config.models.reviewer

    if explainer_model == reviewer_model:
        shared_backend = OllamaBackend(model=explainer_model)
        explainer_backend = shared_backend
        reviewer_backend = shared_backend
    else:
        explainer_backend = OllamaBackend(model=explainer_model)
        reviewer_backend = OllamaBackend(model=reviewer_model)

    explainer = ExplainerAgent(backend=explainer_backend)
    reviewer = ReviewerAgent(backend=reviewer_backend)

    store = VectorStore(Path(app_config.retrieval.persist_directory))
    conversation = Conversation(
        explainer=explainer,
        reviewer=reviewer,
        rounds=app_config.rounds,
        store=store,
        top_k=app_config.retrieval.top_k,
    )
    conversation.run(topic)
    conversation.save_markdown(app_config.output.path)
    click.echo(f"Debate complete. Output written to {app_config.output.path}")


if __name__ == "__main__":  # pragma: no cover
    cli()
