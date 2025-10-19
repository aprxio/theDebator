# theDebator – Backlog and TODO

Scope

- Plan for future features and modes. No implementation in this commit.
- Targets post v2.0 (Apple Silicon-optimized) release.

Guiding principles

- Keep streaming, token budgeting, and cross-page RAG first-class.
- Favor quality/groundedness over length; show sources.
- Minimal deps; use existing Ollama + Chroma where possible.

Milestones

Milestone v2.1 – Quick wins (high impact, low risk)

- [ ] Evidence Cards in answers
  - Show per-citation: page number, short quote/snippet, similarity score, and de-duplicated source id.
  - Acceptance: Every cited claim lists ≥1 card with page anchor; duplicates collapsed; threshold configurable.
  - Depends: retrieval/store distances + metadata; conversation output formatter.
  - Tests: snapshot of a response includes cards; low-relevance chunks filtered.

- [ ] RAG Reranking stage
  - Add a rerank step on top-k (LLM rerank default; local cross-encoder optional later).
  - Acceptance: reranking improves MAP@k on a small canned set; latency budget < +400 ms for k<=10.
  - Depends: retrieval pipeline hook; config.yaml toggle.

- [ ] Transcript export (Markdown + JSONL)
  - CLI: flag to save full conversation with inline footnotes, page anchors, and citations appendix.
  - Acceptance: stable schema; reproducible export; filenames include timestamp and collection hash.
  - Depends: conversation orchestrator; config for default export dir.

- [ ] Config profiles
  - Profiles: fast, balanced, quality; selectable via CLI/config.
  - Acceptance: profile switch adjusts models, top_k, chunking, history budget without editing base config.
  - Depends: config loader with profile overlay.

- [ ] Retrieval/Prompt cache
  - Cache key: normalized query + collection content hash + top_k + rerank on/off.
  - Acceptance: cache hit ratio visible in logs; fallback safe on schema mismatch; TTL configurable.
  - Depends: lightweight disk cache; existing content-hash support.

- [ ] CLI polish
  - Round timers and token/sec per agent; clearer progress banners; truncation notices with counts.
  - Acceptance: logs show timing, tok/s, truncation summary each round.

Milestone v2.2 – Core extensions (medium effort)

- [ ] Conversation modes (MVP set)
  - Socratic Tutor, Peer-Review Triad, Fact-Check Clinic, Decision Memo, Rubber-Duck Explainer.
  - Acceptance: selectable via CLI/config; different role prompts and turn orders; all support streaming/export.
  - Depends: conversation orchestrator templating; agent role configs.

- [ ] Claim and stance tracking
  - Extract numbered claims; per-agent stance (support/oppose/neutral) with confidence.
  - Acceptance: claim table appended to export; IDs stable across rounds; links to evidence cards.
  - Depends: lightweight IE pass using existing LLM backend.

- [ ] Groundedness guardrails
  - Sentence-level re-check against retrieved chunks; flag or downweight ungrounded lines.
  - Acceptance: groundedness score per answer; warnings for low-scored spans; toggle in config.
  - Depends: retrieval context window and similarity API.

- [ ] Multi-document RAG
  - Named collections; per-session filters; cross-doc dedup and source diversity.
  - Acceptance: can ingest/select multiple collections; response shows doc identifiers and diversity count.
  - Depends: store API extension; CLI collection selection.

- [ ] Memory and history control
  - Rolling summaries; per-agent memory slots with budgets; show what was pruned/summarized.
  - Acceptance: memory summaries persisted per session; history fits within budget deterministically.

- [ ] Local embeddings option
  - Allow local small embedding model (fallback to remote/ollama if unset).
  - Acceptance: switch embedding backend via config; ingestion and query parity confirmed.

Milestone v2.3 – Big bets (higher effort)

- [ ] Panel of Experts with consensus
  - Methods/Stats/Ethics experts + synthesizer; show disagreements and final consensus.
  - Acceptance: consensus section with confidence; traceable per-expert citations.

- [ ] Courtroom mode
  - Prosecution/Defense present exhibits (chunks); Judge issues ruling with findings of fact.
  - Acceptance: exhibits listed with page anchors; ruling template consistent.

- [ ] Argument graph visualization (export)
  - Graph of claims, evidence, counterclaims; export to JSON (and optional SVG later).
  - Acceptance: JSON contains nodes/edges with citation refs; deterministic IDs.

- [ ] Calibration game
  - Agent assigns probabilities; track Brier/log scores across sessions.
  - Acceptance: scorecard exported; session-to-session progress tracked.

- [ ] Tournament bracket (model bake-off)
  - Multiple agents/models; knockout rounds with scoring rubric.
  - Acceptance: bracket summary; per-match rubric scores and winner.

Quality, evaluation, and ops

- [ ] Evaluation harness
  - Small benchmark set; metrics: faithfulness, citation precision/recall, tok/s.
  - Acceptance: single command runs eval; outputs CSV + summary table.

- [ ] Safety and controls
  - Per-mode guardrails (no speculation without evidence; max claim risk level).
  - Acceptance: violations flagged inline; can block send based on policy in strict mode.

- [ ] Documentation updates
  - README: new modes, examples, config profiles; PERFORMANCE: rerank/cache tuning.
  - Acceptance: concise sections with updated CLI examples.

- [ ] VS Code tasks and launch
  - Add tasks.json to run ingest, debate, and tests; optional launch config.
  - Acceptance: one-click tasks work on macOS; documented in README.
  - Note: follow repository instructions for creating tasks in .vscode without changing root folder.

Instrumentation

- [ ] Telemetry (local only)
  - Session summary log: rounds, tok/s, cache hits, rerank latency, groundedness score.
  - Acceptance: structured log file per session; can be disabled.

Design notes and dependencies

- Reuse current strengths: streaming output, history budgets, cross-page chunking, cosine similarity, content-hash caching.
- Keep dependencies optional:
  - Reranker default via LLM prompt; optional cross-encoder later.
  - TUI (if added later) via lightweight text UI; avoid heavy frameworks initially.
- Config surface:
  - Add toggles: rerank.enabled, cache.enabled, profiles, groundedness.min_score, modes.

Test plan (high level)

- Deterministic snapshots for export and evidence cards.
- Regression tests for retrieval ranking and filtering thresholds.
- Mode selection E2E tests: Socratic, Fact-Check, Decision Memo.
- Performance guardrails: ensure tok/s degradation < 10% after features toggled on.

Out of scope (for now)

- External web search, complex tool orchestration, cloud services, or non-local telemetry.

Changelog placeholders

- v2.1: Evidence Cards, rerank, export, profiles, cache, CLI polish.
- v2.2: New modes (MVP), claims/stance, groundedness, multi-doc, memory, local embeddings.
- v2.3: Experts + consensus, courtroom, argument graph, calibration, tournament.

Owner notes

- Keep PRs small: 1 feature per PR with docs and tests.
- Feature flags default off unless low risk and measured.
