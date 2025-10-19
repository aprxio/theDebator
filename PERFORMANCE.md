# Performance Guide for M2 MacBook Pro

This guide provides optimization tips for running theDebator on Apple Silicon, specifically targeting the M2 MacBook Pro with 32GB RAM.

## Quick Start: Recommended Configuration

For optimal performance on M2 32GB, use these settings in `config.yaml`:

```yaml
models:
  explainer: llama3.1:8b-q4_K_M    # ~5GB VRAM, 40-60 tok/s
  reviewer: qwen2.5:14b-q4_K_M     # ~9GB VRAM, 20-30 tok/s

retrieval:
  chunk_size: 1000
  chunk_overlap: 250
  top_k: 5
  max_history_tokens: 2000

performance:
  batch_size: 150
  enable_streaming: true
```

## Model Selection

### Quantization Levels

Quantized models run 2-3x faster with minimal quality loss:

| Quantization | Size Reduction | Speed Gain | Quality | Best For |
|-------------|----------------|------------|---------|----------|
| `q4_K_M` | 70% smaller | 2.5x faster | 95% | **Recommended for M2** |
| `q5_K_M` | 60% smaller | 2x faster | 97% | Quality-critical debates |
| `q8_0` | 40% smaller | 1.5x faster | 99% | When VRAM allows |
| (none) | Full size | Baseline | 100% | Avoid on M2 |

### Model Recommendations by Use Case

#### Fast Iteration (Development)

```yaml
models:
  explainer: llama3.1:8b-q4_K_M
  reviewer: llama3.1:8b-q4_K_M
rounds: 2
```

**Performance**: ~50 tok/s both agents, <2 min per debate

#### Balanced Quality/Speed (Production)

```yaml
models:
  explainer: llama3.1:8b-q4_K_M
  reviewer: qwen2.5:14b-q4_K_M
rounds: 3
```

**Performance**: 40-60 tok/s explainer, 20-30 tok/s reviewer, ~5 min per debate

#### Maximum Quality (Heavy Papers)

```yaml
models:
  explainer: qwen2.5:14b-q5_K_M
  reviewer: qwen2.5:32b-q4_K_M  # Requires 18GB VRAM
rounds: 3
```

**Performance**: 15-25 tok/s both agents, 10-15 min per debate

### Installing Quantized Models

```bash
# List available quantizations for a model
ollama show llama3.1:8b

# Pull specific quantization
ollama pull llama3.1:8b-q4_K_M
ollama pull qwen2.5:14b-q4_K_M

# Verify installation
ollama list
```

## Memory Management

### Token Budget Tuning

The `max_history_tokens` setting prevents OOM crashes with long debates:

```yaml
retrieval:
  max_history_tokens: 2000  # Default, good for 3-5 rounds
  # max_history_tokens: 3000  # For deeper debates (6+ rounds)
  # max_history_tokens: 1000  # For 70B+ models with limited memory
```

**Formula**: `max_history_tokens = (Available_RAM_GB - Model_VRAM_GB) * 100`

Example for M2 32GB:

- 8B model (~5GB): `(32 - 5) * 100 = 2700` tokens max
- 14B model (~9GB): `(32 - 9) * 100 = 2300` tokens max
- 32B model (~18GB): `(32 - 18) * 100 = 1400` tokens max

### Monitoring Memory Usage

```bash
# Check VRAM usage during debate
sudo powermetrics --samplers gpu_power -i 1000 -n 1

# Monitor overall RAM
htop
```

If you see "Metal allocation failed" errors, reduce `max_history_tokens` or use smaller models.

## Retrieval Optimization

### Chunk Size vs. Context Quality

| Chunk Size | Use Case | Pros | Cons |
|-----------|----------|------|------|
| 600-800 | Short papers (5-20 pages) | Precise citations | May miss context |
| 1000-1200 | Standard papers (20-50 pages) | **Balanced** | Moderate tokens |
| 1500-2000 | Long papers (50+ pages) | Maximum context | High token cost |

**Recommendation**: Start with 1000, increase if citations are incomplete.

### Top-K Selection

```yaml
retrieval:
  top_k: 3   # Fast, focused answers (good for summaries)
  top_k: 5   # **Recommended** - comprehensive evidence
  top_k: 7   # Deep analysis, longer prompts
```

**Rule of thumb**: `top_k = ceil(paper_pages / 10)`, clamped to 3-7.

### Relevance Filtering

The VectorStore now filters chunks with cosine distance > 0.5:

```python
# In store.py
if dist > 0.5:
    continue  # Skip low-relevance chunks
```

To adjust threshold, edit `src/thedebator/retrieval/store.py`:

```python
# More strict (fewer but higher quality chunks)
if dist > 0.3:
    continue

# More permissive (more chunks, some noise)
if dist > 0.7:
    continue
```

## Streaming Output

Enable streaming for real-time feedback during long generations:

```bash
# Streaming enabled (default)
python -m thedebator.cli debate "What is the methodology?" --stream

# Disable streaming
python -m thedebator.cli debate "What is the methodology?" --no-stream
```

Streaming adds negligible overhead (<1% slower) but dramatically improves UX.

## Batch Ingestion

For large PDFs (100+ pages), use batching:

```bash
python -m thedebator.cli ingest --batch-size 200
```

| Batch Size | Speed | Memory | Use Case |
|-----------|-------|--------|----------|
| 50 | Slower | Low | Testing |
| 150 | **Balanced** | Medium | Default |
| 300 | Fastest | High | Production ingestion |

## Troubleshooting

### Slow Generation (<10 tok/s)

**Symptoms**: Model generates slowly, high CPU usage

**Fixes**:

1. Verify Metal acceleration: check logs for "num_gpu: 1"
2. Use quantized models (q4_K_M or q5_K_M)
3. Reduce `max_history_tokens` to 1500
4. Close other apps to free VRAM

```bash
# Verify Ollama is using GPU
ollama ps
# Should show "Metal" in output

# Restart Ollama with explicit GPU
killall ollama
ollama serve
```

### Out of Memory Crashes

**Symptoms**: "Metal allocation failed", process killed

**Fixes**:

1. Reduce `max_history_tokens` to 1000
2. Lower `top_k` to 3
3. Use smaller models (8B instead of 14B)
4. Reduce `chunk_size` to 800

### Poor Citation Quality

**Symptoms**: Agents don't reference paper, generic answers

**Fixes**:

1. Increase `chunk_size` to 1500
2. Increase `top_k` to 7
3. Re-run `ingest` after config changes
4. Check paper.pdf has extractable text (not scanned images)

### Ingestion Timeout

**Symptoms**: Ingestion hangs on large PDFs

**Fixes**:

1. Increase `--batch-size` to 300
2. Check PDF isn't corrupted: `pdfinfo data.pdf`
3. Split PDF into smaller files if 500+ pages

## Benchmarks (M2 32GB)

### Model Performance

| Model | Quant | VRAM | Tokens/sec | Quality | Recommended |
|-------|-------|------|------------|---------|-------------|
| llama3.1:8b | q4_K_M | 5GB | 50-60 | ⭐⭐⭐⭐ | ✅ Yes |
| llama3.1:8b | q5_K_M | 6GB | 40-50 | ⭐⭐⭐⭐⭐ | ✅ Yes |
| qwen2.5:14b | q4_K_M | 9GB | 25-30 | ⭐⭐⭐⭐⭐ | ✅ Yes |
| qwen2.5:14b | q5_K_M | 11GB | 20-25 | ⭐⭐⭐⭐⭐ | ✅ Yes |
| qwen2.5:32b | q4_K_M | 18GB | 12-15 | ⭐⭐⭐⭐⭐ | ⚠️ Heavy |
| llama3.1:70b | q4_K_M | 35GB | N/A | N/A | ❌ Too large |

### Debate Duration (3 rounds)

| Configuration | Total Time | Per Round |
|--------------|-----------|-----------|
| 8b-q4 + 8b-q4 | 1.5 min | 30 sec |
| 8b-q4 + 14b-q4 | 4 min | 80 sec |
| 14b-q5 + 14b-q5 | 8 min | 160 sec |
| 14b-q4 + 32b-q4 | 15 min | 300 sec |

### Ingestion Speed

| Paper Size | Chunks | Default (batch=150) | Fast (batch=300) |
|-----------|--------|---------------------|------------------|
| 10 pages | ~100 | 5 sec | 3 sec |
| 50 pages | ~500 | 20 sec | 12 sec |
| 200 pages | ~2000 | 90 sec | 50 sec |

## Advanced: Custom Quantization

To create custom quantizations with llama.cpp:

```bash
# Install llama.cpp
brew install llama.cpp

# Quantize a model
llama-quantize model.gguf model-q4_K_M.gguf q4_K_M

# Import to Ollama
ollama create mymodel -f Modelfile
```

See [Ollama documentation](https://github.com/ollama/ollama/blob/main/docs/import.md) for details.

## Recommended Workflow

1. **Start with fast config** (8b + 8b, 2 rounds) to validate setup
2. **Ingest once** with optimized settings
3. **Iterate on debate topic** with streaming enabled
4. **Scale up models** (8b → 14b → 32b) as needed
5. **Monitor performance** with token/sec metrics

## Getting Help

If performance issues persist:

1. Check Ollama logs: `tail -f ~/.ollama/logs/server.log`
2. Verify Metal support: `system_profiler SPDisplaysDataType | grep Metal`
3. Update Ollama: `brew upgrade ollama`
4. Report issues with token/sec metrics and model config
