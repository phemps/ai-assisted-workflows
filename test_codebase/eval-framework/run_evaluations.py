#!/usr/bin/env python3
"""
Security Analysis Evaluation Framework
=====================================

PURPOSE: Evaluate the effectiveness of our security analysis tools by running them
against known vulnerable applications and comparing results with expected findings.

APPROACH:
- Run all available security analyzers against vulnerable test applications
- Compare actual findings with expected vulnerabilities from expected_findings.json
- Calculate metrics: precision, recall, false positives, false negatives
- Generate detailed evaluation reports
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import argparse

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class EvaluationResult:
    """Results from running an analyzer against a vulnerable application."""
    analyzer: str
    application: str
    language: str
    execution_time: float
    findings: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    exit_code: int = 0

@dataclass
class EvaluationMetrics:
    """Evaluation metrics for comparing actual vs expected findings."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    coverage: float = 0.0

class SecurityEvaluationFramework:
    """Framework for evaluating security analyzer effectiveness."""

    def __init__(self, config_path: str = "test_codebase/eval-framework/expected_findings.json"):
        logger.info("🚀 Initializing SecurityEvaluationFramework")
        
        # Get absolute paths to avoid relative path issues
        script_dir = Path(__file__).parent.absolute()
        project_root = script_dir.parent.parent  # Go up from eval-framework to test_codebase to project root
        
        logger.debug(f"Script directory: {script_dir}")
        logger.debug(f"Project root: {project_root}")
        
        self.config_path = Path(config_path)
        if not self.config_path.is_absolute():
            # If config_path is relative, make it relative to script directory
            self.config_path = script_dir / config_path if config_path == "expected_findings.json" else project_root / config_path
            
        self.vulnerable_apps_dir = script_dir.parent / "vulnerable-apps"  # test_codebase/vulnerable-apps
        self.shared_analyzers_dir = project_root / "shared" / "analyzers"
        
        logger.info(f"Config path: {self.config_path}")
        logger.info(f"Vulnerable apps directory: {self.vulnerable_apps_dir}")
        logger.info(f"Shared analyzers directory: {self.shared_analyzers_dir}")
        
        # Load expected findings
        logger.info("📖 Loading expected findings...")
        self.expected_findings = self._load_expected_findings()
        logger.info(f"Loaded {len(self.expected_findings.get('applications', {}))} applications")
        
        # Available analyzers
        self.analyzers = {
            "semgrep": self.shared_analyzers_dir / "security" / "semgrep_analyzer.py",
            "detect_secrets": self.shared_analyzers_dir / "security" / "detect_secrets_analyzer.py", 
            "sqlfluff": self.shared_analyzers_dir / "performance" / "sqlfluff_analyzer.py",
        }
        
        logger.info(f"Available analyzers: {list(self.analyzers.keys())}")
        
        # Verify analyzer scripts exist
        for name, path in self.analyzers.items():
            if path.exists():
                logger.debug(f"✅ {name}: {path}")
            else:
                logger.warning(f"❌ {name}: {path} (not found)")
                
        logger.info("✅ Framework initialization complete")

    def _load_expected_findings(self) -> Dict[str, Any]:
        """Load expected findings from JSON configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Expected findings file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing expected findings JSON: {e}")
            return {}

    def run_analyzer(self, analyzer_name: str, app_path: Path, app_name: str) -> EvaluationResult:
        """Run a specific analyzer against a vulnerable application."""
        logger.info(f"🔍 Running analyzer: {analyzer_name} on {app_name}")
        
        analyzer_script = self.analyzers.get(analyzer_name)
        if not analyzer_script or not analyzer_script.exists():
            logger.error(f"❌ Analyzer script not found: {analyzer_script}")
            return EvaluationResult(
                analyzer=analyzer_name,
                application=app_name,
                language="unknown",
                execution_time=0.0,
                errors=[f"Analyzer script not found: {analyzer_script}"]
            )

        logger.debug(f"✅ Analyzer script found: {analyzer_script}")
        logger.debug(f"App path exists: {app_path.exists()}")

        start_time = time.time()
        
        try:
            # Run analyzer with JSON output format
            cmd = [
                sys.executable, str(analyzer_script),
                str(app_path),
                "--output-format", "json",
                "--max-files", "50"  # Limit for evaluation
            ]
            
            logger.info(f"Command: {' '.join(cmd)}")
            logger.info(f"Working directory: {project_root}")
            logger.info("⏳ Starting subprocess...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=project_root
            )
            
            logger.info(f"✅ Subprocess completed in {time.time() - start_time:.2f}s")
            
            execution_time = time.time() - start_time
            
            logger.info(f"Return code: {result.returncode}")
            logger.debug(f"Stdout length: {len(result.stdout) if result.stdout else 0}")
            logger.debug(f"Stderr length: {len(result.stderr) if result.stderr else 0}")
            
            if result.stderr:
                logger.warning(f"Stderr: {result.stderr[:500]}")
            
            # Parse JSON output
            findings = []
            if result.stdout:
                logger.info("📊 Parsing JSON output...")
                try:
                    output_data = json.loads(result.stdout)
                    if isinstance(output_data, dict):
                        findings = output_data.get('findings', [])
                    elif isinstance(output_data, list):
                        findings = output_data
                    logger.info(f"Found {len(findings)} findings")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON output: {e}")
                    logger.debug(f"Raw stdout: {result.stdout[:1000]}")
            else:
                logger.warning("No stdout output from analyzer")

            # Get application language
            app_info = self.expected_findings.get("applications", {}).get(app_name, {})
            language = app_info.get("language", "unknown")
            logger.debug(f"Application language: {language}")

            return EvaluationResult(
                analyzer=analyzer_name,
                application=app_name,
                language=language,
                execution_time=execution_time,
                findings=findings,
                errors=[result.stderr] if result.stderr else [],
                exit_code=result.returncode
            )

        except subprocess.TimeoutExpired:
            return EvaluationResult(
                analyzer=analyzer_name,
                application=app_name,
                language="unknown", 
                execution_time=time.time() - start_time,
                errors=["Analyzer execution timed out"]
            )
        except Exception as e:
            return EvaluationResult(
                analyzer=analyzer_name,
                application=app_name,
                language="unknown",
                execution_time=time.time() - start_time,
                errors=[f"Execution error: {str(e)}"]
            )

    def calculate_metrics(self, analyzer_name: str, app_name: str, actual_findings: List[Dict[str, Any]]) -> EvaluationMetrics:
        """Calculate evaluation metrics by comparing actual vs expected findings."""
        
        # Get expected vulnerabilities for this app
        app_config = self.expected_findings.get("applications", {}).get(app_name, {})
        expected_vulns = app_config.get("expected_vulnerabilities", {})
        
        # Get analyzer capabilities 
        analyzer_mapping = self.expected_findings.get("analyzer_mapping", {}).get(analyzer_name, {})
        should_detect = set(analyzer_mapping.get("should_detect", []))
        
        # Flatten expected vulnerabilities that this analyzer should detect
        expected_detectable = set()
        for category, vulns in expected_vulns.items():
            for vuln_type, vuln_info in vulns.items():
                if vuln_type in should_detect or category in should_detect:
                    expected_detectable.add(vuln_type)
        
        # Classify findings
        detected_types = set()
        for finding in actual_findings:
            # Extract vulnerability type from finding
            vuln_type = self._extract_vulnerability_type(finding)
            if vuln_type:
                detected_types.add(vuln_type)
        
        # Calculate metrics
        true_positives = len(detected_types & expected_detectable)
        false_positives = len(detected_types - expected_detectable)
        false_negatives = len(expected_detectable - detected_types)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        coverage = len(detected_types) / len(expected_detectable) if expected_detectable else 0
        
        return EvaluationMetrics(
            true_positives=true_positives,
            false_positives=false_positives, 
            false_negatives=false_negatives,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            coverage=coverage
        )

    def _extract_vulnerability_type(self, finding: Dict[str, Any]) -> Optional[str]:
        """Extract vulnerability type from analyzer finding."""
        # This is a simplified approach - real implementation would need 
        # more sophisticated mapping based on each analyzer's output format
        
        message = finding.get('message', '').lower()
        check_id = finding.get('check_id', '').lower()
        rule_id = finding.get('rule_id', '').lower()
        
        # Common patterns to identify vulnerability types
        if any(term in message or term in check_id or term in rule_id 
               for term in ['sql injection', 'sqli']):
            return 'sql_injection'
        elif any(term in message or term in check_id or term in rule_id 
                 for term in ['xss', 'cross-site scripting']):
            return 'xss'
        elif any(term in message or term in check_id or term in rule_id 
                 for term in ['command injection', 'exec']):
            return 'command_injection'
        elif any(term in message or term in check_id or term in rule_id 
                 for term in ['hardcoded', 'secret', 'password']):
            return 'hardcoded_secrets'
        elif any(term in message or term in check_id or term in rule_id 
                 for term in ['path traversal', 'lfi']):
            return 'path_traversal'
        elif any(term in message or term in check_id or term in rule_id 
                 for term in ['unsafe', 'buffer overflow']):
            return 'unsafe_usage'
        
        return None

    def run_filtered_evaluation(self, target_analyzer: Optional[str] = None, target_application: Optional[str] = None) -> Dict[str, Any]:
        """Run evaluation with optional filtering by analyzer or application."""
        
        logger.info("🚀 Starting filtered evaluation")
        
        results = []
        summary = {
            "total_evaluations": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "average_metrics": {},
            "by_analyzer": {},
            "by_application": {},
            "by_language": {}
        }
        
        # Filter applications
        applications = list(self.expected_findings.get('applications', {}).keys())
        if target_application:
            if target_application in applications:
                applications = [target_application]
                logger.info(f"Filtering to application: {target_application}")
            else:
                logger.error(f"Application '{target_application}' not found in expected findings")
                return self._empty_result()
        
        # Filter analyzers  
        analyzers = dict(self.analyzers.items())
        if target_analyzer:
            if target_analyzer in analyzers:
                analyzers = {target_analyzer: self.analyzers[target_analyzer]}
                logger.info(f"Filtering to analyzer: {target_analyzer}")
            else:
                logger.error(f"Analyzer '{target_analyzer}' not available")
                return self._empty_result()
        
        print("🚀 Starting Security Analysis Evaluation")
        print(f"Target applications: {applications}")
        print(f"Target analyzers: {list(analyzers.keys())}")
        print()
        
        logger.info(f"Will evaluate {len(applications)} applications with {len(analyzers)} analyzers")
        
        # Run each analyzer against each application
        app_counter = 0
        for app_name in applications:
            app_counter += 1
            logger.info(f"📂 Processing application {app_counter}/{len(applications)}: {app_name}")
            
            app_path = self.vulnerable_apps_dir / app_name
            if not app_path.exists():
                logger.warning(f"⚠️  Application directory not found: {app_path}")
                print(f"⚠️  Application directory not found: {app_path}")
                continue
                
            print(f"📂 Evaluating application: {app_name}")
            
            analyzer_counter = 0
            for analyzer_name, analyzer_path in analyzers.items():
                analyzer_counter += 1
                logger.info(f"  🔍 Running analyzer {analyzer_counter}/{len(analyzers)}: {analyzer_name}")
                print(f"  🔍 Running {analyzer_name}...")
                
                result = self.run_analyzer(analyzer_name, app_path, app_name)
                results.append(result)
                
                summary["total_evaluations"] += 1
                if result.exit_code == 0:
                    summary["successful_runs"] += 1
                    logger.info(f"    ✅ Success: {len(result.findings)} findings")
                    print(f"    ✅ Success: {len(result.findings)} findings")
                else:
                    summary["failed_runs"] += 1
                    logger.error(f"    ❌ Failed: {result.errors}")
                    print(f"    ❌ Failed: {result.errors}")
        
        logger.info("📊 Calculating summary metrics...")
        # Calculate summary metrics
        self._calculate_summary_metrics(results, summary)
        
        logger.info("✅ Evaluation complete, preparing results...")
        
        return {
            "metadata": {
                "evaluation_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "framework_version": "1.0",
                "total_applications": len(applications),
                "total_analyzers": len(analyzers)
            },
            "summary": summary,
            "detailed_results": [self._result_to_dict(r) for r in results]
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure for error cases."""
        return {
            "metadata": {
                "evaluation_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "framework_version": "1.0",
                "total_applications": 0,
                "total_analyzers": 0
            },
            "summary": {
                "total_evaluations": 0,
                "successful_runs": 0,
                "failed_runs": 0,
            },
            "detailed_results": []
        }

    def run_full_evaluation(self) -> Dict[str, Any]:
        """Run complete evaluation across all analyzers and applications."""
        
        results = []
        summary = {
            "total_evaluations": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "average_metrics": {},
            "by_analyzer": {},
            "by_application": {},
            "by_language": {}
        }
        
        print("🚀 Starting Security Analysis Evaluation")
        print(f"Available applications: {list(self.expected_findings.get('applications', {}).keys())}")
        print(f"Available analyzers: {list(self.analyzers.keys())}")
        print()
        
        # Run each analyzer against each application
        for app_name in self.expected_findings.get("applications", {}):
            app_path = self.vulnerable_apps_dir / app_name
            if not app_path.exists():
                print(f"⚠️  Application directory not found: {app_path}")
                continue
                
            print(f"📂 Evaluating application: {app_name}")
            
            for analyzer_name in self.analyzers:
                print(f"  🔍 Running {analyzer_name}...")
                
                # Run analyzer
                eval_result = self.run_analyzer(analyzer_name, app_path, app_name)
                
                # Calculate metrics
                metrics = self.calculate_metrics(analyzer_name, app_name, eval_result.findings)
                
                # Store results
                result_data = {
                    "analyzer": analyzer_name,
                    "application": app_name,
                    "language": eval_result.language,
                    "execution_time": eval_result.execution_time,
                    "findings_count": len(eval_result.findings),
                    "errors": eval_result.errors,
                    "exit_code": eval_result.exit_code,
                    "metrics": {
                        "true_positives": metrics.true_positives,
                        "false_positives": metrics.false_positives,
                        "false_negatives": metrics.false_negatives,
                        "precision": metrics.precision,
                        "recall": metrics.recall,
                        "f1_score": metrics.f1_score,
                        "coverage": metrics.coverage
                    }
                }
                
                results.append(result_data)
                summary["total_evaluations"] += 1
                
                if eval_result.exit_code == 0 and not eval_result.errors:
                    summary["successful_runs"] += 1
                    print(f"    ✅ Success: {len(eval_result.findings)} findings, F1={metrics.f1_score:.2f}")
                else:
                    summary["failed_runs"] += 1  
                    print(f"    ❌ Failed: {eval_result.errors}")
        
        # Calculate summary statistics
        self._calculate_summary_stats(results, summary)
        
        return {
            "metadata": {
                "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "framework_version": "1.0",
                "total_applications": len(self.expected_findings.get("applications", {})),
                "total_analyzers": len(self.analyzers)
            },
            "summary": summary,
            "detailed_results": results
        }

    def _calculate_summary_stats(self, results: List[Dict[str, Any]], summary: Dict[str, Any]):
        """Calculate summary statistics from detailed results."""
        
        if not results:
            return
            
        # Group by analyzer
        by_analyzer = {}
        by_application = {}
        by_language = {}
        
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        valid_metrics = 0
        
        for result in results:
            analyzer = result["analyzer"]
            app = result["application"] 
            lang = result["language"]
            metrics = result["metrics"]
            
            # By analyzer
            if analyzer not in by_analyzer:
                by_analyzer[analyzer] = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "total_findings": 0,
                    "avg_precision": 0,
                    "avg_recall": 0,
                    "avg_f1": 0
                }
            
            by_analyzer[analyzer]["total_runs"] += 1
            if result["exit_code"] == 0:
                by_analyzer[analyzer]["successful_runs"] += 1
            by_analyzer[analyzer]["total_findings"] += result["findings_count"]
            
            # Similar grouping for applications and languages
            for group_dict, key in [(by_application, app), (by_language, lang)]:
                if key not in group_dict:
                    group_dict[key] = {"runs": 0, "findings": 0, "avg_f1": 0}
                group_dict[key]["runs"] += 1
                group_dict[key]["findings"] += result["findings_count"]
            
            # Overall averages
            if metrics["precision"] > 0 or metrics["recall"] > 0:
                total_precision += metrics["precision"]
                total_recall += metrics["recall"] 
                total_f1 += metrics["f1_score"]
                valid_metrics += 1
        
        # Calculate averages
        if valid_metrics > 0:
            summary["average_metrics"] = {
                "precision": total_precision / valid_metrics,
                "recall": total_recall / valid_metrics,
                "f1_score": total_f1 / valid_metrics
            }
        
        summary["by_analyzer"] = by_analyzer
        summary["by_application"] = by_application  
        summary["by_language"] = by_language

def main():
    parser = argparse.ArgumentParser(description="Security Analysis Evaluation Framework")
    parser.add_argument("--config", default="test_codebase/eval-framework/expected_findings.json",
                       help="Path to expected findings configuration")
    parser.add_argument("--output", default="test_codebase/eval-framework/evaluation_results.json", 
                       help="Output file for results")
    parser.add_argument("--analyzer", help="Run specific analyzer only")
    parser.add_argument("--application", help="Run against specific application only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    logger.info(f"Arguments: analyzer={args.analyzer}, application={args.application}, verbose={args.verbose}")
    
    # Create evaluation framework
    framework = SecurityEvaluationFramework(args.config)
    
    # Run evaluation with filtering
    results = framework.run_filtered_evaluation(
        target_analyzer=args.analyzer,
        target_application=args.application
    )
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Evaluation Results Summary:")
    print(f"Total evaluations: {results['summary']['total_evaluations']}")
    print(f"Successful runs: {results['summary']['successful_runs']}")
    print(f"Failed runs: {results['summary']['failed_runs']}")
    
    if "average_metrics" in results["summary"] and results["summary"]["average_metrics"]:
        metrics = results["summary"]["average_metrics"]
        print(f"Average Precision: {metrics.get('precision', 0):.3f}")
        print(f"Average Recall: {metrics.get('recall', 0):.3f}")  
        print(f"Average F1-Score: {metrics.get('f1_score', 0):.3f}")
    
    print(f"\n📝 Detailed results saved to: {output_path}")

if __name__ == "__main__":
    main()