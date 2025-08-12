# BaseAnalyzer/BaseProfiler Developer Guide

## 🎯 **Quick Start for New Analyzer Development**

This guide provides step-by-step instructions for creating new analysis tools using the proven BaseAnalyzer/BaseProfiler infrastructure.

### **Why Use BaseAnalyzer/BaseProfiler?**

- ✅ **400+ lines of boilerplate eliminated** - No more manual CLI parsing, file scanning, or error handling
- ✅ **Consistent interfaces** - All analyzers have identical CLI and output formats
- ✅ **Quality assurance** - Strict validation prevents placeholder findings and silent failures
- ✅ **No false positives** - All findings are genuine, actionable issues with specific recommendations

## 📋 **Step-by-Step Development Process**

### **Step 1: Choose Your Base Class**

```python
# For general analysis tools (security, quality, architecture, root cause)
from shared.core.base.analyzer_base import BaseAnalyzer

# For performance-specific analysis tools
from shared.core.base.profiler_base import BaseProfiler
```

### **Step 2: Create Your Analyzer File**

Create your analyzer in the appropriate category directory:

- `shared/analyzers/security/` - Authentication, secrets, vulnerabilities
- `shared/analyzers/quality/` - Complexity, coverage, duplicates, patterns
- `shared/analyzers/performance/` - Profiling, bottlenecks, optimization
- `shared/analyzers/architecture/` - Coupling, dependencies, scalability
- `shared/analyzers/root_cause/` - Error analysis, tracing, debugging

### **Step 3: Basic Analyzer Template**

```python
#!/usr/bin/env python3
"""
My Custom Analyzer
==================

PURPOSE: [Describe what this analyzer detects/measures]

APPROACH: [Explain your analysis methodology]

EXTENDS: BaseAnalyzer for common analyzer infrastructure
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import base analyzer infrastructure
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.core.base.analyzer_base import BaseAnalyzer, AnalyzerConfig, create_standard_finding

class MyCustomAnalyzer(BaseAnalyzer):
    """Custom analyzer extending BaseAnalyzer infrastructure."""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        # Define file types your analyzer can process
        custom_config = config or AnalyzerConfig(
            code_extensions={".py", ".js", ".ts", ".java"},  # File types to analyze
            skip_patterns={"node_modules", "__pycache__", "venv"}  # Directories to skip
        )

        # Initialize base analyzer with your analyzer type
        super().__init__("my_analyzer_type", custom_config)

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Analyze a single file and return findings.

        This is the core method you must implement. BaseAnalyzer handles:
        - Directory iteration and file filtering
        - CLI argument parsing
        - Error handling and logging
        - Result formatting and output

        You just focus on the analysis logic for a single file.

        Args:
            target_path: Path to single file to analyze

        Returns:
            List of finding dictionaries with required fields
        """
        findings = []

        try:
            # Read and analyze the file
            with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                return findings

            # IMPLEMENT YOUR ANALYSIS LOGIC HERE
            if self._detect_issue(content):
                # Use helper function for consistent finding format
                finding = create_standard_finding(
                    title="Specific Issue Found",  # Specific, not generic
                    description="Detailed description of what was detected",
                    severity="medium",  # critical/high/medium/low/info
                    file_path=target_path,
                    line_number=self._find_line_number(content),
                    recommendation="Specific action to fix this issue",
                    metadata={
                        "pattern_type": "my_pattern",
                        "confidence": 0.85
                    }
                )
                findings.append(finding)

        except Exception as e:
            # Error handling - return error finding rather than crashing
            error_finding = create_standard_finding(
                title="Analysis Error",
                description=f"Failed to analyze file: {str(e)}",
                severity="low",
                file_path=target_path,
                line_number=1,
                recommendation="Check file permissions and encoding, then retry",
                metadata={"error_type": type(e).__name__}
            )
            findings.append(error_finding)

        return findings

    def get_analyzer_metadata(self) -> Dict[str, Any]:
        """
        Return analyzer-specific metadata for introspection.

        This helps other tools understand what your analyzer does
        and what capabilities it provides.
        """
        return {
            "analysis_type": "my_custom_analysis",
            "supported_languages": ["Python", "JavaScript", "TypeScript", "Java"],
            "capabilities": {
                "pattern_detection": "Detects specific code patterns or issues",
                "multi_language": "Supports multiple programming languages"
            },
            "dependencies": ["List", "of", "required", "external", "tools"],
            "use_cases": [
                "Primary use case description",
                "Secondary use case description",
                "Integration scenario description"
            ],
            "thresholds": {
                "confidence_minimum": 0.7,
                "severity_mapping": "How severity levels are determined"
            }
        }

    # Private helper methods for your analysis logic
    def _detect_issue(self, content: str) -> bool:
        """Implement your detection logic here."""
        # Example: Simple pattern matching
        return "problematic_pattern" in content

    def _find_line_number(self, content: str) -> int:
        """Find the line number where issue occurs."""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if "problematic_pattern" in line:
                return i
        return 1

# Legacy function for backward compatibility
def analyze_my_custom_logic(
    target_path: str,
    output_format: str = "json",
    **kwargs
) -> Dict[str, Any]:
    """
    Legacy function wrapper for backward compatibility.

    This ensures existing code that calls your analyzer directly
    continues to work while new code can use the BaseAnalyzer interface.
    """
    try:
        config = AnalyzerConfig(
            target_path=target_path,
            output_format=output_format,
            **kwargs
        )

        analyzer = MyCustomAnalyzer(config=config)
        results = analyzer.analyze()

        return {
            "success": True,
            "findings": results.findings if hasattr(results, "findings") else [],
            "metadata": results.metadata if hasattr(results, "metadata") else {},
            "execution_time": results.execution_time if hasattr(results, "execution_time") else 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "findings": []
        }

# CLI Integration
def main():
    """CLI entry point using BaseAnalyzer infrastructure."""
    analyzer = MyCustomAnalyzer()
    exit_code = analyzer.run_cli()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
```

## 🧪 **Development and Testing Workflow**

### **Step 4: Test Your Implementation**

```bash
# Test with strict validation (this will catch any issues)
cd shared && PYTHONPATH=. python analyzers/category/my_custom_analyzer.py ../test_codebase/monorepo --max-files 5

# Expected output: JSON with real findings (not placeholders)
{
  "success": true,
  "findings": [
    {
      "title": "Specific Issue Found",  # NOT "security finding"
      "description": "Detailed description...",  # NOT "Analysis issue detected"
      "severity": "medium",
      "file_path": "actual/file/path.py",  # NOT "unknown"
      "line_number": 42,  # NOT 0
      "recommendation": "Specific fix to apply"  # NOT "Review issue"
    }
  ]
}
```

### **Step 5: Validation Checklist**

Before submitting your analyzer, ensure:

- [ ] **No KeyError exceptions** - All required fields present
- [ ] **Specific titles** - Not "security finding", "quality finding", etc.
- [ ] **Detailed descriptions** - Not "Analysis issue detected", "Issue found"
- [ ] **Actionable recommendations** - Not "Review issue", "Fix problem"
- [ ] **Real file paths** - Not "unknown" or placeholder values
- [ ] **Actual line numbers** - Not 0 unless it's an error case
- [ ] **CLI working** - `--help`, `--max-files`, `--output-format` all function
- [ ] **Legacy compatibility** - Backward-compatible function wrapper provided

### **Step 6: Common Patterns and Best Practices**

#### **Pattern Detection**

```python
def _detect_sql_injection(self, content: str, file_path: str) -> List[Dict[str, Any]]:
    """Example: SQL injection detection pattern."""
    findings = []
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Look for concatenated SQL queries
        if re.search(r'query\s*=\s*["\'].*\+.*["\']', line):
            finding = create_standard_finding(
                title="SQL Injection Vulnerability",
                description="String concatenation used in SQL query construction - vulnerable to injection",
                severity="high",
                file_path=file_path,
                line_number=line_num,
                recommendation="Use parameterized queries or ORM methods instead of string concatenation",
                metadata={
                    "pattern": "string_concatenation_sql",
                    "line_content": line.strip(),
                    "vulnerability_type": "sql_injection"
                }
            )
            findings.append(finding)

    return findings
```

#### **Multi-Language Support**

```python
def _get_file_language(self, file_path: str) -> str:
    """Determine programming language from file extension."""
    ext = Path(file_path).suffix.lower()

    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.cs': 'csharp',
        '.php': 'php'
    }

    return language_map.get(ext, 'unknown')

def _analyze_by_language(self, content: str, language: str) -> List[Dict[str, Any]]:
    """Apply language-specific analysis patterns."""
    if language == 'python':
        return self._analyze_python_patterns(content)
    elif language == 'javascript':
        return self._analyze_javascript_patterns(content)
    # ... more languages
    else:
        return []  # Unsupported language
```

#### **Severity Mapping**

```python
def _calculate_severity(self, issue_type: str, confidence: float) -> str:
    """Determine severity based on issue type and confidence."""
    if issue_type in ['sql_injection', 'xss', 'hardcoded_secret']:
        return 'critical'
    elif issue_type in ['weak_crypto', 'path_traversal'] and confidence > 0.8:
        return 'high'
    elif confidence > 0.6:
        return 'medium'
    else:
        return 'low'
```

## 🎨 **Advanced Patterns**

### **AST-Based Analysis** (Python files)

```python
import ast

def _analyze_python_ast(self, content: str, file_path: str) -> List[Dict[str, Any]]:
    """Analyze Python code using AST parsing."""
    findings = []

    try:
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for functions with too many parameters
                if len(node.args.args) > 7:
                    finding = create_standard_finding(
                        title="Function Has Too Many Parameters",
                        description=f"Function '{node.name}' has {len(node.args.args)} parameters (limit: 7)",
                        severity="medium",
                        file_path=file_path,
                        line_number=node.lineno,
                        recommendation="Consider using a configuration object or breaking into smaller functions",
                        metadata={
                            "function_name": node.name,
                            "parameter_count": len(node.args.args),
                            "pattern_type": "too_many_parameters"
                        }
                    )
                    findings.append(finding)

    except SyntaxError as e:
        # Handle syntax errors gracefully
        pass

    return findings
```

### **Configuration-Driven Analysis**

```python
@dataclass
class MyAnalyzerConfig:
    """Custom configuration for your analyzer."""
    max_complexity: int = 10
    min_confidence: float = 0.7
    enabled_patterns: Set[str] = field(default_factory=lambda: {"pattern1", "pattern2"})
    severity_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "critical": 0.9,
        "high": 0.7,
        "medium": 0.5
    })

class MyCustomAnalyzer(BaseAnalyzer):
    def __init__(self, config: Optional[AnalyzerConfig] = None, custom_config: Optional[MyAnalyzerConfig] = None):
        super().__init__("my_analyzer", config)
        self.custom_config = custom_config or MyAnalyzerConfig()

    def analyze_target(self, target_path: str) -> List[Dict[str, Any]]:
        # Use self.custom_config for analysis parameters
        findings = []

        for pattern in self.custom_config.enabled_patterns:
            pattern_findings = self._check_pattern(target_path, pattern)
            findings.extend(pattern_findings)

        return findings
```

### **Integration with External Tools**

```python
import subprocess
from pathlib import Path

def _run_external_tool(self, file_path: str) -> List[Dict[str, Any]]:
    """Example: Integrate with external security tool."""
    findings = []

    try:
        # Run external tool (e.g., bandit for Python security)
        result = subprocess.run(
            ['bandit', '-f', 'json', file_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Parse tool output and convert to standard format
            import json
            tool_results = json.loads(result.stdout)

            for issue in tool_results.get('results', []):
                finding = create_standard_finding(
                    title=f"Security Issue: {issue.get('test_name', 'Unknown')}",
                    description=issue.get('issue_text', 'Security vulnerability detected'),
                    severity=self._map_bandit_severity(issue.get('issue_severity')),
                    file_path=file_path,
                    line_number=issue.get('line_number', 1),
                    recommendation=issue.get('issue_text', 'Review security issue'),
                    metadata={
                        "tool": "bandit",
                        "confidence": issue.get('issue_confidence', 'unknown'),
                        "cwe": issue.get('cwe', {})
                    }
                )
                findings.append(finding)

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError) as e:
        self.logger.debug(f"External tool execution failed: {e}")

    return findings
```

## 📊 **Testing and Quality Assurance**

### **Unit Testing Your Analyzer**

```python
# tests/test_my_custom_analyzer.py
import pytest
from pathlib import Path
from shared.analyzers.category.my_custom_analyzer import MyCustomAnalyzer

class TestMyCustomAnalyzer:
    def setup_method(self):
        """Setup test analyzer."""
        self.analyzer = MyCustomAnalyzer()

    def test_detect_issue_positive(self):
        """Test that analyzer detects known issues."""
        test_content = """
def vulnerable_function():
    query = "SELECT * FROM users WHERE id = " + user_id
    return query
        """

        with open("test_file.py", "w") as f:
            f.write(test_content)

        findings = self.analyzer.analyze_target("test_file.py")

        assert len(findings) == 1
        assert findings[0]["title"] == "SQL Injection Vulnerability"
        assert findings[0]["severity"] == "high"
        assert "parameterized queries" in findings[0]["recommendation"]

        Path("test_file.py").unlink()  # Cleanup

    def test_no_false_positives(self):
        """Test that analyzer doesn't flag safe code."""
        safe_content = """
def safe_function():
    query = "SELECT * FROM users WHERE id = ?"
    return db.execute(query, [user_id])
        """

        with open("test_file.py", "w") as f:
            f.write(safe_content)

        findings = self.analyzer.analyze_target("test_file.py")

        assert len(findings) == 0  # No false positives

        Path("test_file.py").unlink()  # Cleanup

    def test_required_fields_present(self):
        """Test that all findings have required fields."""
        test_content = "problematic_pattern here"

        with open("test_file.py", "w") as f:
            f.write(test_content)

        findings = self.analyzer.analyze_target("test_file.py")

        required_fields = ["title", "description", "severity", "file_path", "line_number", "recommendation"]

        for finding in findings:
            for field in required_fields:
                assert field in finding, f"Missing required field: {field}"

            # Validate no generic placeholders
            assert finding["title"] != "security finding"
            assert finding["description"] != "Analysis issue detected"
            assert finding["file_path"] != "unknown"
            assert finding["line_number"] > 0

        Path("test_file.py").unlink()  # Cleanup
```

### **Integration Testing**

```bash
#!/bin/bash
# test_analyzer_integration.sh

echo "Testing MyCustomAnalyzer integration..."

# Test CLI functionality
cd shared
PYTHONPATH=. python analyzers/category/my_custom_analyzer.py ../test_codebase/monorepo --max-files 5 > /tmp/analyzer_output.json

# Validate output format
if jq empty /tmp/analyzer_output.json 2>/dev/null; then
    echo "✅ Valid JSON output"
else
    echo "❌ Invalid JSON output"
    exit 1
fi

# Check for required fields in findings
if jq -e '.findings[] | select(has("title") and has("description") and has("severity") and has("file_path") and has("line_number") and has("recommendation"))' /tmp/analyzer_output.json > /dev/null; then
    echo "✅ All required fields present"
else
    echo "❌ Missing required fields"
    exit 1
fi

# Check for placeholder values
if jq -e '.findings[] | select(.title == "security finding" or .description == "Analysis issue detected")' /tmp/analyzer_output.json > /dev/null; then
    echo "❌ Found placeholder values"
    exit 1
else
    echo "✅ No placeholder values found"
fi

echo "All integration tests passed!"
```

## 🚀 **Deployment and Distribution**

### **Installation Integration**

Your analyzer will be automatically included in the installation process if placed in the correct directory structure. The `install.sh` script copies all `shared/analyzers/` content to the target installation.

### **Documentation**

- Update `CLAUDE.md` with your analyzer's capabilities
- Add examples to `shared/core/base/ANALYZER_INTERFACE.md` if implementing novel patterns
- Include usage examples in your analyzer's docstring

### **Version Compatibility**

- All analyzers should support Python 3.8+ (the minimum version for BaseAnalyzer)
- Use type hints for better IDE support and documentation
- Follow the existing code style and formatting conventions

## 🎯 **Success Criteria**

Your analyzer is ready for production when:

- [ ] **Extends BaseAnalyzer/BaseProfiler** correctly
- [ ] **All required abstract methods** implemented
- [ ] **Strict validation passing** - No placeholder findings
- [ ] **Unit tests written** with good coverage
- [ ] **Integration tests passing**
- [ ] **CLI interface working** - All standard arguments supported
- [ ] **Legacy compatibility** - Backward-compatible wrapper function
- [ ] **Documentation updated** - CLAUDE.md and interface docs
- [ ] **Real findings only** - No generic titles, descriptions, or recommendations

## 📚 **Reference and Resources**

### **Working Examples**

- **Simple Pattern Matching**: `shared/analyzers/security/check_auth.py`
- **External Tool Integration**: `shared/analyzers/quality/complexity_lizard.py`
- **Multi-Component Orchestration**: `shared/analyzers/quality/analysis_engine.py`
- **Performance Analysis**: `shared/analyzers/performance/profile_code.py`

### **Helper Functions**

- `create_standard_finding()` - Create properly formatted findings
- `validate_finding()` - Validate finding structure
- `batch_validate_findings()` - Validate lists of findings

### **Infrastructure Components**

- `BaseAnalyzer` - General analysis tools
- `BaseProfiler` - Performance analysis tools
- `AnalyzerConfig` - Standard configuration management
- `CLIBase` - Consistent command-line interfaces

---

**Created**: 2025-08-12
**BaseAnalyzer Version**: 2.0 (Strict Validation)
**Status**: Complete development guide for BaseAnalyzer/BaseProfiler ecosystem
**Next Steps**: Start building your analyzer using this template and patterns!
