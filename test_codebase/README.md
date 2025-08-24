# Security Analysis Test Suite

⚠️ **WARNING: This directory contains intentionally vulnerable applications for security testing purposes. NEVER deploy to production or expose to untrusted networks!**

## Overview

This test suite provides a comprehensive collection of intentionally vulnerable applications across multiple programming languages, designed to evaluate the effectiveness of our security analysis tools. It includes both well-known OWASP applications and custom vulnerability examples.

## Directory Structure

```
test_codebase/
├── vulnerable-apps/          # Intentionally vulnerable applications
│   ├── nodegoat/            # Node.js/JavaScript vulnerabilities (OWASP)
│   ├── pygoat/              # Python/Django vulnerabilities (OWASP)
│   ├── vulnerable-flask/    # Python/Flask vulnerabilities
│   ├── dvwa/                # PHP vulnerabilities (Damn Vulnerable Web App)
│   ├── webgoat/             # Java/Spring Boot vulnerabilities (OWASP)
│   ├── govwa/               # Go vulnerabilities
│   ├── damn-vulnerable-go/  # Go vulnerability examples
│   ├── rust-vulns/          # Rust vulnerability examples (custom)
│   ├── sql-vulns/           # SQL vulnerability examples (custom)
├── eval-framework/           # Evaluation framework
│   ├── expected_findings.json # Known vulnerabilities catalog
│   ├── run_evaluations.py    # Evaluation execution engine
│   ├── generate_report.py    # Report generation
│   ├── run_eval.sh           # Convenience evaluation script
│   └── results/              # Evaluation results and reports
├── monorepo/                 # Existing test monorepo
├── duplicate_detectors/      # Code duplication test cases
└── README.md                 # This file
```

## Quick Start

### 1. Run Security Analysis Evaluation

```bash
cd test_codebase/eval-framework
./run_eval.sh
```

This will:
- Run all available security analyzers against vulnerable applications
- Compare findings with expected vulnerabilities
- Calculate precision, recall, and F1-scores
- Generate comprehensive HTML and markdown reports

### 2. View Results

```bash
# View latest HTML report
open eval-framework/results/latest_report.html

# View latest markdown report
cat eval-framework/results/latest_report.md

# View raw JSON results
cat eval-framework/results/latest_results.json
```

## Supported Languages and Applications

| Language | Application | Framework | Vulnerabilities | Source |
|----------|-------------|-----------|----------------|---------|

## Expected Vulnerability Coverage

Our test suite covers all **OWASP Top 10** categories:

- **A01: Injection** - SQL injection, NoSQL injection, command injection
- **A02: Broken Authentication** - Weak session management, auth bypass
- **A03: Sensitive Data Exposure** - Plaintext passwords, PII exposure
- **A04: XML External Entities** - XXE vulnerabilities (where applicable)
- **A05: Broken Access Control** - IDOR, privilege escalation
- **A06: Security Misconfiguration** - Debug modes, default credentials
- **A07: Cross-Site Scripting** - Reflected, stored, DOM-based XSS
- **A08: Insecure Deserialization** - Object injection, RCE
- **A09: Known Vulnerabilities** - Outdated dependencies
- **A10: Insufficient Logging** - Missing security monitoring

Plus **language-specific vulnerabilities**:
- **Go**: Unsafe operations, race conditions, memory leaks
- **Rust**: Unsafe blocks, buffer overflows, use-after-free
- **SQL**: Performance issues, missing indexes, anti-patterns

## Available Security Analyzers

The evaluation framework tests these analyzers:

| Analyzer | Languages | Detects |
|----------|-----------|---------|
| **Semgrep** | JS, Python, Java, Go, Rust | Injection, XSS, hardcoded secrets, unsafe patterns |
| **detect-secrets** | All | API keys, passwords, tokens, credentials |
| **SQLFluff** | SQL | SQL injection, performance issues, anti-patterns |

## Evaluation Metrics

The framework calculates:

- **Precision** = True Positives / (True Positives + False Positives)
- **Recall** = True Positives / (True Positives + False Negatives)
- **F1-Score** = 2 × (Precision × Recall) / (Precision + Recall)
- **Coverage** = Detected Vulnerabilities / Expected Vulnerabilities

## Advanced Usage

### Run Specific Analyzer

```bash
cd eval-framework
./run_eval.sh --analyzer semgrep --verbose
```

### Test Specific Application

```bash
cd eval-framework
./run_eval.sh --application nodegoat
```

### Custom Evaluation

```bash
cd eval-framework
python3 run_evaluations.py --analyzer semgrep --application pygoat --verbose
python3 generate_report.py --results evaluation_results.json --format html
```

## Configuration

### Expected Findings

Edit `eval-framework/expected_findings.json` to:
- Add new vulnerability types
- Update application information
- Configure analyzer capabilities
- Adjust severity mappings

### Analyzer Integration

To add a new analyzer:

1. Add analyzer script to `shared/analyzers/`
2. Update `eval-framework/run_evaluations.py` analyzers dict
3. Add analyzer capabilities to `expected_findings.json`
4. Update vulnerability type extraction logic

### Performance Tracking

Track evaluation metrics over time:

```bash
# Compare results across time
python3 -c "
import json
import glob

results = []
for f in glob.glob('eval-framework/results/evaluation_results_*.json'):
    with open(f) as file:
        data = json.load(file)
        results.append({
            'date': data['metadata']['evaluation_date'],
            'f1_score': data['summary'].get('average_metrics', {}).get('f1_score', 0)
        })

results.sort(key=lambda x: x['date'])
for r in results[-5:]:  # Last 5 runs
    print(f\"{r['date']}: F1-Score = {r['f1_score']:.3f}\")
"
```

## Troubleshooting

### Common Issues

**Setup fails for some applications:**
```bash
# Check logs in setup script
cd vulnerable-apps
./setup.sh 2>&1 | tee setup.log
```

**Evaluation times out:**
```bash
# Increase timeout or limit files
python3 run_evaluations.py --max-files 20
```

**Docker containers fail to start:**
```bash
# Check Docker daemon and logs
docker-compose logs [service-name]
```

**Missing dependencies:**
```bash
# Install analyzer dependencies
pip install semgrep detect-secrets sqlfluff
```

### Debug Mode

Enable verbose logging:
```bash
export PYTHONPATH=$PWD
python3 -m pdb eval-framework/run_evaluations.py --verbose
```

## Contributing

### Adding New Vulnerabilities

1. Create vulnerability example in appropriate language directory
2. Update `expected_findings.json` with new vulnerability details
3. Test with existing analyzers
4. Document in application README
5. Submit pull request with test results

### Adding New Applications

1. Add application to `vulnerable-apps/` directory
2. Update `setup.sh` with installation steps
3. Add Docker configuration if applicable
4. Document vulnerabilities in `expected_findings.json`
5. Test evaluation framework integration

## Further Reading

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Vulnerable Web Applications Directory](https://owasp.org/www-project-vulnerable-web-applications-directory/)
- [Semgrep Rules](https://semgrep.dev/explore)
- [detect-secrets Documentation](https://github.com/Yelp/detect-secrets)
- [SQLFluff Documentation](https://docs.sqlfluff.com/)
