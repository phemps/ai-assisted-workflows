---
argument-hint: [target-path] [--verbose]
---

# analyze-security v0.5

**Mindset**: "What could go wrong?" - Combine automated scanning with contextual threat assessment.

## Behavior

Comprehensive security analysis using OWASP Top 10 framework with automated script integration and contextual threat assessment.

## Workflow Process

### Phase 1: Automated Security Assessment

1. **Execute automated security scripts** - Run comprehensive OWASP Top 10 vulnerability detection

   ```bash
   # Set paths and execute the analyzers
   export PYTHONPATH="$(pwd)/.claude/scripts"
   VENV_PYTHON="$(pwd)/.claude/venv/bin/python"

   "$VENV_PYTHON" -m core.cli.run_analyzer --analyzer security:semgrep --target . --output-format json
   "$VENV_PYTHON" -m core.cli.run_analyzer --analyzer security:detect_secrets --target . --output-format json
   ```

2. **Analyze script outputs** - Process automated findings against OWASP framework

   - **semgrep_analyzer.py**: Comprehensive OWASP Top 10 detection including A01 (Injection), A03 (XSS), A07 (Authentication Failures), and input validation using semantic analysis
   - **detect_secrets_analyzer.py**: Advanced entropy-based secrets detection for hardcoded credentials and API keys (A02 - Cryptographic Failures)

3. **Generate security baseline** - Compile automated results for contextual analysis

**⚠️ REQUIRED USER CONFIRMATION**: Ask user "Automated security analysis complete. Proceed with gap assessment? (y/n)" and WAIT for response before continuing to Phase 2. If user responds "n" or "no", stop workflow execution.

### Phase 2: Gap Assessment and Contextual Analysis

1. **Perform OWASP Top 10 systematic coverage review** - Compare automated findings against actual codebase

   - Identify technology-specific security patterns not covered by the script based analysis
   - Assess framework-specific requirements (Django CSRF, React XSS protections, Express.js headers)

2. **Execute autonomous security searches** - Targeted analysis for identified gaps
   - Custom vulnerability pattern searches based on identified technology stack
   - Configuration security validation for detected frameworks
   - Authorization matrix validation for detected user roles and permissions
   - Data flow security analysis between components and external interfaces
   - Infrastructure and deployment security review

**⚠️ REQUIRED USER CONFIRMATION**: Ask user "Gap assessment and contextual analysis complete. Proceed with risk prioritization? (y/n)" and WAIT for response before continuing to Phase 3. If user responds "n" or "no", stop workflow execution.

### Phase 3: Risk Prioritization and Reporting

1. **Correlate and prioritize findings** - Combine automated and contextual analysis results

   - Generate security score based on identified vulnerabilities
   - Prioritize by business impact and exploitability

2. **Create security report** - Format findings by severity level

   - **CRITICAL**: Data breach, system compromise, compliance violation
   - **HIGH**: Privilege escalation, injection, auth bypass
   - **MEDIUM**: Information disclosure, DoS, config issues
   - **LOW**: Hardening opportunities, defense gaps

3. **Generate remediation roadmap** - Phased approach with specific locations
   - Phase 1: Critical security issues requiring immediate attention
   - Phase 2: High priority security concerns
   - Phase 3: Security hardening and configuration improvements

### Phase 4: Quality Validation and Task Transfer

1. **Validate analysis completeness** - Ensure comprehensive OWASP Top 10 coverage

   - Verify all security script outputs processed
   - Confirm gap assessment covered technology-specific patterns

2. **Quality Gates Validation**

   - [ ] All OWASP Top 10 categories systematically assessed
   - [ ] Script outputs validated against codebase architecture
   - [ ] Technology-specific security patterns identified
   - [ ] Business logic vulnerabilities evaluated
   - [ ] Security findings prioritized by business impact

3. **Transfer security tasks to todos.md** - Generate actionable remediation tasks
   - Append formatted security findings with clear priorities to todos.md

**⚠️ REQUIRED USER CONFIRMATION**: Ask user "Security analysis complete and validated. Transfer findings to todos.md? (y/n)" and WAIT for response before proceeding with todo transfer. If user responds "n" or "no", stop workflow execution.

## Enhanced Optional Flags

**--verbose**: Show detailed script outputs, gap analysis table, and comprehensive vulnerability descriptions

## Task Format for todos.md Transfer

```markdown
## Security Remediation Implementation

### Phase 1: Critical Security Issues

- [ ] [CRITICAL-FINDING] - [LOCATION]
- [ ] [CRITICAL-FINDING] - [LOCATION]

### Phase 2: High Priority Security Issues

- [ ] [HIGH-FINDING] - [LOCATION]
- [ ] [HIGH-FINDING] - [LOCATION]

### Phase 3: Security Hardening

- [ ] [MEDIUM-FINDING] - [LOCATION]
- [ ] [LOW-FINDING] - [LOCATION]
```

$ARGUMENTS
