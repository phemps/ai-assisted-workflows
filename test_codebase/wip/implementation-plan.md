# Evaluation Framework Implementation Plan

Date: 2025-08-12
Status: Draft for Execution
Owner: Evaluation Orchestrator Working Group

## 1. Phase Overview

| Phase     | Goal                          | Duration (est) | Key KPIs  |
| --------- | ----------------------------- | -------------- | --------- |
| P1        | Core skeleton + baseline KPIs | 1–1.5 weeks    | K1,K9,K11 |
| P2        | Quality instrumentation       | 0.5–1 week     | K2,K13    |
| P3        | Code quality enrichment       | 1 week         | K3,K4     |
| P4        | Structural complexity metrics | 0.5–1 week     | K5,K6     |
| P5        | Security & governance         | 1 week         | K7,K8     |
| P6        | Feature-level granularity     | 0.5–1 week     | K10,K12   |
| P7        | Resilience & escalation       | 1–1.5 weeks    | K14,K15   |
| Hardening | Optimization + dashboard      | 1 week         | Composite |

## 2. Detailed Tasks By Phase

### Phase 1: Core Skeleton

Deliverables:

- `evaluation/scenarios/challenge_v1.yaml`
- `evaluation/orchestrator/scenario_loader.py`
- `evaluation/orchestrator/run_coordinator.py`
- `evaluation/instrumentation/event_bus.py`
- Adapters: `tool_adapter.py`, `token_adapter.py`, `state_adapter.py`
- `evaluation/kpi/engine.py` (calculator registry stub)
- KPI calculators: K1FailedToolCalls, K9TokenSpend, K11TaskRuntime
- Report builder skeleton `evaluation/report/report_builder.py`
- CLI/command `/evaluate-scenarios`
- Metrics storage layout `.metrics/events` & `.metrics/reports`
  Steps:

1. Define pydantic models (Scenario, Variant, Event, KPIResult).
2. Implement EventBus (buffer, flush policies, JSONL writer).
3. Instrument tool executor wrapper (emit TOOL events).
4. Patch token usage (wrap LLM API module) emitting TOKEN events.
5. Add state transition hook in plan-manager emitting STATE events.
6. Baseline scenario YAML + plan file stub.
7. RunCoordinator: sequential execution, sandbox = current workspace copy (placeholder).
8. KPI Engine: simple pass over events.
9. Report: list KPIs, raw values, thresholds placeholder.
10. Smoke test end-to-end; persist first report.
    Exit Criteria: Report produced with K1,K9,K11 for challenge_v1.

### Phase 2: Quality Instrumentation

Deliverables:

- Quality gate hook `quality_adapter.py`
- KPI calculators: K2QualityGateRerunAvg, K13CommandAccuracy
- Expected vs executed command extractor.
  Steps:

1. Hook quality monitor entry/exit; record expected commands list.
2. Sequence alignment (LCS) calculator.
3. Add rerun counter from state transitions (quality_review→in_progress cycles).
4. Update report grouping (Accuracy bucket includes K13).
   Exit Criteria: Rerun, accuracy values stable across 3 runs.

### Phase 3: Code Quality Enrichment

Deliverables:

- Placeholder scanner `evaluation/analysis/placeholder_scanner.py`
- Integration call post-commit.
- Duplicate analyzer snapshot wrapper.
- KPI calculators: K3PlaceholderIncidents, K4DuplicatePercent.
  Steps:

1. Implement diff parser (git diff --unified=0) for added lines.
2. Pattern matching + density metrics.
3. Run duplication analyzer at end; compute duplicate_line_equivalents.
   Exit Criteria: K3 & K4 appear; false positive rate <10% on seeded fixtures.

### Phase 4: Structural Complexity Metrics

Deliverables:

- CouplingAnalyzer + Lizard wrapper integration into snapshot runner.
- KPI calculators: K5ArchitectureScore, K6CodeComplexityScore.
  Steps:

1. Create normalization cache (rolling window JSON).
2. Compute composite scores.
   Exit Criteria: Scores reproducible ±1pt over repeated runs absent code changes.

### Phase 5: Security & Governance

Deliverables:

- Vulnerability scanner snapshot integration.
- Feature creep detector `feature_detector.py` (plan parsing + artifact diff heuristics).
- KPI calculators: K7SecurityIssues, K8FeatureCreep.
  Exit Criteria: Injected synthetic extra feature increments creep count; security issues aggregated.

### Phase 6: Feature-Level Granularity

Deliverables:

- Feature token mapping (start/end correlation IDs).
- KPI calculators: K10TokenPerFeature, K12FeatureCommitCycleTime.
- Update report to show per-feature breakdown table.
  Exit Criteria: Each planned feature row populated with tokens & cycle time.

### Phase 7: Resilience & Escalation

Deliverables:

- Fault injector framework `faults/` (config, injector, registry).
- Escalation event instrumentation (CTO & human thresholds).
- KPI calculators: K14EscalationEffectiveness, K15RecoveryMTTR.
  Exit Criteria: Simulated injected timeout yields recovery metrics; escalation resolution recorded.

### Hardening & Optimization

Deliverables:

- Parallel sandbox execution (worktree manager).
- Scenario matrix support.
- Composite scoring rubric weights implementation.
- Historical aggregation & simple dashboard `.metrics/dashboards/index.md`.
- Optional SQLite ingestion module.
- Stability & performance profiling (overhead <8%).

## 3. File Layout (Proposed)

```
evaluation/
  scenarios/
    challenge_v1.yaml
  orchestrator/
    __init__.py
    scenario_loader.py
    run_coordinator.py
    sandbox_manager.py
    phase_monitor.py
  instrumentation/
    __init__.py
    event_bus.py
    tool_adapter.py
    token_adapter.py
    state_adapter.py
    quality_adapter.py
  analysis/
    __init__.py
    placeholder_scanner.py
    feature_detector.py
  kpi/
    __init__.py
    engine.py
    calculators/
      k1_failed_tool_calls.py
      k2_quality_reruns.py
      k3_placeholder_incidents.py
      k4_duplicate_percent.py
      k5_architecture_score.py
      k6_code_complexity_score.py
      k7_security_issues.py
      k8_feature_creep.py
      k9_token_spend.py
      k10_token_per_feature.py
      k11_task_runtime.py
      k12_feature_cycle_time.py
      k13_command_accuracy.py
      k14_escalation_effectiveness.py
      k15_recovery_mttr.py
  report/
    __init__.py
    report_builder.py
  faults/ (Phase 7)
    __init__.py
    fault_injector.py
    profiles/
  optimization/ (Later)
    router.py
```

## 4. Cross-Cutting Concerns

- Logging: Structured JSON to `.metrics/logs/eval.log`.
- Config: `evaluation/config.yaml` (threshold overrides, concurrency).
- Versioning: `evaluation/VERSION` used in reports.
- Performance: Buffer size, flush thresholds configurable.

## 5. Estimation & Dependencies

- Phases independent except calculators relying on prior instrumentation.
- Parallelization: P2 can start while P1 stabilization tests run.

## 6. Testing Strategy

- Unit: calculators (deterministic sample event sets).
- Integration: scenario dry-run (mock agents) verifying event emission counts.
- Regression: replay events to recompute KPIs (idempotency test).
- Performance: measure overhead with instrumentation toggled on/off.

## 7. Acceptance Criteria Summary

| Phase | Criteria (Abbrev)                                               |
| ----- | --------------------------------------------------------------- |
| P1    | Report JSON+MD with K1,K9,K11; event coverage ≥95% tools        |
| P2    | K13 accuracy stable; rerun avg reported                         |
| P3    | Placeholder FP<10%; duplicate % computed                        |
| P4    | Architecture & Complexity scores reproducible                   |
| P5    | Feature creep detection works; security issues counted          |
| P6    | Per-feature token and cycle time table                          |
| P7    | Fault injection produces K15; escalation effectiveness computed |

## 8. Risks & Mitigations (Incremental)

- Overhead: measure each phase; budget <8% runtime.
- Drift in normalization windows: persist baselines; lock during evaluation cycles.
- Tool wrapper conflicts: feature flag instrumentation on/off.

## 9. Go / No-Go Gates

- After P1: Confirm data fidelity before expanding.
- After P3: Validate code quality metrics accuracy before structural scoring.
- After P5: Governance metrics accuracy check (manual review of creep detection).

## 10. Next Steps (Immediate)

1. Approve plan structure & file layout.
2. Create initial `evaluation/scenarios/challenge_v1.yaml` placeholder.
3. Begin Phase 1 scaffolding.

---

Pending approval to commence Phase 1 implementation.
