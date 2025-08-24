# Evaluation Framework Solution Design

(Existing design content consolidated—see prior assistant response. This file will house the architecture, components, data flows, interface contracts, risks, and open decisions.)

## 1. Summary

A nano-agent inspired evaluation framework providing scenario-driven, sandboxed, multi-model benchmarking of the multi-agent workflow using KPI instrumentation.

## 2. Core Components

- Scenario Specification Layer (YAML)
- Evaluation Orchestrator (command + coordinator)
- Instrumentation Fabric (event bus + adapters)
- Sandbox Manager (worktree/temp copy strategies)
- KPI Engine (calculator registry)
- Analyzer Snapshot Runner (reuses existing analyzers)
- Report Generator (JSON + Markdown)
- Variant Matrix Runner (model/strategy combinations)
- Fault Injection Layer (phase 2+)
- Optimization / Routing Advisor (later)

## 3. Scenario YAML Schema (v1)

```yaml
id: challenge_v1
description: Baseline feature delivery benchmark
plan_file: baseline/PLAN.md
phases: [planning, implementation, quality, commit]
features_expected: 6
kpis: [K1, K2, K3, K4, K5, K6, K7, K8, K9, K10, K11, K12, K13]
variants:
  models:
    - id: gpt-5-mini
    - id: claude-sonnet-4
    - id: gpt-oss:20b
  strategies:
    - name: baseline
      flags: []
    - name: prototype_mode
      flags: [--prototype]
sandbox:
  strategy: git_worktree
  mutable: true
timeouts:
  total_minutes: 45
  phase_overrides:
    implementation: 25
scoring:
  weights:
    accuracy: 0.35
    quality: 0.25
    robustness: 0.15
    efficiency: 0.15
    governance: 0.10
```

## 4. Event Model

See `kpi-specification.md` for detailed event + KPI schemas.

## 5. Data Flow Sequence

1. Load scenario → build run plan
2. For each variant: create sandbox, start event session
3. Drive agents via existing commands; instrumentation emits events
4. Phase boundaries trigger analyzer snapshots
5. On completion: compute KPIs, score, store report
6. Aggregate comparisons across variants

## 6. KPI Group to Composite Score Mapping

- Accuracy: Command Execution Accuracy, Feature Completion Ratio
- Quality: Complexity Score, Duplicate %, Security Issues penalty
- Robustness: Escalation Effectiveness, Recovery MTTR
- Efficiency: Token Spend vs Baseline, Runtime vs Baseline
- Governance: Feature Creep, Placeholder Density

## 7. Interfaces (Abbreviated)

```python
class ScenarioLoader: def load(id) -> Scenario
class RunCoordinator: def execute(run_manifest) -> RunResult
class SandboxManager: def provision(run) -> Path; def finalize(run)
class EventBus: def emit(type, payload, **ctx); def flush()
class KPICalculator: id; def compute(events, snapshots, context) -> KPIResult
class ReportBuilder: def build(run_results, scenario) -> Report
```

## 8. Sandboxing Strategies

- git_worktree (default)
- temp_copy (fallback)
  Selection via scenario.sandbox.strategy.

## 9. Fault Injection (Phase 4)

Profiles declare triggers (phase, counter) and actions (delay, tool error, git conflict).

## 10. Risks & Mitigations

See original design (summarized): isolation, overhead, variance, drift, overfitting.

## 11. Open Decisions

- Confirm KPI subset for MVP (proposed: K1,K2,K9,K11,K13)
- Storage backend (JSONL + optional SQLite)
- Parallelism default (sequential first)

## 12. Future Extensions

- Historical dashboard
- Optimization routing advisor
- Scenario packs & rotation

(Refer to `implementation-plan.md` for phased execution details.)
