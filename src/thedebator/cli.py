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
@click.option("--batch-size", default=100, help="Chunks per batch for ingestion")
def ingest(config_path: Path, batch_size: int) -> None:
    """Ingest the PDF into the vector store with progress tracking."""
    app_config = load_config(config_path)
    pdf = PDFIngestor(app_config.paper.path)
    store = VectorStore(Path(app_config.retrieval.persist_directory))
    store.reset()

    chunks = list(pdf.iter_chunks(app_config.retrieval.chunk_size, app_config.retrieval.chunk_overlap))
    
    if not chunks:
        click.echo("No chunks to ingest.")
        return

    total = 0
    batch = []
    
    with click.progressbar(chunks, label="Ingesting chunks") as bar:
        for chunk in bar:
            batch.append(chunk)
            if len(batch) >= batch_size:
                count = store.upsert(batch)
                total += count
                batch = []

        if batch:
            count = store.upsert(batch)
            total += count

    click.echo(f"\nIngestion complete. Stored {total} chunks in collection '{store.collection_name}'.")


@cli.command()
@click.argument("topic")
@click.option("--config", "config_path", type=click.Path(exists=True, path_type=Path), default=Path("config.yaml"))
@click.option("--stream/--no-stream", default=True, help="Stream output in real-time")
def debate(topic: str, config_path: Path, stream: bool) -> None:
    """Run the debate and output markdown with optional streaming."""
    app_config: AppConfig = load_config(config_path)
    explainer_model = app_config.models.explainer
    reviewer_model = app_config.models.reviewer

    # Get max_history_tokens from config if available, else default to 2000
    max_history = getattr(app_config.retrieval, "max_history_tokens", 2000)

    if explainer_model == reviewer_model:
        shared_backend = OllamaBackend(model=explainer_model, max_history_tokens=max_history)
        explainer_backend = shared_backend
        reviewer_backend = shared_backend
    else:
        explainer_backend = OllamaBackend(model=explainer_model, max_history_tokens=max_history)
        reviewer_backend = OllamaBackend(model=reviewer_model, max_history_tokens=max_history)

    explainer = ExplainerAgent(backend=explainer_backend)
    reviewer = ReviewerAgent(backend=reviewer_backend)

    store = VectorStore(Path(app_config.retrieval.persist_directory))
    conversation = Conversation(
        explainer=explainer,
        reviewer=reviewer,
        rounds=app_config.rounds,
        store=store,
        top_k=app_config.retrieval.top_k,
        stream_output=stream,
    )
    conversation.run(topic)
    conversation.save_markdown(app_config.output.path)
    click.echo(f"\nDebate complete. Output written to {app_config.output.path}")


if __name__ == "__main__":  # pragma: no cover
    cli()
