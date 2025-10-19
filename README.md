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

## Configuration Deep Dive

### Key Parameters

**`retrieval.chunk_size`** (default: 1000)

- **Small (600-800)**: Precise citations, may miss context
- **Medium (1000-1200)**: ⭐ Balanced, recommended
- **Large (1500-2000)**: Maximum context, higher token cost

**`retrieval.top_k`** (default: 5)

- **3**: Fast, focused answers
- **5**: ⭐ Comprehensive evidence
- **7+**: Deep analysis, longer prompts

**`retrieval.max_history_tokens`** (default: 2000)

Limits conversation history to prevent memory crashes.

- **1000**: For 32B+ models
- **2000**: ⭐ Safe default for 8-14B models
- **3000**: For 8B models with 64GB+ RAM

**`rounds`** (default: 3)

Number of back-and-forth exchanges.

- **2**: Quick summary
- **3**: ⭐ Balanced debate
- **5+**: Deep analysis (watch memory!)

### Performance Tuning

For M2 32GB, optimal settings:

```yaml
models:
  explainer: llama3.1:8b-q4_K_M
  reviewer: qwen2.5:14b-q4_K_M

retrieval:
  chunk_size: 1000
  chunk_overlap: 250
  top_k: 5
  max_history_tokens: 2000
```

This gives ~25-40 tok/s average, 4-5 min per debate, excellent quality.

## Troubleshooting

### Slow generation (<10 tok/s)

- ✅ Use quantized models (q4_K_M or q5_K_M)
- ✅ Verify Metal acceleration: logs should show "num_gpu: 1"
- ✅ Close other apps to free VRAM
- ✅ Reduce `max_history_tokens` to 1500

### Out of memory crashes

- ✅ Reduce `max_history_tokens` to 1000
- ✅ Lower `top_k` to 3
- ✅ Use smaller models (8B instead of 14B)
- ✅ Reduce `rounds` to 2

### Poor citation quality

- ✅ Increase `chunk_size` to 1500
- ✅ Increase `top_k` to 7
- ✅ Re-run `ingest` after config changes
- ✅ Verify PDF has extractable text (not scanned)

### Ingestion hangs

- ✅ Increase `--batch-size` to 300
- ✅ Check PDF isn't corrupted: `pdfinfo data.pdf`
- ✅ Split large PDFs (500+ pages) into smaller files

See [PERFORMANCE.md](PERFORMANCE.md) for detailed troubleshooting and benchmarks.

## Advanced Usage

### Different models for explainer and reviewer

Create asymmetric debates for Socratic questioning:

```yaml
models:
  explainer: llama3.1:8b-q4_K_M      # Fast initial explanations
  reviewer: qwen2.5:32b-q4_K_M       # Deep critical analysis
```

The CLI automatically instantiates separate backends when models differ.

### Suggested pairings

| Scenario | Explainer | Reviewer | Rationale |
|----------|-----------|----------|-----------|
| Fast summary | 8b-q4 | 8b-q4 | Quick pass for abstracts |
| **Balanced** ⭐ | 8b-q4 | 14b-q4 | Good speed/quality tradeoff |
| Deep analysis | 14b-q5 | 14b-q5 | Better reasoning, slower |
| Rigorous audit | 14b-q4 | 32b-q4 | Maximum scrutiny |

### Batch processing multiple papers

```bash
for paper in papers/*.pdf; do
  sed "s|path: .*|path: $paper|" config.yaml > temp_config.yaml
  python -m thedebator.cli ingest --config temp_config.yaml
  python -m thedebator.cli debate "Summarize key findings" --config temp_config.yaml
done
```

## What's New

### Version 2.0 Improvements

1. **Modern dependencies**: ChromaDB 0.5.x, PyPDF2 3.x, Pydantic 2.x
2. **Token budget management**: Prevents OOM by limiting conversation history
3. **Streaming output**: Real-time token generation for better UX
4. **Cross-page chunking**: Preserves context at page boundaries
5. **Relevance filtering**: Cosine distance threshold removes weak matches
6. **Batch ingestion**: Handle large PDFs with progress tracking
7. **Performance monitoring**: Token/sec metrics logged automatically
8. **M2 optimization**: Metal GPU acceleration enabled by default

### Breaking Changes

- **Config format**: Added `performance` section (optional, backwards compatible)
- **OllamaBackend**: Now requires `max_history_tokens` parameter (defaults to 2000)
- **VectorStore**: Uses cosine similarity instead of L2 distance
- **Dependencies**: Requires Python 3.10+ (was 3.9+)

## Project Layout

```
theDebator/
├── src/thedebator/
│   ├── cli.py              # Command-line interface
│   ├── conversation.py     # Debate orchestration with streaming
│   ├── config.py           # Configuration loading
│   ├── agents/             # Agent implementations
│   ├── backends/           # LLM backends (Ollama)
│   └── retrieval/          # PDF ingestion & vector store
├── tests/                  # Unit tests
├── config.yaml             # Runtime configuration
├── PERFORMANCE.md          # Optimization guide
└── README.md               # This file
```

## Running Tests

```bash
pytest                      # Run all tests
pytest -v                   # Verbose output
pytest tests/test_store.py  # Specific test file
```

## Notes

- 🔄 Run `ingest` before `debate` to populate the vector store
- 🎯 Change models in `config.yaml` and re-run `debate` (no re-ingestion needed)
- 💾 Vector store persists to `chroma_store/` by default
- 🚀 Keep `ollama serve` running in another terminal for instant model loading
- 📚 Export `PYTHONPATH=src` or install with `pip install -e src` before running CLI

## Performance Tips

1. **Start small**: Test with 8b-q4 + 8b-q4 for fast iteration
2. **Monitor tokens/sec**: Logs show generation speed for tuning
3. **Use streaming**: Dramatically improves perceived performance
4. **Quantize everything**: q4_K_M is the sweet spot for M2
5. **Batch large ingests**: Use `--batch-size 200+` for 100+ page papers

## License

This project uses local models only - no API keys or external services required.

## Contributing

Contributions welcome! Key areas:

- Additional backends (llama.cpp, MLX, etc.)
- More agent personalities (skeptic, synthesizer, etc.)
- Performance optimizations for M3/M4 chips
- Multi-document debates
