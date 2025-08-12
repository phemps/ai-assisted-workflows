# Nano-Agent Evaluation Framework Adaptation Proposals

Date: 2025-08-12
Author: Strategic Analysis (AI Assistant)
Status: Draft for stakeholder review

## 1. Comprehensive Analysis of Nano-Agent Framework

### 1.1 Core Purpose
Nano-Agent is an experimental, small-scale engineering MCP server focused on benchmarking agentic capabilities of multiple LLM providers (OpenAI GPT‑5 variants, Anthropic Claude variants, local Ollama models) across Performance, Speed, and Cost using a uniform execution substrate (OpenAI Agent SDK) for apples‑to‑apples comparison.

### 1.2 Architectural Highlights
- **Nested Agent Pattern**: Outer MCP server exposes a single `prompt_nano_agent` tool; internally it instantiates a fresh inner agent (OpenAI Agent SDK) per request with its own toolset (read, list, write, edit, metadata).
- **Multi-Provider Abstraction**: OpenAI-compatible endpoints for Anthropic + Ollama unify interface (providers differentiated by base URL & model naming).
- **Token & Cost Tracking**: Standardized tracking enabling cost/performance trade-off evaluation.
- **Isolation per Invocation**: Fresh inner agent reduces state bleed; improves repeatability of benchmarks.
- **Simple FS Tool Suite**: Intentionally constrained tool set keeps evaluation surface controlled.

### 1.3 Evaluation System (HOP/LOP Pattern)
- **HOP (Higher Order Prompt)**: Orchestrator prompt file that ingests one or more LOP spec files, launches target sub-agents concurrently, aggregates outputs, grades & ranks results, and formats comparison tables.
- **LOP (Lower Order Prompt)**: Test case spec: scenario prompt, expected outputs (sometimes assertions), participating @agent references, grading rubric (performance correctness criteria + maybe latency/cost weighting).
- **Parallel Execution**: All selected models run simultaneously to mitigate temporal drift.
- **Deterministic Context**: Identical prompt & sandbox environment per model.
- **Output Artifacts**: Structured markdown evaluation result files with comparative metrics.

### 1.4 Strengths
- Rapid multi-model experimentation.
- Clear trade-off visualization (speed vs accuracy vs cost).
- Extensible via new LOP test files & agent config files.
- Low cognitive overhead: single tool outwardly, complexity internalized.

### 1.5 Limitations (Relative to Your AI Assisted Workflows System)
- Narrow operational surface: simple file ops vs your broader multi-phase build, validation, quality gates, escalation.
- Metrics limited (Performance/Speed/Cost) vs your richer success metrics (coordination, robustness, productivity, escalation efficiency, duplicate detection accuracy, etc.).
- One-shot invocation focus vs long-lived multi-state workflows.
- Lacks explicit state machine, escalation logic, or continuous improvement feedback loops.

---
## 2. Mapping Nano-Agent Evaluation Principles to Current System

| Nano-Agent Concept | Equivalent / Mapping in AI Assisted Workflows | Gap / Opportunity |
|--------------------|-----------------------------------------------|-------------------|
| HOP Orchestrator (benchmark controller) | Potential new Evaluation Orchestrator role (extension of build orchestrator or separate `evaluation-orchestrator`) | Need module to schedule & parallelize scenario executions across agents & (optionally) model variants |
| LOP Test Specs | New `eval_scenarios/` definitions (markdown or YAML) encapsulating: task state path, expected artifacts, grading functions | Need richer schema supporting multi-step, state transitions, quality gates, escalation triggers |
| Parallel Model Invocation | Parallel subagent / provider variant execution (could spin synthetic agents with different model backends) | Coordination complexity with shared repo mutations (need sandbox or ephemeral worktrees) |
| Metrics: Performance, Speed, Cost | Extend existing CI metrics with: command accuracy, coordination latency, error recovery success rate, user productivity uplift | Need unified metrics adapter & storage extension |
| Isolation via Fresh Inner Agent | Use git worktrees / ephemeral temp dirs + containerized tool sandboxes per evaluation run | Requires provisioning layer & cleanup strategy |
| Unified SDK Abstraction | Already abstracted via Claude Code + possible MCP servers; extend to multi-model injection in agent definitions | Need model override and cost tracking integration |
| Result Comparison Tables | Augment `/ci-monitoring-status` or new `/evaluation-report` command to show multi-dimensional comparison | Add rendering & historical trend storage |
| Simple FS Tools | Your system uses broad automation; adopt “capability scoping” per evaluation to keep tests deterministic | Introduce capability profiles per scenario |

### Additional Mapped Metrics
| Target Success Metric | Measurement Approach (Proposed) |
|-----------------------|---------------------------------|
| Command execution accuracy | Compare actual executed shell/build/test commands vs detected expected command set (AST/log parsing) |
| Subagent coordination effectiveness | Measure number of coordination cycles, redundant attempts, escalation frequency & resolution time |
| User satisfaction/productivity | Proxy: reduction in manual interventions, cycle time per task, first-pass success %, prompt-to-commit duration |
| System robustness/error handling | Fault injection scenario success rate, mean recovery time, failure containment (no cross-task contamination) |
| Scalability & maintenance | Resource consumption per concurrent evaluation, config complexity (LOC of scenario spec), onboarding time |

---
## 3. Strategic Evaluation Proposals

### Proposal A: Baseline HOP/LOP Layer for Multi-Agent Workflow
Core Strategy: Introduce a lightweight evaluation harness mirroring nano-agent HOP/LOP to benchmark existing agents (as-is) on discrete scripted scenarios (planning, implementation, quality review) with parallel model variants only where safe (read-only phases).

### Proposal B: Ephemeral Worktree Parallel Sandbox Evaluation
Core Strategy: Extend Proposal A by sandboxing each agent/model run in isolated git worktrees (or temp directories) allowing true parallel end-to-end workflow simulation (including file mutations) with merge & diff-based grading.

### Proposal C: Continuous Adaptive Benchmark Loop (In-CI Auto Scheduling)
Core Strategy: Integrate evaluation scenarios into the continuous improvement loop; trigger targeted scenario subsets on code changes (e.g., new quality gate, agent modification) and maintain rolling performance baselines & regression detection.

### Proposal D: Fault Injection & Recovery Stress Harness
Core Strategy: Layer a resilience-focused evaluation suite injecting controlled failures (timeouts, tool errors, git conflicts, corrupted logs) to grade robustness, escalation correctness, and recovery pathways mapped to state machine transitions.

### Proposal E: Model/Agent Portfolio Optimizer with Cost-Aware Routing
Core Strategy: Instrument evaluations to feed a routing optimizer that recommends or automatically reconfigures subagents to use the most cost-effective model meeting SLA thresholds (latency, accuracy, robustness) per task category.

---
## 4. Comparative Analysis

### 4.1 Implementation Complexity (Low → High)
A < B < C < D ≈ E (optimizer logic + fault harness both advanced but different domains).

### 4.2 Coverage & Effectiveness
| Proposal | Functional Coverage | Coordination Insight | Robustness Insight | Cost Optimization | Longitudinal Trend Value |
|----------|--------------------|----------------------|--------------------|-------------------|---------------------------|
| A | Core phases (subset) | Basic (sequential metrics) | Minimal | Low | Low |
| B | Full workflow (parallel) | Medium (parallel contention) | Moderate (sandbox failure isolation) | Low | Medium |
| C | Incremental + historical | Medium-High | Moderate | Medium (trend-based) | High |
| D | Failure modes & escalation | High (stress patterns) | High (resilience focus) | Low | Medium |
| E | Depends on feeding data from A–D | Medium (routing decisions) | Indirect (via penalty metrics) | High | High (adaptive routing evolution) |

### 4.3 Resource Requirements Summary
| Proposal | Engineering Effort | Runtime Cost | Infra Needs | Data Volume | Maintenance Load |
|----------|--------------------|-------------|------------|------------|------------------|
| A | ~1–2 weeks | Low | None (reuse current) | Small | Low |
| B | ~3–4 weeks | Medium (parallel runs) | Worktree / container mgmt | Medium | Medium |
| C | ~4 weeks (after B) | Medium (scheduled runs) | CI integration, storage | Large (history) | Medium |
| D | ~3–5 weeks (parallel stream) | Medium-High (fault cases) | Fault inject layer (mocks, interceptors) | Medium | Medium-High |
| E | ~5–6 weeks (post A/B data) | Variable (model exploration) | Optimization service (scheduler) | Large (metrics + decisions) | High (model drift, pricing changes) |

### 4.4 Strengths & Limitations
| Proposal | Strengths | Limitations |
|----------|-----------|-------------|
| A | Fast to implement, establishes baseline comparability | Limited depth; no isolation for conflicting writes |
| B | Realistic parallelism; safe mutation isolation; diff-based grading | Higher infra complexity; merge conflict synthesis logic needed |
| C | Provides trend analytics & regression detection; integrates with existing CI quality ethos | Requires stable scenario catalog & noise filtering |
| D | Surfaces hidden coordination & escalation weaknesses early | Artificial failure design risk; tuning required to avoid false negatives |
| E | Direct cost/performance ROI; dynamic model allocation; supports scaling | Needs robust, reliable metric inputs; potential instability if optimizer overfits |

---
## 5. Discussion Points

### 5.1 Key Decisions Requiring Stakeholder Input
1. Scope of initial metric set (Minimal: accuracy/latency vs Expanded: escalation correctness, recovery time).
2. Parallel mutation policy (Adopt worktrees now vs defer until post-baseline).
3. Fault injection priority (Include in MVP vs stage later).
4. Automated routing autonomy level (Recommendation-only vs auto-reconfiguration).
5. Storage & retention strategy for evaluation artifacts (Local files vs structured DB).

### 5.2 Potential Challenges & Mitigations
| Challenge | Impact | Mitigation |
|----------|--------|------------|
| Non-deterministic LLM outputs inflate variance | Reduces confidence in regression detection | Multi-run averaging + statistical control limits (EWMA) |
| Parallel runs cause resource contention | Slower eval cycles | Concurrency limiter + priority queue |
| Scenario spec drift vs real workflows | Misaligned benchmarks | Link scenarios to state machine phases with version tags |
| Fault injection overfitting agents to synthetic failures | Reduced real-world resilience | Periodically refresh fault catalog; sample real incident logs |
| Cost escalation with broad model matrix | Budget overruns | Dynamic pruning of underperforming model variants (top-K retention) |
| Optimizer causing oscillations in model selection | Instability for users | Introduce hysteresis & minimum dwell time per routing decision |

### 5.3 Recommended Proposal Prioritization (Incremental Roadmap)
1. Phase 1: Implement Proposal A (Baseline) + minimal metric schema.
2. Phase 2: Implement Proposal B (Parallel Sandbox) enabling safe expansion of scenario complexity.
3. Phase 3: Layer Proposal C (Continuous Loop) for trend analytics & regression gates.
4. Phase 4: Parallel track start of Proposal D (Fault Harness) focusing on top 3 failure archetypes first (tool error, timeout, git conflict).
5. Phase 5: Implement Proposal E once 4+ weeks of stable metrics collected.

---
## 6. Key Insights
- Nano-Agent’s HOP/LOP offers a composable, version-controlled evaluation spec model directly portable as `scenario` definitions; your system can extend it with richer life-cycle & escalation semantics.
- Isolation & comparability principles (fresh agent, unified tooling) map naturally to using ephemeral worktrees + constrained capability profiles for deterministic evaluations.
- Your broader success metrics require multi-dimensional grading beyond correctness (coordination efficiency, recovery success, productivity proxies) suggesting a pluggable scoring pipeline.
- Embedding evaluation into the continuous improvement loop transforms benchmarks from one-off experiments into enforceable quality signals.
- Cost-performance optimization becomes feasible only after disciplined metric collection & variance control.

---
## 7. Recommended Next Steps

### Immediate (Week 1–2)
- Approve baseline scenario schema (YAML/MD) including: id, phase coverage, preconditions, prompt(s), expected artifacts, grading rubric functions.
- Implement Proposal A harness: `/evaluate-scenarios` command, scenario loader, sequential execution, metrics recording (exec_time, success_flag, command_accuracy, token_usage placeholder).
- Define metric storage contract (JSON Lines under `shared/metrics/eval/` or lightweight SQLite).

### Short Term (Week 3–5)
- Add parallel execution with read-only phase guardrails → progress to Proposal B.
- Introduce worktree sandbox creation utility (reuse existing `todo-worktree` patterns) with deterministic cleanup & diff capture.
- Implement basic statistical variance controls (store run count, stddev, flag unstable scenarios).

### Mid Term (Week 6–9)
- Integrate with CI: auto-run critical scenario subset on PR affecting agent logic or quality gate config (Proposal C).
- Add early fault injection prototypes (Proposal D initial cases).
- Start collecting cost metrics via provider-specific token/cost sources.

### Longer Term (Week 10+)
- Expand fault library; add escalation path verification assertions.
- Build routing optimizer prototype (Proposal E) with simple heuristic (Pareto frontier selection) before advanced ML.
- Add dashboard summarizing trends (success rate by phase, MTTR, cost per successful task) & anomaly detection triggers.

### Artifacts to Create (Planned)
1. `docs/eval-scenarios-schema.md`
2. `evaluation/runner/` module (scenario loader, executor, metric emitter)
3. `evaluation/scenarios/` initial set (3–5 baseline scenarios)
4. Metric adapter: `shared/ci/metrics/evaluation_metrics.py`
5. Fault injector scaffolding: `evaluation/faults/` (stubs)

---
## 8. Open Questions for Stakeholders
1. Acceptable additional monthly evaluation cost ceiling? (Needed for model matrix size decisions.)
2. Preferred persistence layer (file-based vs embedded DB) for evaluation history?
3. Minimum stability period required before allowing optimizer to alter subagent model configs?
4. Are there compliance or data handling constraints impacting storage of evaluation transcripts?
5. Priority order among robustness vs cost optimization vs speed improvements?

---
## 9. Glossary (Context Alignment)
- **Scenario (LOP analogue)**: Structured multi-phase test of agent coordination & quality gates.
- **Evaluation Orchestrator (HOP analogue)**: Command/process that schedules and grades scenarios across agent/model variants.
- **Capability Profile**: Whitelist of tools enabled for the evaluation run to ensure determinism.
- **Command Execution Accuracy**: % of required detected commands actually executed successfully (build/test/lint) in correct order.
- **Escalation Efficacy**: Rate of successful resolution post-escalation without human intervention.
- **Recovery Time**: Elapsed time from injected failure detection to restored nominal state.

---
## 10. Summary
Adopting a staged adaptation of nano-agent’s evaluation paradigm provides a low-risk pathway to rigorous, multi-dimensional benchmarking of your multi-agent workflow system. Starting lean (Proposal A) establishes foundational comparability; advancing through sandbox isolation, continuous benchmarking, fault resilience, and cost-aware optimization successively addresses your defined success metrics while maintaining incremental complexity control. This roadmap supports measurable improvements in command accuracy, coordination effectiveness, robustness, and cost efficiency.

> Recommendation: Proceed with Proposal A immediately; schedule design review for scenario schema + metric contract within the next development cycle.
