# Security Review Command

**Mindset**: "What could go wrong?" - Combine automated scanning with contextual threat assessment.

## Behavior
Comprehensive security analysis using OWASP Top 10 framework with automated script integration and contextual threat assessment.

### Automated Security Checks (OWASP Top 10 Coverage)
Execute security analysis scripts via Bash tool for measurable vulnerability detection:
```bash
# Secret detection and vulnerability scanning
python claude/scripts/analyze/security/detect_secrets.py --target . --format json
python claude/scripts/analyze/security/scan_vulnerabilities.py --target . --format json  
python claude/scripts/analyze/security/check_auth.py --target . --format json
python claude/scripts/analyze/security/validate_inputs.py --target . --format json
```

## Script Capabilities (OWASP Top 10 Coverage)
- **scan_vulnerabilities.py**: Detects OWASP A01 (Injection - SQL, Command, LDAP, XPath) and A03 (XSS - Reflected, Stored)
- **validate_inputs.py**: Comprehensive injection detection covering SQL, NoSQL, Command, Path Traversal, and LDAP injection patterns
- **check_auth.py**: Covers OWASP A07 (Authentication Failures) including weak passwords, session fixation, missing CSRF
- **detect_secrets.py**: Identifies hardcoded credentials and API keys (supports OWASP A02 - Cryptographic Failures)

### Contextual Security Assessment
- **Business Logic Security**: Evaluate authorization rules for privilege escalation risks
- **Architecture Security Review**: Assess defense-in-depth implementation and control effectiveness
- **Risk Assessment**: Identify assets, threats, vulnerabilities in business context
- **Data Flow Security**: Analyze security between components and external interfaces

### Security Coverage Gap Assessment & Autonomous Action
- **Script vs. Codebase Reality Assessment**: Analyze script outputs against actual codebase architecture, technology stack, and implementation patterns to identify coverage gaps
- **Technology-Specific Security Analysis**: Identify framework-specific security requirements not covered by generic scripts (e.g., Django CSRF middleware, React XSS protections, Express.js security headers, JWT implementation patterns)
- **Business Logic Security Deep Dive**: Examine authorization flows, data access patterns, and privilege escalation paths that scripts cannot detect
- **Infrastructure & Deployment Security**: Assess configuration files, environment variables, container security, and deployment patterns for security misconfigurations
- **Autonomous Complementary Actions**: Perform additional security analysis tasks identified during gap assessment, including:
  - Custom vulnerability pattern searches based on identified technology stack
  - Configuration security validation for detected frameworks
  - Data flow security analysis for identified sensitive data paths
  - Authorization matrix validation for detected user roles and permissions

## Analysis Process
1. **Run scripts** to identify measurable security issues
2. **Analyze outputs** in context of business requirements  
3. **Security Coverage Gap Assessment & Autonomous Action** - Assess script effectiveness against codebase reality and perform complementary security analysis
4. **Evaluate risks** through architectural review
5. **Prioritize findings** by business impact and exploitability
6. **Generate report** combining automated + contextual + autonomous analysis

### Gap Assessment Instructions
The LLM must autonomously:

**Phase 3A: Coverage Gap Identification**
- Compare script patterns against detected codebase patterns to identify blind spots
- Identify technology stack specific security requirements (frameworks, libraries, patterns)
- Assess script pattern effectiveness against actual code implementations
- Document specific gaps between script objectives and codebase security reality

**Phase 3B: Autonomous Security Actions**
- Perform targeted Grep searches for technology-specific vulnerability patterns not covered by scripts
- Analyze configuration files for security misconfigurations (docker, nginx, package.json, requirements.txt)
- Examine environment variable usage and secret management patterns
- Validate authorization and authentication implementation patterns against best practices
- Search for business logic vulnerabilities in identified critical data flows
- Assess API security implementations (rate limiting, input validation, output encoding)

**Phase 3C: Enhanced Finding Generation**
- Generate additional security findings from autonomous analysis
- Correlate script findings with autonomous analysis results
- Identify compound security risks not detectable by individual script analysis
- Document technology-specific security recommendations

## Optional Flags
--c7: Use when you need to verify your security implementations against current OWASP Top 10 guidelines and framework-specific security patterns (e.g., Django CSRF middleware configuration, Express.js helmet security headers)
--seq: Use for comprehensive security audits - systematically breaks down the analysis into OWASP Top 10 categories with specific steps like 'A01: scan for injection vulnerabilities', 'A02: check authentication failures', 'A03: validate data exposure'

## Risk Assessment Levels
- **CRITICAL**: Data breach, system compromise, compliance violation
- **HIGH**: Privilege escalation, injection, auth bypass
- **MEDIUM**: Information disclosure, DoS, config issues  
- **LOW**: Hardening opportunities, defense gaps

## Output Requirements
- Risk-rated vulnerability report with script outputs
- Coverage gap assessment with autonomous analysis results
- Technology-specific security findings and recommendations
- Contextual analysis with business impact assessment
- Prioritized remediation roadmap with implementation guidance
- Code examples and security control recommendations

## Symbol Legend
- 🤖 Automated script analysis
- 🧠 LLM contextual analysis
- 🔍 LLM autonomous gap assessment and action
- 🚨 Critical security flaw requiring immediate attention
- ⚠️ Security concern requiring assessment and remediation
- ✅ Security control properly implemented
- 📋 Coverage gap identified requiring complementary analysis

$ARGUMENTS