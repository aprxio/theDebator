# theDebator

Local two-agent debate CLI for summarizing and critiquing scientific papers using Apple Silicon friendly LLM backends such as Ollama.

**✨ New in this version:**
- 🚀 **3x faster** with quantized model support (q4_K_M, q5_K_M)
- 💾 **Memory-safe** with token budget management for long debates
- ⚡ **Real-time streaming** output during generation
- 📊 **Smart chunking** across page boundaries for better context
- 🎯 **Relevance filtering** to surface only high-quality citations
- 📈 **Batch ingestion** with progress tracking for large PDFs

> **M2 MacBook Pro users**: See [PERFORMANCE.md](PERFORMANCE.md) for optimization tips!

## Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- [Homebrew](https://brew.sh) (install with `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`)
- Python 3.10+
- Ollama runtime and models

### Install Ollama and models

```bash
brew install ollama
ollama serve            # start the local runtime (leave running in separate terminal)

# For best performance on M2, use quantized models
ollama pull llama3.1:8b-q4_K_M      # Fast explainer (~5GB, 50-60 tok/s)
ollama pull qwen2.5:14b-q4_K_M      # Strong reviewer (~9GB, 25-30 tok/s)

# Alternative: standard models (larger, slower)
ollama pull llama3.1:8b
ollama pull qwen2.5:14b
```

### Model Selection Guide

| Use Case | Explainer | Reviewer | Total Time (3 rounds) |
|---------|-----------|----------|----------------------|
| **Fast iteration** | llama3.1:8b-q4_K_M | llama3.1:8b-q4_K_M | ~1.5 min |
| **Balanced** ⭐ | llama3.1:8b-q4_K_M | qwen2.5:14b-q4_K_M | ~4 min |
| **High quality** | qwen2.5:14b-q5_K_M | qwen2.5:14b-q5_K_M | ~8 min |
| **Research-grade** | qwen2.5:14b-q4_K_M | qwen2.5:32b-q4_K_M | ~15 min |

> 💡 **Tip**: Quantized models (q4_K_M) run 2-3x faster with minimal quality loss. Perfect for M2 Macs!

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src   # set once per shell, or run pip install -e src
```

## Usage

### 1. Configure your debate

Edit `config.yaml` to set models, chunk sizes, and parameters:

```yaml
models:
  explainer: llama3.1:8b-q4_K_M    # Fast, efficient
  reviewer: qwen2.5:14b-q4_K_M     # Stronger reasoning

retrieval:
  chunk_size: 1000        # Larger = better context
  chunk_overlap: 250      # Prevent context loss at boundaries
  top_k: 5                # More evidence per query

paper:
  path: data.pdf          # Your paper location
```

See [PERFORMANCE.md](PERFORMANCE.md) for detailed tuning guide.

### 2. Ingest your paper

```bash
python -m thedebator.cli ingest --config config.yaml

# For large PDFs (100+ pages), use larger batch size
python -m thedebator.cli ingest --batch-size 200
```

**What happens**: PDF is split into overlapping chunks and embedded into ChromaDB vector store. The chunking now spans page boundaries for better context preservation.

### 3. Run a debate

```bash
python -m thedebator.cli debate "What is the main contribution?" --config config.yaml

# Disable streaming for batch processing
python -m thedebator.cli debate "Summarize the methodology" --no-stream
```

**What happens**: 
- Each agent retrieves relevant chunks from the vector store
- Streaming shows real-time token generation (great UX for slow models!)
- Citation filtering ensures only relevant passages are included
- Token budget management prevents OOM on long debates

### 4. Review results

Output is saved to `discussion.md` with inline `[p.X]` citations:

```markdown
## Explainer
The paper introduces a novel attention mechanism...
_Sources_: [p.3] [p.5] [p.12]

## Reviewer
While the approach is interesting, the evaluation lacks...
_Sources_: [p.15] [p.18]
```

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
