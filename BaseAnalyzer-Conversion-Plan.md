# BaseAnalyzer Conversion Plan

## Multi-Session Completion Guide

### 📋 Initial Context for Fresh Sessions

When starting a new session to continue BaseAnalyzer conversions, review this context:

#### What is BaseAnalyzer?

- **Abstract base class** providing shared infrastructure for all analyzers
- **Location**: `shared/core/base/analyzer_base.py` (480+ lines)
- **Purpose**: Eliminate 20-30 lines of boilerplate per analyzer across 20+ files
- **Pattern**: Follows same successful approach as BaseProfiler

#### Key Components:

- **AnalyzerConfig**: Standardized configuration with 24+ file extensions and skip patterns
- **Abstract Methods**: `analyze_target()` and `get_analyzer_metadata()`
- **Shared Infrastructure**: File scanning, CLI, error handling, timing, result formatting
- **Backward Compatibility**: Legacy function wrappers maintain existing integrations

#### Proven Examples:

- ✅ **AuthSecurityAnalyzer** (Phase 4): 105 findings detected, 25+ lines eliminated
- ✅ **LizardComplexityAnalyzer** (Phase 5.1): 15 findings detected, 50+ lines eliminated

#### 6-Step Conversion Pattern:

1. **Convert Class**: Extend BaseAnalyzer instead of standalone implementation
2. **Implement Abstract Methods**: `analyze_target()` and `get_analyzer_metadata()`
3. **Remove Boilerplate**: Eliminate manual sys.path, utility imports, CLI parsing
4. **Add Legacy Wrapper**: Maintain backward compatibility with existing function signatures
5. **Test Functionality**: Verify analysis logic works with BaseAnalyzer infrastructure
6. **Validate CLI**: Ensure standardized interface works correctly

---

### 🎯 Analyzer Conversion Checklist

#### Security Analyzers (3 remaining)

- [x] `check_auth.py` ✅ (Phase 4 - Complete)
- [ ] `detect_secrets.py` - Secret detection patterns
- [ ] `scan_vulnerabilities.py` - Vulnerability scanning (750-line implementation)
- [ ] `validate_inputs.py` - Input validation security checks

#### Quality Analyzers (0 remaining) 🎉 **COMPLETE**

- [x] `complexity_lizard.py` ✅ (Phase 5.1 - Complete)
- [x] `coverage_analysis.py` ✅ (Phase 5.2 - Complete) - Test coverage analysis across languages
- [x] `code_duplication_analyzer.py` ✅ (Pre-converted) - Traditional quality analysis tool - Already extends BaseAnalyzer
- [x] `analysis_engine.py` ✅ (Phase 5.3 - Complete) - Quality analysis orchestration engine extending BaseAnalyzer
- [x] `pattern_classifier.py` ✅ (Phase 5.4 - Complete) - Code pattern classification with multi-detector analysis
- [x] `result_aggregator.py` ✅ (Phase 5.5 - Complete) - Analysis result aggregation with executive reporting

#### Architecture Analyzers (4 remaining)

- [ ] `coupling_analysis.py` - Code coupling analysis
- [ ] `dependency_analysis.py` - Dependency analysis and visualization
- [ ] `pattern_evaluation.py` - Architectural pattern evaluation
- [ ] `scalability_check.py` - Scalability assessment

#### Performance Analyzers (3 remaining)

- [ ] `analyze_frontend.py` - Frontend-specific performance analysis
- [ ] `check_bottlenecks.py` - Performance bottleneck detection
- [ ] `performance_baseline.py` - Performance baseline establishment
  > Note: `profile_code.py` and `profile_database.py` already use BaseProfiler

#### Root Cause Analyzers (4 remaining)

- [ ] `error_patterns.py` - Error pattern detection
- [ ] `recent_changes.py` - Recent change analysis for debugging
- [ ] `simple_trace.py` - Simple execution tracing
- [ ] `trace_execution.py` - Advanced execution tracing analysis

---

### 📊 Progress Tracking

**Total Analyzers**: 21
**Completed**: 7 ✅ (33.3%)
**Remaining**: 14 ⏳ (66.7%)

**By Category:**

- Security: 1/4 complete (25%)
- Quality: 6/6 complete (100%) 🎉 **COMPLETE**
- Architecture: 0/4 complete (0%)
- Performance: 0/3 complete (0%)
- Root Cause: 0/4 complete (0%)

---

### 🚀 Session Workflow

#### Starting a New Session:

1. **Read this plan** to understand current progress
2. **Check session-notes.md** for latest technical details
3. **Pick next analyzer** from unchecked items above
4. **Follow 6-step conversion pattern**
5. **Test functionality** and commit changes
6. **Update this checklist** by marking item complete
7. **Update session-notes.md** with session details

#### Quick Reference Commands:

```bash
# Test converted analyzer
python shared/analyzers/{category}/{analyzer}.py --help

# Run analysis test
python shared/analyzers/{category}/{analyzer}.py . --output-format console

# Check git status and commit
git status
git add shared/analyzers/{category}/{analyzer}.py
git commit -m "feat: convert {analyzer} to BaseAnalyzer infrastructure"
```

#### Expected Benefits per Conversion:

- **Code Reduction**: 20-30 lines of boilerplate eliminated
- **Standardized CLI**: Consistent --max-files, --batch-size, --timeout options
- **Shared Infrastructure**: File scanning, error handling, logging patterns
- **Backward Compatibility**: Legacy function wrappers maintained

---

### 🎯 Completion Goals

**Short-term (Next 3-5 sessions):**

- Complete all remaining Quality analyzers (5 files)
- Start Architecture analyzers (4 files)

**Medium-term (5-10 sessions):**

- Complete Architecture and Performance analyzers (7 files)
- Start Root Cause analyzers (4 files)

**Long-term (10-15 sessions):**

- Complete all 19 remaining analyzers
- Achieve 400-600 lines of boilerplate elimination
- Establish consistent CLI interfaces across all analyzers

**Final Validation:**

- All 21 analyzers extend BaseAnalyzer ✅
- All analyzers have standardized CLI interfaces ✅
- All legacy functions maintain backward compatibility ✅
- Comprehensive testing validates no functionality regression ✅

---

_Last Updated: 2025-08-12 - Phase 5.1 Complete_
_Next Target: Quality analyzers (`coverage_analysis.py`, `code_duplication_analyzer.py`)_
