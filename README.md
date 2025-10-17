# theDebator

Local two-agent debate CLI for summarizing and critiquing scientific papers using Apple Silicon friendly LLM backends such as Ollama.

## Prerequisites

- macOS with Apple Silicon
- [Homebrew](https://brew.sh) (install with `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)
- Python 3.10+
- Ollama runtime and at least one model (default `llama3:8b`)

### Install Ollama and models

```bash
brew install ollama
ollama serve            # start the local runtime (leave running)
ollama pull llama3:8b   # download the default model
```

### Choose and manage models

- List available models with `ollama list`; add new ones by running `ollama pull <model-name>`.
- Larger science-focused options such as `llama3:70b`, `qwen2.5:72b`, or `mixtral-8x7b` offer better reasoning at the cost of GPU/CPU and RAM usage.
- Set debate backends in `config.yaml` under `models.explainer` and `models.reviewer`; both default to `llama3:8b` if you omit the section.
- If you change models often, keep `ollama serve` running so the runtime reloads weights quickly between debates.

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src   # set once per shell, or run pip install -e src
```

## Usage

1. **Configure** the debate parameters in `config.yaml`. The default setup expects your paper at `paper.path: data.pdf`, which resolves to the `data.pdf` file in the project root—replace the file or update the path if you store papers elsewhere.
2. **Ingest** the target PDF to build the retrieval index:

   ```bash
   python -m thedebator.cli ingest --config config.yaml
   ```

3. **Run** a debate on a question or topic grounded in the ingested paper:

   ```bash
   python -m thedebator.cli debate "What is the main contribution?" --config config.yaml
   ```

4. Review `discussion.md` for a Markdown transcript that includes `[p.X]` citations aligned with the supporting passages.

> Tip: keep `ollama serve` running in another terminal so debate requests connect immediately.

### Configuration tuning

- `rounds`: number of back-and-forth exchanges. More rounds deepen the debate but multiply latency and token usage; tighten it for quick summaries, expand it when you want nuanced critique.
- `retrieval.chunk_size`: characters per PDF chunk before embedding. Larger chunks preserve context for long paragraphs but inflate tokens; smaller chunks surface precise quotes but may drop surrounding detail.
- `retrieval.chunk_overlap`: shared characters between neighboring chunks. Increase overlap when the paper has dense formulas or cross-sentence references to keep context; lower it to reduce ingestion/storage cost on straightforward prose.
- `retrieval.top_k`: number of chunks fetched for each question turn. Higher values provide broader evidence coverage but can dilute focus and lengthen prompts; lower values keep answers concise but risk missing supporting passages.
- Match chunk sizes and `top_k` to your document length: short articles work well with 500–800 char chunks and `top_k=3`, whereas long reports may benefit from 1 000–1 200 char chunks and `top_k=5` to cover all sections.
- Every increase in chunk size, overlap, or `top_k` translates into larger prompts, which can slow execution and strain smaller models. Balance quality against runtime by adjusting one knob at a time and re-running `ingest` when chunk parameters change.

### Different models for explainer and reviewer

- Configure asymmetric debates by editing `config.yaml`:

   ```yaml
   models:
      explainer: llama3:8b
      reviewer: llama3:70b
   ```

- Run `ollama pull` for every model you reference; the CLI automatically instantiates separate backends and reuses one runtime if both names match.
Suggested pairings:

| Scenario | Explainer model | Reviewer model | Rationale |
| --- | --- | --- | --- |
| Fast summary | `llama3:8b` | `llama3:8b` | Quick, low-memory pass for abstracts or short papers. |
| Socratic drill-down | `llama3:8b` | `mixtral-8x7b` | Reviewer adds mixture-of-experts reasoning to surface counterpoints. |
| Rigorous audit | `mixtral-8x7b` | `llama3:70b` or `qwen2.5:72b` | Heavy compute trade for deep technical scrutiny. |
| Specialized science | Domain model (e.g. `llama3:instruct-bio`) | Domain model (`mistral-nemo`, etc.) | Match vocabulary and style to niche disciplines. |

- Mixing model sizes changes latency: larger reviewer models slow each round but often improve factual pressure; consider reducing `rounds` if the loop becomes too slow.
- Switching agent models does not require re-running `ingest`; only retrieval parameter changes need a fresh embedding pass.

## Project Layout

- `src/thedebator/` — CLI, conversation engine, agent definitions, vector store, and backends.
- `config.yaml` — runtime configuration for models, retrieval, and paths.
- `tests/` — unit tests for key components.

## Running Tests

```bash
pytest
```

## Notes

- Run the ingestion step before `debate` so the ChromaDB store contains the paper context.
- Adjust `models.explainer` and `models.reviewer` in `config.yaml` to experiment with different local models.
- The vector store persists to `chroma_store/` by default; change `retrieval.persist_directory` if you want a different path.
- Because the project uses a `src/` layout, export `PYTHONPATH=src` (or install the package with `pip install -e src`) before running the CLI commands from the project root.
