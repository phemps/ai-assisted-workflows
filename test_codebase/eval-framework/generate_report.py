#!/usr/bin/env python3
"""
Evaluation Report Generator
==========================

PURPOSE: Generate human-readable evaluation reports from security analysis results.

APPROACH:
- Load evaluation results from run_evaluations.py output
- Generate comprehensive HTML and markdown reports
- Create visualizations and comparative analysis
- Identify trends and improvement opportunities
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import argparse

def count_expected_vulnerabilities(app_name: str, expected_data: Dict) -> int:
    """Count total expected vulnerabilities for an application."""
    app_data = expected_data.get("applications", {}).get(app_name, {})
    count = 0
    vulns = app_data.get("expected_vulnerabilities", {})
    
    def count_recursive(obj):
        """Recursively count vulnerabilities with 'locations' field."""
        if isinstance(obj, dict):
            if "locations" in obj:
                return len(obj.get("locations", []))
            else:
                total = 0
                for value in obj.values():
                    total += count_recursive(value)
                return total
        return 0
    
    return count_recursive(vulns)

def calculate_simplified_metrics(results: Dict, expected_data: Dict) -> List[Dict]:
    """Calculate simplified coverage metrics by application."""
    simplified = []
    
    # Group results by application
    by_app = {}
    for result in results.get("detailed_results", []):
        app = result.get("application", "unknown")
        if app not in by_app:
            by_app[app] = {"found": 0, "expected": 0}
        by_app[app]["found"] += result.get("findings_count", 0)
    
    # Add expected counts and calculate coverage
    for app, counts in by_app.items():
        counts["expected"] = count_expected_vulnerabilities(app, expected_data)
        counts["coverage"] = (counts["found"] / counts["expected"] * 100) if counts["expected"] > 0 else 0
        simplified.append({
            "application": app,
            "issues_found": counts["found"],
            "issues_expected": counts["expected"],
            "coverage_percent": counts["coverage"]
        })
    
    return simplified

def load_evaluation_results(results_path: str) -> Dict[str, Any]:
    """Load evaluation results from JSON file."""
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Results file not found: {results_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing results JSON: {e}")
        return {}

def generate_markdown_report(results: Dict[str, Any]) -> str:
    """Generate detailed markdown report."""
    
    if not results:
        return "# Evaluation Report\n\nNo results data available.\n"
    
    # Load expected findings for coverage calculation
    expected_data = {}
    expected_path = Path(__file__).parent / "expected_findings.json"
    if expected_path.exists():
        with open(expected_path, 'r') as f:
            expected_data = json.load(f)
    
    metadata = results.get("metadata", {})
    summary = results.get("summary", {})
    detailed = results.get("detailed_results", [])
    
    report = []
    
    # Header
    report.append("# Security Analysis Evaluation Report")
    report.append(f"\n**Generated:** {metadata.get('evaluation_date', 'Unknown')}")
    report.append(f"**Framework Version:** {metadata.get('framework_version', '1.0')}")
    report.append(f"**Applications Tested:** {metadata.get('total_applications', 0)}")
    report.append(f"**Analyzers Tested:** {metadata.get('total_analyzers', 0)}")
    
    # Executive Summary
    report.append("\n## Executive Summary")
    report.append(f"\n- **Total Evaluations:** {summary.get('total_evaluations', 0)}")
    report.append(f"- **Successful Runs:** {summary.get('successful_runs', 0)}")
    report.append(f"- **Failed Runs:** {summary.get('failed_runs', 0)}")
    
    success_rate = 0
    if summary.get('total_evaluations', 0) > 0:
        success_rate = (summary.get('successful_runs', 0) / summary.get('total_evaluations', 1)) * 100
    report.append(f"- **Success Rate:** {success_rate:.1f}%")
    
    # Overall Metrics
    if "average_metrics" in summary:
        metrics = summary["average_metrics"]
        report.append("\n### Overall Performance Metrics")
        report.append(f"\n- **Precision:** {metrics.get('precision', 0):.3f}")
        report.append(f"- **Recall:** {metrics.get('recall', 0):.3f}")
        report.append(f"- **F1-Score:** {metrics.get('f1_score', 0):.3f}")
        
        # Calculate overall accuracy score
        # Get aggregate metrics from detailed results
        total_tp = sum(result.get("metrics", {}).get("true_positives", 0) for result in detailed)
        total_fp = sum(result.get("metrics", {}).get("false_positives", 0) for result in detailed)
        total_fn = sum(result.get("metrics", {}).get("false_negatives", 0) for result in detailed)
        
        # Accuracy = TP / (TP + FP + FN) × 100
        accuracy = 0
        if (total_tp + total_fp + total_fn) > 0:
            accuracy = (total_tp / (total_tp + total_fp + total_fn)) * 100
            
        report.append(f"\n**Overall Accuracy:** {accuracy:.1f}%")
    
    # Analyzer Performance
    report.append("\n## Analyzer Performance")
    
    by_analyzer = summary.get("by_analyzer", {})
    if by_analyzer:
        report.append("\n| Analyzer | Total Runs | Success Rate | Avg Findings | Accuracy % |")
        report.append("|----------|------------|--------------|--------------|------------|")
        
        for analyzer, stats in by_analyzer.items():
            total_runs = stats.get("total_runs", 0)
            successful = stats.get("successful_runs", 0)
            success_rate = (successful / total_runs * 100) if total_runs > 0 else 0
            avg_findings = stats.get("total_findings", 0) / total_runs if total_runs > 0 else 0
            
            # Calculate accuracy for this analyzer from detailed results
            analyzer_tp = sum(result.get("metrics", {}).get("true_positives", 0) 
                             for result in detailed if result.get("analyzer") == analyzer)
            analyzer_fp = sum(result.get("metrics", {}).get("false_positives", 0) 
                             for result in detailed if result.get("analyzer") == analyzer)
            analyzer_fn = sum(result.get("metrics", {}).get("false_negatives", 0) 
                             for result in detailed if result.get("analyzer") == analyzer)
            
            accuracy = 0
            if (analyzer_tp + analyzer_fp + analyzer_fn) > 0:
                accuracy = (analyzer_tp / (analyzer_tp + analyzer_fp + analyzer_fn)) * 100
            
            report.append(f"| {analyzer} | {total_runs} | {success_rate:.1f}% | {avg_findings:.1f} | {accuracy:.1f}% |")
    
    # Application Coverage
    report.append("\n## Application Coverage")
    
    by_application = summary.get("by_application", {})
    if by_application:
        report.append("\n| Application | Language | Evaluations | Total Findings | Accuracy % |")
        report.append("|-------------|----------|-------------|----------------|------------|")
        
        for app, stats in by_application.items():
            # Get language info from detailed results
            language = "Unknown"
            for result in detailed:
                if result.get("application") == app:
                    language = result.get("language", "Unknown")
                    break
                    
            runs = stats.get("runs", 0)
            findings = stats.get("findings", 0)
            
            # Calculate accuracy for this application from detailed results
            app_tp = sum(result.get("metrics", {}).get("true_positives", 0) 
                        for result in detailed if result.get("application") == app)
            app_fp = sum(result.get("metrics", {}).get("false_positives", 0) 
                        for result in detailed if result.get("application") == app)
            app_fn = sum(result.get("metrics", {}).get("false_negatives", 0) 
                        for result in detailed if result.get("application") == app)
            
            accuracy = 0
            if (app_tp + app_fp + app_fn) > 0:
                accuracy = (app_tp / (app_tp + app_fp + app_fn)) * 100
            
            report.append(f"| {app} | {language} | {runs} | {findings} | {accuracy:.1f}% |")
    
    # Simplified Coverage Metrics
    report.append("\n## Simplified Coverage Metrics")
    report.append("\nThis table shows the percentage of expected vulnerabilities detected per application:")
    report.append("\n| Application | Issues Found | Issues Expected | Coverage % |")
    report.append("|-------------|--------------|-----------------|------------|")

    simplified_metrics = calculate_simplified_metrics(results, expected_data)
    for metric in simplified_metrics:
        report.append(
            f"| {metric['application']} | "
            f"{metric['issues_found']} | "
            f"{metric['issues_expected']} | "
            f"{metric['coverage_percent']:.1f}% |"
        )
    
    # Detailed Results by Application
    report.append("\n## Detailed Results by Application")
    
    # Group detailed results by application
    by_app = {}
    for result in detailed:
        app_name = result.get("application", "unknown")
        if app_name not in by_app:
            by_app[app_name] = []
        by_app[app_name].append(result)
    
    for app_name, app_results in by_app.items():
        report.append(f"\n### {app_name}")
        
        # Get application info
        language = app_results[0].get("language", "Unknown") if app_results else "Unknown"
        report.append(f"\n**Language:** {language}")
        
        # Results table for this application
        report.append("\n| Analyzer | Findings | True+ | False+ | False- | Precision | Recall | F1-Score |")
        report.append("|----------|----------|-------|--------|--------|-----------|--------|----------|")
        
        for result in app_results:
            analyzer = result.get("analyzer", "unknown")
            findings_count = result.get("findings_count", 0)
            metrics = result.get("metrics", {})
            
            tp = metrics.get("true_positives", 0)
            fp = metrics.get("false_positives", 0)
            fn = metrics.get("false_negatives", 0)
            precision = metrics.get("precision", 0)
            recall = metrics.get("recall", 0)
            f1 = metrics.get("f1_score", 0)
            
            report.append(f"| {analyzer} | {findings_count} | {tp} | {fp} | {fn} | {precision:.2f} | {recall:.2f} | {f1:.2f} |")
        
        # Highlight best performing analyzer for this app
        best_analyzer = None
        best_f1 = 0
        for result in app_results:
            f1 = result.get("metrics", {}).get("f1_score", 0)
            if f1 > best_f1:
                best_f1 = f1
                best_analyzer = result.get("analyzer")
        
        if best_analyzer and best_f1 > 0:
            report.append(f"\n**Best Performer:** {best_analyzer} (F1: {best_f1:.3f})")
    
    # Language Analysis
    report.append("\n## Language Analysis")
    
    by_language = summary.get("by_language", {})
    if by_language:
        report.append("\n| Language | Evaluations | Total Findings | Avg per Run |")
        report.append("|----------|-------------|----------------|-------------|")
        
        for language, stats in by_language.items():
            runs = stats.get("runs", 0)
            findings = stats.get("findings", 0)
            avg_per_run = findings / runs if runs > 0 else 0
            
            report.append(f"| {language} | {runs} | {findings} | {avg_per_run:.1f} |")
    
    # Recommendations
    report.append("\n## Recommendations")
    
    recommendations = []
    
    # Analyze results for recommendations
    if summary.get("failed_runs", 0) > 0:
        recommendations.append("🔧 **Fix Failed Runs**: Some analyzers failed to execute properly. Check logs and dependencies.")
    
    if "average_metrics" in summary:
        avg_f1 = summary["average_metrics"].get("f1_score", 0)
        if avg_f1 < 0.6:
            recommendations.append("📈 **Improve Detection Rules**: Low F1-score indicates room for improvement in detection accuracy.")
        
        avg_precision = summary["average_metrics"].get("precision", 0)
        if avg_precision < 0.7:
            recommendations.append("🎯 **Reduce False Positives**: Low precision suggests too many false positive detections.")
        
        avg_recall = summary["average_metrics"].get("recall", 0)
        if avg_recall < 0.7:
            recommendations.append("🔍 **Improve Coverage**: Low recall indicates missing vulnerability detections.")
    
    # Analyzer-specific recommendations
    for analyzer, stats in by_analyzer.items():
        success_rate = (stats.get("successful_runs", 0) / stats.get("total_runs", 1)) * 100
        if success_rate < 80:
            recommendations.append(f"⚠️ **Fix {analyzer}**: Success rate of {success_rate:.1f}% is below acceptable threshold.")
    
    if not recommendations:
        recommendations.append("✅ **Good Performance**: All analyzers are performing within acceptable ranges.")
    
    for i, rec in enumerate(recommendations, 1):
        report.append(f"\n{i}. {rec}")
    
    # Technical Details
    report.append("\n## Technical Details")
    report.append(f"\n- **Evaluation Framework:** Security Analysis Evaluation v{metadata.get('framework_version', '1.0')}")
    report.append(f"- **Total Runtime:** Calculated from individual analyzer execution times")
    report.append(f"- **Metrics Calculation:** Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2*(P*R)/(P+R)")
    report.append(f"- **Applications Path:** test_codebase/vulnerable-apps/")
    report.append(f"- **Expected Findings:** test_codebase/eval-framework/expected_findings.json")
    
    # Errors and Issues
    errors_found = []
    for result in detailed:
        if result.get("errors"):
            errors_found.extend(result["errors"])
    
    if errors_found:
        report.append("\n## Errors and Issues")
        for error in set(errors_found):  # Remove duplicates
            if error.strip():  # Only non-empty errors
                report.append(f"- {error}")
    
    return "\n".join(report)

def generate_html_report(markdown_content: str) -> str:
    """Convert markdown report to HTML with styling."""
    
    # Simple markdown to HTML conversion (basic implementation)
    html_lines = []
    in_table = False
    
    for line in markdown_content.split('\n'):
        line = line.strip()
        
        if not line:
            if not in_table:
                html_lines.append('<br>')
            continue
            
        # Headers
        if line.startswith('# '):
            html_lines.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('### '):
            html_lines.append(f'<h3>{line[4:]}</h3>')
        
        # Table detection
        elif '|' in line and not line.startswith('|--'):
            if not in_table:
                html_lines.append('<table border="1" style="border-collapse: collapse; margin: 10px 0;">')
                in_table = True
            
            # Convert table row
            cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
            if any('---' in cell for cell in cells):
                continue  # Skip header separator
            
            row_html = '<tr>'
            for cell in cells:
                # Apply basic formatting
                cell = cell.replace('✅', '<span style="color: green;">✅</span>')
                cell = cell.replace('❌', '<span style="color: red;">❌</span>')
                cell = cell.replace('⚠️', '<span style="color: orange;">⚠️</span>')
                cell = cell.replace('🟢', '<span style="color: green;">🟢</span>')
                cell = cell.replace('🔴', '<span style="color: red;">🔴</span>')
                
                row_html += f'<td style="padding: 5px;">{cell}</td>'
            row_html += '</tr>'
            html_lines.append(row_html)
        
        # List items
        elif line.startswith('- '):
            if in_table:
                html_lines.append('</table>')
                in_table = False
            html_lines.append(f'<li>{line[2:]}</li>')
        
        # Numbered lists
        elif line[0].isdigit() and '. ' in line:
            if in_table:
                html_lines.append('</table>')
                in_table = False
            html_lines.append(f'<li>{line.split(". ", 1)[1]}</li>')
        
        # Bold text
        elif line.startswith('**') and line.endswith('**'):
            if in_table:
                html_lines.append('</table>')
                in_table = False
            html_lines.append(f'<strong>{line[2:-2]}</strong>')
        
        # Regular paragraphs
        else:
            if in_table:
                html_lines.append('</table>')
                in_table = False
            
            # Apply basic formatting
            line = line.replace('**', '<strong>').replace('**', '</strong>')
            html_lines.append(f'<p>{line}</p>')
    
    # Close any open table
    if in_table:
        html_lines.append('</table>')
    
    # Wrap in complete HTML document
    html_doc = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Analysis Evaluation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            h1 {{ color: #333; border-bottom: 2px solid #333; }}
            h2 {{ color: #666; border-bottom: 1px solid #666; }}
            h3 {{ color: #888; }}
            table {{ width: 100%; margin: 10px 0; }}
            th, td {{ padding: 8px; text-align: left; }}
            .success {{ color: green; }}
            .warning {{ color: orange; }}
            .error {{ color: red; }}
            .metric {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        {''.join(html_lines)}
    </body>
    </html>
    """
    
    return html_doc

def main():
    parser = argparse.ArgumentParser(description="Generate evaluation reports")
    parser.add_argument("--results", default="test_codebase/eval-framework/evaluation_results.json",
                       help="Path to evaluation results JSON file")
    parser.add_argument("--output", default="test_codebase/eval-framework/evaluation_report",
                       help="Output file prefix (will create .md and .html versions)")
    parser.add_argument("--format", choices=["markdown", "html", "both"], default="both",
                       help="Report format to generate")
    
    args = parser.parse_args()
    
    # Load evaluation results
    results = load_evaluation_results(args.results)
    if not results:
        print("No results to process")
        return
    
    # Generate markdown report
    markdown_content = generate_markdown_report(results)
    
    # Save reports
    if args.format in ["markdown", "both"]:
        markdown_path = Path(f"{args.output}.md")
        with open(markdown_path, 'w') as f:
            f.write(markdown_content)
        print(f"📄 Markdown report saved to: {markdown_path}")
    
    if args.format in ["html", "both"]:
        html_content = generate_html_report(markdown_content)
        html_path = Path(f"{args.output}.html")
        with open(html_path, 'w') as f:
            f.write(html_content)
        print(f"🌐 HTML report saved to: {html_path}")
    
    print("\n✅ Report generation complete")

if __name__ == "__main__":
    main()