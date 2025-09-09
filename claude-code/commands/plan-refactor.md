# plan-refactor v0.4

**Mindset**: "Improve without breaking" - Strategic technical debt reduction and modernization planning through automated analysis, proven patterns, and comprehensive testing frameworks.

## Workflow Process

### Phase 1: Technical Debt Assessment

1. **Execute automated analysis** - Run comprehensive technical debt assessment

   ```bash
   # Set paths and execute the analyzers
   export PYTHONPATH="$(pwd)/.claude/scripts"
   VENV_PYTHON="$(pwd)/.claude/venv/bin/python"

   "$VENV_PYTHON" -m core.cli.run_analyzer --analyzer quality:lizard --target . --output-format json
   "$VENV_PYTHON" -m core.cli.run_analyzer --analyzer architecture:coupling --target . --output-format json
   "$VENV_PYTHON" -m core.cli.run_analyzer --analyzer performance:baseline --target . --output-format json
   ```

2. **Identify refactoring priorities** - Analyze complexity hotspots and architectural debt

   - Cross-reference security vulnerabilities with refactoring scope

3. **Generate technical debt report** - Compile results into executive summary
   - Define migration scope with clear boundaries and dependencies

**STOP** → "Technical debt analysis complete. Proceed with strategy development? (y/n)"

### Phase 2: Migration Strategy Development

1. **Research proven refactoring patterns** - Use Context7 for industry-proven strategies

   - Identify patterns: Strangler Fig, Module Federation, Blue-Green deployment

2. **Create phased migration plan** - Design incremental strategy with minimal risk

   - Define feature flag integration for safe deployment

3. **Define rollback procedures** - Establish automated rollback mechanisms
   - Create safety nets and monitoring for each migration phase

**STOP** → "Migration strategy defined. Ready to create implementation plan? (y/n)"

### Phase 3: Implementation Planning

1. **Generate detailed task breakdown** - Create implementation timeline with checkpoints

   - Plan integration testing at each migration phase

2. **Create testing strategy** - Establish baselines and regression coverage

   **Use previously resolved SCRIPT_PATH (registry-driven CLI):**

   ```bash
   PYTHONPATH="$SCRIPTS_ROOT" python -m core.cli.run_analyzer --analyzer quality:coverage --target . --output-format json
   ```

3. **Define success metrics** - Set measurable complexity and performance targets
   - Create development velocity impact assessment framework

### Phase 4: Quality Validation and Task Transfer

1. **Validate plan completeness** - Verify approaches and rollback procedures

   - Ensure success metrics are measurable and achievable

2. **Quality Gates Validation**

   - [ ] Technical debt hotspots identified and prioritized
   - [ ] Migration strategy validated against proven patterns
   - [ ] Implementation phases include comprehensive rollback procedures
   - [ ] Testing strategy covers regression prevention and performance validation
   - [ ] All refactoring targets have defined success metrics

3. **Transfer tasks to todos.md** - Generate actionable implementation tasks
   - Append formatted tasks with clear phases to todos.md

**STOP** → "Implementation plan complete and validated. Transfer to todos.md? (y/n)"

## Enhanced Optional Flags

None currently defined.

## Task Format for todos.md Transfer

```markdown
## [System/Component] Refactoring Implementation

### Phase [PHASE-NUMBER]: [PHASE-TITLE]

- [ ] [PHASE-TASK]
- [ ] [PHASE-TASK]
- [ ] [PHASE-TASK]
```

$ARGUMENTS

TLE]

- [ ] [PHASE-TASK]
- [ ] [PHASE-TASK]
- [ ] [PHASE-TASK]
```

$ARGUMENTS
d prioritized
   - [ ] Migration strategy validated against proven patterns
   - [ ] Implementation phases include comprehensive rollback procedures
   - [ ] Testing strategy covers regression prevention and performance validation
   - [ ] All refactoring targets have defined success metrics

3. **Transfer tasks to todos.md** - Generate actionable implementation tasks
   - Append formatted tasks with clear phases to todos.md

**STOP** → "Implementation plan complete and validated. Transfer to todos.md? (y/n)"

## Enhanced Optional Flags

None currently defined.

## Task Format for todos.md Transfer

```markdown
## [System/Component] Refactoring Implementation

### Phase [PHASE-NUMBER]: [PHASE-TITLE]

- [ ] [PHASE-TASK]
- [ ] [PHASE-TASK]
- [ ] [PHASE-TASK]
```

$ARGUMENTS
ITLE]

- [ ] [PHASE-TASK]
- [ ] [PHASE-TASK]
- [ ] [PHASE-TASK]
```

$ARGUMENTS
