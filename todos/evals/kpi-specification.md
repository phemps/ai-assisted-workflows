# Workflow KPI Specification

Date: 2025-08-12
Status: Draft (Review Requested)
Owner: Evaluation Orchestrator Working Group

## 1. Scope & Objectives

Define precise, automatable KPIs to evaluate multi-agent workflow performance across implementation, quality, robustness, efficiency, and governance. KPIs must be:

- Deterministic (same raw events → same value)
- Source-mapped (explicit data origin)
- Normalized (scalable across project sizes)
- Correlatable (feature/task, model, scenario)

## 2. KPI Catalog

| ID  | KPI                           | Definition                                                                           | Formula (Pseudo)                                                                     | Data Sources                                                     | Update Timing                    |
| --- | ----------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------- | -------------------------------- |
| K1  | Failed Tool Calls             | Count of tool invocations returning error/timeout/invalid output                     | COUNT(events where event.type=TOOL and success=false)                                | Instrumented tool wrapper                                        | Real-time (per call)             |
| K2  | Quality Gate Rerun Avg        | Average number of quality gate cycles per completed task                             | SUM(quality_review_retries_per_task)/tasks_completed                                 | State transitions (quality_review→in_progress), plan-manager     | On task completion               |
| K3  | Placeholder Code Incidents    | Count & density of placeholder patterns introduced in feature implementation         | COUNT(placeholder_hits); density=placeholder_lines/new_code_lines                    | Commit diff scanner, placeholder regex set                       | Post-commit & scenario end       |
| K4  | Duplicate Code %              | % of total logical lines considered part of duplicate pairs (confidence ≥ threshold) | (duplicate_line_equivalents / total_analyzable_lines)\*100                           | CodeDuplicationAnalyzer composite + line mapping                 | Scheduled (post-task)            |
| K5  | Architecture Complexity Score | Weighted composite of coupling metrics normalized 0–100 (higher better)              | 100 - normalize(w_fan_in*Z(fan_in_hi)+w_fan_out*Z(fan_out_hi)+w_cycles\*cycle_ratio) | CouplingAnalyzer metadata                                        | Scheduled (daily / scenario end) |
| K6  | Code Complexity Score         | 100 - normalize(weighted avg over cyclomatic, long fn %, param excess %)             | LizardComplexityAnalyzer findings                                                    | Scheduled (post-task batch)                                      |
| K7  | Security Issues (Med+)        | Count of vulnerabilities severity ≥ medium                                           | COUNT(vuln_findings severity in {medium,high,critical})                              | VulnerabilityScanner                                             | Post-scan (daily / scenario end) |
| K8  | Feature Creep Count           | Features implemented not declared in plan scope                                      | implemented_features - planned_features                                              | Plan parser + feature detector (file/function naming heuristics) | Post-scenario                    |
| K9  | Token Spend (Task)            | Total tokens consumed from first planning to commit                                  | SUM(token_usage where correlation_id=task)                                           | Token instrumentation (LLM events)                               | Real-time aggregate              |
| K10 | Token Spend per Feature       | Average & distribution of tokens per feature unit                                    | tokens_per_feature = tokens(feature span)                                            | Token + feature mapping                                          | Post-feature completion          |
| K11 | Task Runtime (End-to-End)     | Wall-clock from task.created to task.completed                                       | completed_at - created_at                                                            | State machine timestamps                                         | On completion                    |
| K12 | Feature Commit Cycle Time     | Time from feature start (validated) to successful commit                             | commit_time - feature_start_time                                                     | State timestamps + feature mapping                               | On commit                        |
| K13 | Command Execution Accuracy    | % expected commands executed successfully in correct sequence                        | (executed_in_sequence / expected)\*100                                               | Quality monitor log + expected command detector                  | During quality phase             |
| K14 | Escalation Effectiveness      | % escalations resolved without human                                                 | resolved_escalations / total_escalations \*100                                       | CTO intervention logs                                            | Post-escalation                  |
| K15 | Recovery MTTR                 | Mean time to recover from injected failure class                                     | AVG(recovery_time by failure_type)                                                   | Fault injector events + state transitions                        | Post-scenario                    |

## 3. Data Model

### 3.1 Event Envelope

```json
{
  "ts": "2025-08-12T12:34:56.123Z",
  "type": "TOOL|STATE|TOKEN|QUALITY|ANALYZER|PLACEHOLDER|FEATURE|FAULT|ESCALATION",
  "task_id": "TASK-123",
  "feature_id": "feat_slug",
  "correlation_id": "uuid",
  "actor": "@agent-fullstack-developer",
  "payload": { "key": "value" },
  "success": true
}
```

Stored as JSON Lines at `.metrics/events/*.jsonl` and optionally ingested to SQLite.

### 3.2 Aggregated Metric Record

```json
{
  "kpi_id": "K1",
  "scope": "task|feature|scenario|daily",
  "entity_id": "TASK-123",
  "value": 7,
  "numerator": 7,
  "denominator": 120,
  "window_start": "...",
  "window_end": "...",
  "sources": ["events/tool.jsonl"],
  "calc_version": "1.0.0"
}
```

## 4. Instrumentation Hooks

| Hook Point                         | Event Type  | Implementation Notes                                                          |
| ---------------------------------- | ----------- | ----------------------------------------------------------------------------- |
| Tool invocation wrapper            | TOOL        | Wrap existing tool executor; capture name, duration, exit status, error class |
| LLM request/response adapter       | TOKEN       | Collect model, tokens_in/out, cost_estimate, correlation_id (task / feature)  |
| State manager (plan-manager)       | STATE       | Emit on every state transition with previous/current, duration_in_state       |
| Quality monitor gate executor      | QUALITY     | Record expected commands, executed commands, pass/fail, rerun_index           |
| Commit diff analyzer (post-commit) | PLACEHOLDER | Scan added lines for placeholder regex patterns                               |
| Feature detector (parser)          | FEATURE     | Map feature_id -> artifact list & declare planned vs implemented              |
| Fault injector (future)            | FAULT       | Injected failure type, insertion_ts, detection_ts, recovery_ts                |
| CTO escalation handler             | ESCALATION  | Outcome, attempts, resolved_without_human                                     |
| Analyzer runners                   | ANALYZER    | Persist snapshot outputs (duplication %, complexity metrics)                  |

## 5. Detection & Computation Details

### 5.1 Placeholder Code Patterns

Regex set (v1):

- `\bTODO\b|FIXME|HACK|XXX`
- `raise NotImplementedError`
- `pass  # placeholder`
- `return 0  # stub` / `return None  # stub`
- `function\s+\w+\([^)]*\)\s*{\s*}` (empty bodies)
  False positive mitigation: ignore test files; min cluster of ≥2 placeholder markers in same function increases severity.

### 5.2 Duplicate Code % (K4)

```
duplicate_line_equivalents = SUM( min(lines_block1, lines_block2) for high_confidence_matches )
percentage = duplicate_line_equivalents / total_analyzable_lines * 100
```

Confidence threshold: exact=1.0; structural≥0.85; semantic≥0.8.

### 5.3 Architecture Complexity Score (K5)

Raw metrics: max_fan_in, max_fan_out, circular_cycles, cycle_ratio=circular_edges/total_edges.
Normalize each via min-max over rolling 30-day window. Weighted composite (defaults):

```
raw = 0.4*norm(max_fan_in)+0.4*norm(max_fan_out)+0.2*norm(cycle_ratio)
score = round(100 - raw*100,1)
```

### 5.4 Code Complexity Score (K6)

```
avg_ccn = mean(ccn_per_fn)
long_fn_pct = count(fn_loc>50)/total_fns
param_excess_pct = count(param_count>5)/total_fns
raw = 0.5*Z(avg_ccn) + 0.3*long_fn_pct + 0.2*param_excess_pct
score = clamp(100 - raw_scaled)
```

Where Z scaled into 0..1 using empirical bounds (ccn: 1..25).

### 5.5 Feature Creep (K8)

Plan file: fenced list or headings `### Feature:` produce planned_features set.
Implemented feature detection:

- New top-level directories/files under `src/` or `app/`
- New API endpoints (route file additions) pattern match
- New UI components (React component file names) if not referenced in plan mapping.
  Feature creep count = |implemented - planned| (only additions). Ratio also stored: creep_ratio = added / planned.

### 5.6 Command Execution Accuracy (K13)

Expected command list derived from quality monitor detection (build, test, lint, typecheck). Sequence alignment:

```
executed_in_sequence = LCS(expected_sequence, executed_sequence)
accuracy = executed_in_sequence / len(expected_sequence)
```

Gate pass required and accuracy≥0.9 for green.

### 5.7 Escalation Effectiveness (K14)

```
resolved_escalations = COUNT(escalation events with outcome=resolved_without_human)
rate = resolved_escalations / total_escalations
```

### 5.8 Recovery MTTR (K15)

For each fault type: recovery_time = recovery_ts - detection_ts; mean across window.

## 6. Fixed Coding Challenge Baseline

Goal: Standard reference scenario for multi-model evaluation.
Components:

1. Plan file (baseline): enumerated 6 features (API endpoint, persistence, auth middleware, caching layer, unit tests, refactor one duplication).
2. Golden implementation branch `baseline-challenge-main` (immutable).
3. Scenario YAML:

```yaml
id: challenge_v1
plan_file: baseline/PLAN.md
features_expected: 6
metrics: [K1, K2, K3, K4, K5, K6, K7, K8, K9, K10, K11, K12, K13]
allowed_tools_profile: standard
sandbox_strategy: git_worktree
max_duration_minutes: 45
models: [gpt-5-mini, claude-sonnet-4, gpt-oss:20b]
```

4. Scoring rubric: Primary (Accuracy 35%, Quality 25%, Robustness 15%, Efficiency 15%, Governance 10%). KPI→rubric mapping table maintained in code.

## 7. Evaluation Flow (Unified Solution Option)

1. Scenario Loader parses YAML → instantiates sandbox (git worktree).\*
2. Inject plan + baseline scaffolding; start instrumentation timer.
3. Run orchestrated agents with tool & token instrumentation wrappers.
4. After each state transition to `testing` or `quality_review`, run analyzers (duplication, complexity, security) capturing snapshots.
5. On completion/timeout, finalize events, compute KPIs via aggregator.
6. Compare metrics to baseline thresholds → produce scoreboard.
7. Emit `evaluation_report.json` & markdown summary.

\*Isolation prevents parallel runs from interfering.

## 8. Storage Layout

```
.metrics/
  events/
    2025-08-12_task-TASK123.jsonl
  aggregates/
    kpi_daily_2025-08-12.json
  reports/
    challenge_v1_run_<timestamp>.json
  dashboards/
    index.md
```

## 9. Thresholds & Alert Policies (Initial)

| KPI                       | Warning        | Alert | Hard Fail (Scenario) |
| ------------------------- | -------------- | ----- | -------------------- |
| K1 Failed Tool Calls      | >3 per task    | >6    | >10                  |
| K2 Quality Gate Rerun Avg | >1.2           | >1.5  | >2.0                 |
| K3 Placeholder Density    | >0.01          | >0.02 | >0.05                |
| K4 Duplicate Code %       | >8%            | >12%  | >18%                 |
| K5 Architecture Score     | <75            | <65   | <55                  |
| K6 Code Complexity Score  | <70            | <60   | <50                  |
| K7 Security Issues (Med+) | >3             | >7    | >10                  |
| K8 Feature Creep Count    | >1             | >2    | >3                   |
| K9 Token Spend (Task)     | >1.2x baseline | >1.5x | >2x                  |
| K11 Task Runtime          | >1.2x baseline | >1.5x | >2x                  |
| K13 Command Accuracy      | <95%           | <90%  | <80%                 |

## 10. Implementation Phasing

| Phase | Deliverables                                               | KPIs Covered |
| ----- | ---------------------------------------------------------- | ------------ |
| P1    | Event bus + TOOL/STATE/TOKEN hooks, baseline scenario file | K1,K9,K11    |
| P2    | Quality gate instrumentation + rerun detection             | K2,K13       |
| P3    | Placeholder scanner + duplication integration              | K3,K4        |
| P4    | Complexity + architecture composite                        | K5,K6        |
| P5    | Security scanning + feature creep detector                 | K7,K8        |
| P6    | Feature-level token mapping + cycle time                   | K10,K12      |
| P7    | Escalation & fault metrics                                 | K14,K15      |

## 11. Open Questions

1. Confirm plan file format for feature enumeration? (Proposed: `### Feature:` headings)
2. Accept JSON Lines + optional SQLite or require DB from start?
3. Token provider API consistency guaranteed across models? Need fallback estimation?
4. Are placeholder patterns project-specific configurable? (Proposed YAML override.)

## 12. Versioning & Change Control

- `calc_version` increments on formula changes.
- Backfill jobs recompute aggregates when version changes.
- Semantic versioning: MAJOR (breaking), MINOR (new KPI), PATCH (bug fix).

## 13. Risks & Mitigations

| Risk                             | Impact                        | Mitigation                                    |
| -------------------------------- | ----------------------------- | --------------------------------------------- |
| Metric variance (LLM randomness) | Noisy comparisons             | Multi-run median, store run_count             |
| Over-instrumentation overhead    | Slower tasks                  | Async write buffer, batch flush               |
| False positives placeholder      | Developer noise               | Confidence weighting, severity thresholds     |
| Feature creep misclassification  | Misleading governance metrics | Manual override map, ignore test/support dirs |

## 14. Acceptance Criteria (P1)

- Events captured for ≥95% tool calls during scenario run.
- KPI K1, K9, K11 computed and persisted.
- Scenario report generated with rubric skeleton.

---

Prepared for review. Feedback requested on thresholds, formulas, and phasing.
