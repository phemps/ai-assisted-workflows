# plan-solution v0.7

**Purpose**: Research-driven technical challenge solving with systematic analysis and implementation planning.

## Workflow

### Phase 1: Context Gathering
**STOP** → "Describe your technical challenge and constraints"

**Required context:**
- Technical challenge description
- Current technology stack
- Timeline/complexity preferences
- Team constraints

### Phase 2: System Analysis
1. **Run architecture analysis**:
   ```bash
   # Find scripts dynamically
   glob **/scripts/analyze/architecture/*.py
   python [SCRIPT_PATH]/pattern_evaluation.py .
   python [SCRIPT_PATH]/scalability_check.py .
   python [SCRIPT_PATH]/coupling_analysis.py .
   ```

2. **Document findings**:
   - Current patterns identified
   - Scalability constraints
   - Integration points
   - Technical debt considerations

### Phase 3: Research & Solutions
1. **Research best practices** (web search)
2. **Develop 3 solution approaches**:
   - **Solution 1**: Conservative/established approach
   - **Solution 2**: Balanced approach
   - **Solution 3**: Innovative/modern approach

### Phase 4: Comparative Analysis
| Aspect | Solution 1 | Solution 2 | Solution 3 |
|--------|------------|------------|------------|
| **Development Complexity** | [Rating/Notes] | [Rating/Notes] | [Rating/Notes] |
| **Integration Effort** | [Rating/Notes] | [Rating/Notes] | [Rating/Notes] |
| **Technology Risk** | [Rating/Notes] | [Rating/Notes] | [Rating/Notes] |
| **Team Readiness** | [Rating/Notes] | [Rating/Notes] | [Rating/Notes] |

### Phase 5: Recommendation & Roadmap
**Recommended Solution**: [Choose one]

**Justification**:
- Technical alignment with current system
- Balance of risk vs benefit
- Resource/timeline fit

**Implementation Roadmap**:
- **Phase 1**: Foundation setup ([timeline])
- **Phase 2**: Core implementation ([timeline])
- **Phase 3**: Optimization & testing ([timeline])

**Success Criteria**:
- Performance benchmarks: [metrics]
- Integration success: [validation approach]
- Monitoring setup: [observability plan]

### Phase 6: Task Transfer
**STOP** → "Ready to transfer implementation roadmap to todo.md?"

**If confirmed**:
1. Check `./todos/todos.md` exists
2. Append implementation tasks
3. Format as actionable checkboxes
4. Confirm transfer complete

## Flags
- `--c7`: Validate against current industry standards
- `--critique`: Critique your reasoning around the user request, the solution options you select and the final recommendation
- `--seq`: Systematic breakdown: analyze → research → compare → recommend → transfer

## Templates
**Solution format**:
```
## [Solution Name]
**Approach**: [Technical strategy]
**Stack**: [Technologies]
**Complexity**: [Effort/Resources]
**Risk**: [Assessment]
```