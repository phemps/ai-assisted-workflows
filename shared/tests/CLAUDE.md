## Testing

Frameworks: pytest, Custom evaluation frameworks, Integration test suites

Running Tests:

# Run all analyzer integration tests (registry-based)

PYTHONPATH=shared NO_EXTERNAL=true python shared/tests/integration/test_all_analyzers.py test_codebase/juice-shop-monorepo --output-format json --max-files 2

# Omit NO_EXTERNAL to include analyzers that require external tools (semgrep, detect-secrets, sqlfluff)

# Security analyzer evaluation

PYTHONPATH=shared python shared/tests/integration/test_security_analysers.py --analyzer detect_secrets --verbose

# Root cause analyzers integration test

PYTHONPATH=shared python shared/tests/integration/test_root_cause_analyzers.py

# Individual analyzer testing

cd shared && python analyzers/security/detect_secrets_analyzer.py ../test_codebase/project --max-files 10

### Test Commands:

```bash
from repo root:

# Run evaluation with specific analyzer (clean output)
PYTHONPATH=shared python shared/tests/integration/test_security_analysers.py --analyzer detect_secrets

# Run with detailed progress information
PYTHONPATH=shared python shared/tests/integration/test_security_analysers.py --analyzer semgrep --verbose

# Test specific applications only
PYTHONPATH=shared python shared/tests/integration/test_security_analysers.py --analyzer detect_secrets --applications test-python test-java

# Run with limited file scanning
PYTHONPATH=shared python shared/tests/integration/test_security_analysers.py --analyzer semgrep --max-files 10
```

- `--analyzer`: Choose specific analyzer (detect_secrets, semgrep)
- `--applications`: Test specific applications only
- `--max-files`: Limit number of files scanned per application
- `--min-severity medium`: Filter findings by severity
- `--verbose`: Show detailed execution progress and debug information
- `--output-format json` Output results in JSON format
