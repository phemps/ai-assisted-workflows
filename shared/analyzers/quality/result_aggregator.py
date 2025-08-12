#!/usr/bin/env python3
"""
Analysis Result Aggregation System
Part of Phase 2.4: Analysis Engine - Result Aggregation

This module aggregates results from multiple analysis engines (duplicate detection,
pattern classification, etc.) into unified, actionable reports with prioritization
and correlation analysis.
"""

import json
from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
import logging
from enum import Enum
from collections import defaultdict, Counter

from .duplicate_detection import DuplicateMatch
from .pattern_classifier import (
    PatternMatch,
    PatternSeverity,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of analysis that can be aggregated."""

    DUPLICATE_DETECTION = "duplicate_detection"
    PATTERN_CLASSIFICATION = "pattern_classification"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"


class Priority(Enum):
    """Priority levels for analysis findings."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


@dataclass
class AnalysisResult:
    """Unified representation of analysis results."""

    analysis_id: str
    analysis_type: AnalysisType
    file_path: str
    start_line: int
    end_line: int
    title: str
    description: str
    recommendation: str
    priority: Priority
    confidence: float
    code_snippet: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["analysis_type"] = self.analysis_type.value
        result["priority"] = self.priority.value
        result["created_at"] = self.created_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisResult":
        """Create from dictionary."""
        data["analysis_type"] = AnalysisType(data["analysis_type"])
        data["priority"] = Priority(data["priority"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class FileAnalysisSummary:
    """Summary of analysis results for a single file."""

    file_path: str
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    info_issues: int
    avg_confidence: float
    analysis_types: Set[AnalysisType]
    first_analyzed: datetime
    last_analyzed: datetime

    def get_severity_distribution(self) -> Dict[str, int]:
        """Get distribution of issues by severity."""
        return {
            "critical": self.critical_issues,
            "high": self.high_issues,
            "medium": self.medium_issues,
            "low": self.low_issues,
            "info": self.info_issues,
        }


@dataclass
class ProjectAnalysisSummary:
    """Summary of analysis results for the entire project."""

    project_path: str
    total_files_analyzed: int
    total_issues: int
    issues_by_priority: Dict[Priority, int]
    issues_by_type: Dict[AnalysisType, int]
    files_with_issues: int
    avg_confidence: float
    top_problematic_files: List[Tuple[str, int]]  # (file_path, issue_count)
    analysis_duration: float  # seconds
    created_at: datetime = field(default_factory=datetime.now)


class ResultConverter:
    """Converts analysis results from various engines to unified format."""

    @staticmethod
    def convert_duplicate_matches(
        matches: List[DuplicateMatch],
    ) -> List[AnalysisResult]:
        """Convert duplicate detection results to unified format."""
        results = []

        for match in matches:
            # Create result for first block
            result1 = AnalysisResult(
                analysis_id=f"dup_{hash(match.block1.file_path + str(match.block1.start_line))}",
                analysis_type=AnalysisType.DUPLICATE_DETECTION,
                file_path=match.block1.file_path,
                start_line=match.block1.start_line,
                end_line=match.block1.end_line,
                title=f"Duplicate Code ({match.match_type.capitalize()})",
                description=f"Code block is {match.similarity_score:.1%} similar to {match.block2.file_path}:{match.block2.start_line}-{match.block2.end_line}",
                recommendation="Consider extracting common code into a shared function or class",
                priority=ResultConverter._get_duplicate_priority(match),
                confidence=match.confidence,
                code_snippet=match.block1.content[:200] + "..."
                if len(match.block1.content) > 200
                else match.block1.content,
                metadata={
                    "duplicate_location": f"{match.block2.file_path}:{match.block2.start_line}-{match.block2.end_line}",
                    "similarity_score": match.similarity_score,
                    "match_type": match.match_type,
                    **match.metadata,
                },
            )

            # Create result for second block
            result2 = AnalysisResult(
                analysis_id=f"dup_{hash(match.block2.file_path + str(match.block2.start_line))}",
                analysis_type=AnalysisType.DUPLICATE_DETECTION,
                file_path=match.block2.file_path,
                start_line=match.block2.start_line,
                end_line=match.block2.end_line,
                title=f"Duplicate Code ({match.match_type.capitalize()})",
                description=f"Code block is {match.similarity_score:.1%} similar to {match.block1.file_path}:{match.block1.start_line}-{match.block1.end_line}",
                recommendation="Consider extracting common code into a shared function or class",
                priority=ResultConverter._get_duplicate_priority(match),
                confidence=match.confidence,
                code_snippet=match.block2.content[:200] + "..."
                if len(match.block2.content) > 200
                else match.block2.content,
                metadata={
                    "duplicate_location": f"{match.block1.file_path}:{match.block1.start_line}-{match.block1.end_line}",
                    "similarity_score": match.similarity_score,
                    "match_type": match.match_type,
                    **match.metadata,
                },
            )

            results.extend([result1, result2])

        return results

    @staticmethod
    def convert_pattern_matches(matches: List[PatternMatch]) -> List[AnalysisResult]:
        """Convert pattern classification results to unified format."""
        results = []

        for match in matches:
            result = AnalysisResult(
                analysis_id=f"pat_{hash(match.file_path + match.pattern_name + str(match.start_line))}",
                analysis_type=AnalysisType.PATTERN_CLASSIFICATION,
                file_path=match.file_path,
                start_line=match.start_line,
                end_line=match.end_line,
                title=match.pattern_name,
                description=match.description,
                recommendation=match.recommendation,
                priority=ResultConverter._get_pattern_priority(match),
                confidence=match.confidence,
                code_snippet=match.code_snippet,
                metadata={
                    "pattern_type": match.pattern_type.value,
                    "severity": match.severity.value,
                    **match.metadata,
                },
            )
            results.append(result)

        return results

    @staticmethod
    def _get_duplicate_priority(match: DuplicateMatch) -> Priority:
        """Determine priority for duplicate code matches."""
        if match.similarity_score >= 0.95:
            return Priority.HIGH
        elif match.similarity_score >= 0.8:
            return Priority.MEDIUM
        else:
            return Priority.LOW

    @staticmethod
    def _get_pattern_priority(match: PatternMatch) -> Priority:
        """Determine priority for pattern matches."""
        severity_map = {
            PatternSeverity.CRITICAL: Priority.CRITICAL,
            PatternSeverity.HIGH: Priority.HIGH,
            PatternSeverity.MEDIUM: Priority.MEDIUM,
            PatternSeverity.LOW: Priority.LOW,
            PatternSeverity.INFO: Priority.INFO,
        }
        return severity_map.get(match.severity, Priority.LOW)


class ResultCorrelator:
    """Correlates related analysis results for better insights."""

    def __init__(self):
        self.correlation_rules = [
            self._correlate_duplicates_and_patterns,
            self._correlate_file_hotspots,
            self._correlate_similar_issues,
        ]

    def correlate_results(
        self, results: List[AnalysisResult]
    ) -> Dict[str, List[AnalysisResult]]:
        """Find correlated results and group them."""
        correlations = {}

        for rule in self.correlation_rules:
            try:
                correlations.update(rule(results))
            except Exception as e:
                logger.debug(f"Correlation rule error: {e}")

        return correlations

    def _correlate_duplicates_and_patterns(
        self, results: List[AnalysisResult]
    ) -> Dict[str, List[AnalysisResult]]:
        """Find files that have both duplicates and patterns."""
        correlations = {}

        # Group by file
        file_results = defaultdict(list)
        for result in results:
            file_results[result.file_path].append(result)

        # Find files with multiple issue types
        for file_path, file_results_list in file_results.items():
            analysis_types = set(result.analysis_type for result in file_results_list)

            if (
                AnalysisType.DUPLICATE_DETECTION in analysis_types
                and AnalysisType.PATTERN_CLASSIFICATION in analysis_types
            ):
                correlations[f"multi_issue_file:{file_path}"] = file_results_list

        return correlations

    def _correlate_file_hotspots(
        self, results: List[AnalysisResult]
    ) -> Dict[str, List[AnalysisResult]]:
        """Identify files with many issues (hotspots)."""
        correlations = {}

        # Count issues per file
        file_issue_counts = Counter(result.file_path for result in results)

        # Find hotspots (files with more than 5 issues)
        for file_path, count in file_issue_counts.items():
            if count >= 5:
                hotspot_results = [r for r in results if r.file_path == file_path]
                correlations[f"hotspot:{file_path}"] = hotspot_results

        return correlations

    def _correlate_similar_issues(
        self, results: List[AnalysisResult]
    ) -> Dict[str, List[AnalysisResult]]:
        """Find similar issues across different files."""
        correlations = {}

        # Group by title/issue type
        title_groups = defaultdict(list)
        for result in results:
            title_groups[result.title].append(result)

        # Find recurring issues (same issue in multiple files)
        for title, title_results in title_groups.items():
            if len(title_results) >= 3:  # Same issue in 3+ files
                files = set(result.file_path for result in title_results)
                if len(files) >= 2:  # Ensure it's across different files
                    correlations[f"recurring_issue:{title}"] = title_results

        return correlations


class AnalysisAggregator:
    """Main aggregator that combines and organizes analysis results."""

    def __init__(self):
        self.converter = ResultConverter()
        self.correlator = ResultCorrelator()
        self.results: List[AnalysisResult] = []

    def add_duplicate_analysis(self, matches: List[DuplicateMatch]) -> None:
        """Add duplicate detection results."""
        converted = self.converter.convert_duplicate_matches(matches)
        self.results.extend(converted)
        logger.info(f"Added {len(converted)} duplicate analysis results")

    def add_pattern_analysis(self, matches: List[PatternMatch]) -> None:
        """Add pattern classification results."""
        converted = self.converter.convert_pattern_matches(matches)
        self.results.extend(converted)
        logger.info(f"Added {len(converted)} pattern analysis results")

    def add_custom_analysis(self, results: List[AnalysisResult]) -> None:
        """Add custom analysis results."""
        self.results.extend(results)
        logger.info(f"Added {len(results)} custom analysis results")

    def generate_file_summaries(self) -> Dict[str, FileAnalysisSummary]:
        """Generate summaries for each file."""
        file_summaries = {}

        # Group results by file
        file_groups = defaultdict(list)
        for result in self.results:
            file_groups[result.file_path].append(result)

        # Create summaries
        for file_path, file_results in file_groups.items():
            # Count by priority
            priority_counts = Counter(result.priority for result in file_results)

            # Calculate statistics
            confidences = [result.confidence for result in file_results]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            analysis_types = set(result.analysis_type for result in file_results)
            timestamps = [result.created_at for result in file_results]

            summary = FileAnalysisSummary(
                file_path=file_path,
                total_issues=len(file_results),
                critical_issues=priority_counts.get(Priority.CRITICAL, 0),
                high_issues=priority_counts.get(Priority.HIGH, 0),
                medium_issues=priority_counts.get(Priority.MEDIUM, 0),
                low_issues=priority_counts.get(Priority.LOW, 0),
                info_issues=priority_counts.get(Priority.INFO, 0),
                avg_confidence=avg_confidence,
                analysis_types=analysis_types,
                first_analyzed=min(timestamps),
                last_analyzed=max(timestamps),
            )

            file_summaries[file_path] = summary

        return file_summaries

    def generate_project_summary(self) -> ProjectAnalysisSummary:
        """Generate overall project summary."""
        if not self.results:
            return ProjectAnalysisSummary(
                project_path="",
                total_files_analyzed=0,
                total_issues=0,
                issues_by_priority={},
                issues_by_type={},
                files_with_issues=0,
                avg_confidence=0.0,
                top_problematic_files=[],
                analysis_duration=0.0,
            )

        # Count by priority and type
        priority_counts = Counter(result.priority for result in self.results)
        type_counts = Counter(result.analysis_type for result in self.results)

        # Calculate statistics
        unique_files = set(result.file_path for result in self.results)
        confidences = [result.confidence for result in self.results]
        avg_confidence = sum(confidences) / len(confidences)

        # Top problematic files
        file_issue_counts = Counter(result.file_path for result in self.results)
        top_files = file_issue_counts.most_common(10)

        # Determine project path
        if unique_files:
            # Find common prefix
            project_path = str(Path.cwd())
        else:
            project_path = ""

        return ProjectAnalysisSummary(
            project_path=project_path,
            total_files_analyzed=len(unique_files),
            total_issues=len(self.results),
            issues_by_priority=dict(priority_counts),
            issues_by_type=dict(type_counts),
            files_with_issues=len(unique_files),
            avg_confidence=avg_confidence,
            top_problematic_files=top_files,
            analysis_duration=0.0,  # Would be calculated by timing the analysis
        )

    def get_filtered_results(
        self,
        priority: Optional[Priority] = None,
        analysis_type: Optional[AnalysisType] = None,
        file_path: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> List[AnalysisResult]:
        """Get filtered analysis results."""
        filtered = self.results

        if priority:
            filtered = [r for r in filtered if r.priority == priority]

        if analysis_type:
            filtered = [r for r in filtered if r.analysis_type == analysis_type]

        if file_path:
            filtered = [r for r in filtered if file_path in r.file_path]

        if min_confidence:
            filtered = [r for r in filtered if r.confidence >= min_confidence]

        return filtered

    def get_top_issues(self, limit: int = 10) -> List[AnalysisResult]:
        """Get top issues sorted by priority and confidence."""
        priority_order = {p: i for i, p in enumerate(Priority)}

        sorted_results = sorted(
            self.results, key=lambda r: (priority_order[r.priority], -r.confidence)
        )

        return sorted_results[:limit]

    def export_results(
        self, format: str = "json", output_path: Optional[str] = None
    ) -> str:
        """Export results in specified format."""
        if format.lower() == "json":
            return self._export_json(output_path)
        elif format.lower() == "csv":
            return self._export_csv(output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self, output_path: Optional[str]) -> str:
        """Export results as JSON."""
        data = {
            "project_summary": self._make_json_serializable(
                asdict(self.generate_project_summary())
            ),
            "file_summaries": {
                k: self._make_json_serializable(asdict(v))
                for k, v in self.generate_file_summaries().items()
            },
            "results": [
                self._make_json_serializable(result.to_dict())
                for result in self.results
            ],
            "correlations": self._make_json_serializable(
                self.correlator.correlate_results(self.results)
            ),
        }

        # Convert enums and other non-serializable objects
        json_data = json.dumps(data, default=str, indent=2)

        if output_path:
            Path(output_path).write_text(json_data)
            logger.info(f"Results exported to {output_path}")

        return json_data

    def _make_json_serializable(self, obj):
        """Recursively convert enum keys and values to strings for JSON serialization."""
        if isinstance(obj, dict):
            # Convert enum keys to strings and recursively process values
            return {
                str(k) if isinstance(k, Enum) else k: self._make_json_serializable(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, Enum):
            return str(obj)
        else:
            return obj

    def _export_csv(self, output_path: Optional[str]) -> str:
        """Export results as CSV."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "file_path",
                "line_start",
                "line_end",
                "title",
                "priority",
                "confidence",
                "analysis_type",
                "description",
                "recommendation",
            ],
        )

        writer.writeheader()
        for result in self.results:
            writer.writerow(
                {
                    "file_path": result.file_path,
                    "line_start": result.start_line,
                    "line_end": result.end_line,
                    "title": result.title,
                    "priority": result.priority.name,
                    "confidence": f"{result.confidence:.2f}",
                    "analysis_type": result.analysis_type.value,
                    "description": result.description,
                    "recommendation": result.recommendation,
                }
            )

        csv_data = output.getvalue()
        output.close()

        if output_path:
            Path(output_path).write_text(csv_data)
            logger.info(f"Results exported to {output_path}")

        return csv_data


class ComprehensiveAnalysisReport:
    """Generates comprehensive, actionable analysis reports."""

    def __init__(self, aggregator: AnalysisAggregator):
        self.aggregator = aggregator
        self.project_summary = aggregator.generate_project_summary()
        self.file_summaries = aggregator.generate_file_summaries()
        self.correlations = aggregator.correlator.correlate_results(aggregator.results)

    def generate_executive_summary(self) -> str:
        """Generate high-level executive summary."""
        summary = f"""
Code Quality Analysis - Executive Summary
========================================

Project Analysis Overview:
- Files Analyzed: {self.project_summary.total_files_analyzed}
- Total Issues Found: {self.project_summary.total_issues}
- Average Confidence: {self.project_summary.avg_confidence:.1%}

Issue Breakdown by Priority:
"""

        for priority, count in self.project_summary.issues_by_priority.items():
            summary += f"  {priority.name}: {count}\n"

        summary += """
Analysis Types Performed:
"""
        for analysis_type, count in self.project_summary.issues_by_type.items():
            summary += f"  {analysis_type.value.replace('_', ' ').title()}: {count}\n"

        # Top problematic files
        if self.project_summary.top_problematic_files:
            summary += "\nMost Problematic Files:\n"
            for file_path, count in self.project_summary.top_problematic_files[:5]:
                summary += f"  {file_path}: {count} issues\n"

        return summary

    def generate_detailed_report(self) -> str:
        """Generate detailed technical report."""
        report = self.generate_executive_summary()

        # Top critical issues
        critical_issues = self.aggregator.get_filtered_results(
            priority=Priority.CRITICAL
        )
        if critical_issues:
            report += f"\n\nCRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION ({len(critical_issues)}):\n"
            report += "=" * 60 + "\n"

            for i, issue in enumerate(critical_issues[:10], 1):
                report += f"\n{i}. {issue.title}\n"
                report += (
                    f"   File: {issue.file_path}:{issue.start_line}-{issue.end_line}\n"
                )
                report += f"   Confidence: {issue.confidence:.1%}\n"
                report += f"   Description: {issue.description}\n"
                report += f"   Recommendation: {issue.recommendation}\n"

        # Correlation insights
        if self.correlations:
            report += "\n\nCORRELATED ISSUES & INSIGHTS:\n"
            report += "=" * 40 + "\n"

            for correlation_name, correlated_results in list(self.correlations.items())[
                :5
            ]:
                report += f"\n{correlation_name}:\n"
                report += f"  Related Issues: {len(correlated_results)}\n"

                if "hotspot" in correlation_name:
                    report += "  This file appears to be a quality hotspot requiring refactoring.\n"
                elif "recurring_issue" in correlation_name:
                    report += "  This issue pattern appears across multiple files.\n"
                elif "multi_issue" in correlation_name:
                    report += "  This file has multiple types of quality issues.\n"

        return report

    def generate_action_plan(self) -> str:
        """Generate prioritized action plan."""
        plan = """
PRIORITIZED ACTION PLAN
=====================

Based on the analysis results, here's a recommended action plan:

"""

        # Critical actions
        critical_issues = self.aggregator.get_filtered_results(
            priority=Priority.CRITICAL
        )
        if critical_issues:
            plan += f"IMMEDIATE ACTIONS (Critical - {len(critical_issues)} issues):\n"
            plan += "1. Address all security vulnerabilities\n"
            plan += "2. Fix hardcoded secrets and credentials\n"
            plan += "3. Resolve dangerous code execution patterns\n\n"

        # High priority actions
        high_issues = self.aggregator.get_filtered_results(priority=Priority.HIGH)
        if high_issues:
            plan += f"SHORT-TERM ACTIONS (High Priority - {len(high_issues)} issues):\n"
            plan += "1. Refactor God classes and long methods\n"
            plan += "2. Address SQL injection risks\n"
            plan += "3. Remove exact code duplicates\n\n"

        # Medium priority actions
        medium_issues = self.aggregator.get_filtered_results(priority=Priority.MEDIUM)
        if medium_issues:
            plan += f"MEDIUM-TERM ACTIONS (Medium Priority - {len(medium_issues)} issues):\n"
            plan += "1. Improve code organization and structure\n"
            plan += "2. Reduce structural code duplication\n"
            plan += "3. Address code smells and anti-patterns\n\n"

        # File-specific recommendations
        if self.project_summary.top_problematic_files:
            plan += "FILE-SPECIFIC RECOMMENDATIONS:\n"
            for file_path, count in self.project_summary.top_problematic_files[:3]:
                plan += f"  {file_path} ({count} issues):\n"
                plan += "    - Consider comprehensive refactoring\n"
                plan += "    - Break into smaller, more focused modules\n"
                plan += "    - Add unit tests before refactoring\n\n"

        return plan


def main():
    """Example usage of the result aggregation system."""
    from .duplicate_detection import CompositeDuplicateDetector, CodeBlock
    from .pattern_classifier import CompositePatternClassifier

    # Sample data
    sample_code = """
def process_user_data(username, password, email, phone, address, city, state, zip_code):
    # This is a long parameter list
    admin_password = "admin123"  # Hardcoded secret

    query = f"SELECT * FROM users WHERE username = '{username}'"  # SQL injection
    cursor.execute(query)

    if user_type == "admin":
        admin_logic()
    elif user_type == "moderator":
        moderator_logic()
    elif user_type == "user":
        user_logic()
    elif user_type == "guest":
        guest_logic()
    elif user_type == "premium":
        premium_logic()

    return result
"""

    # Create sample analysis results
    aggregator = AnalysisAggregator()

    # Add duplicate detection results (simulated)
    sample_blocks = [
        CodeBlock(sample_code, "example1.py", 1, 20),
        CodeBlock(sample_code, "example2.py", 30, 49),  # Simulated duplicate
    ]

    duplicate_detector = CompositeDuplicateDetector()
    duplicate_matches = duplicate_detector.detect_all_duplicates(sample_blocks)
    aggregator.add_duplicate_analysis(duplicate_matches)

    # Add pattern classification results
    pattern_classifier = CompositePatternClassifier()
    pattern_matches = pattern_classifier.classify_patterns(sample_code, "example.py")
    aggregator.add_pattern_analysis(pattern_matches)

    # Generate comprehensive report
    report_generator = ComprehensiveAnalysisReport(aggregator)

    print("=== EXECUTIVE SUMMARY ===")
    print(report_generator.generate_executive_summary())

    print("\n=== ACTION PLAN ===")
    print(report_generator.generate_action_plan())

    # Export results
    aggregator.export_results("json")
    print(f"\nExported {len(aggregator.results)} results to JSON")


if __name__ == "__main__":
    main()
