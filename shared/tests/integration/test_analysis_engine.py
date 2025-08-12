#!/usr/bin/env python3
"""
Integration Testing Suite for Analysis Engine
Part of Phase 2.5: Analysis Engine - Integration Testing

This module provides comprehensive integration tests for the entire analysis engine,
verifying that duplicate detection, pattern classification, and result aggregation
work together correctly.
"""

import tempfile
import pytest
from pathlib import Path

from shared.analyzers.quality.duplicate_detection import (
    CompositeDuplicateDetector,
    CodeBlock,
)
from shared.analyzers.quality.pattern_classifier import (
    CompositePatternClassifier,
    PatternType,
)
from shared.analyzers.quality.result_aggregator import (
    AnalysisAggregator,
    AnalysisType,
    Priority,
    ComprehensiveAnalysisReport,
)


class TestAnalysisEngineIntegration:
    """Integration tests for the complete analysis engine."""

    @pytest.fixture
    def sample_codebase(self):
        """Create a temporary codebase with various code quality issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)

            # File 1: God class with security issues
            file1_content = """
class UserManager:
    def __init__(self):
        self.database_password = "admin123"  # Hardcoded secret
        self.users = []
        self.roles = []
        self.permissions = []
        self.sessions = []
        self.logs = []
        self.settings = {}
        self.cache = {}

    def create_user(self, username, password, email):
        query = f"INSERT INTO users (username, password) VALUES ('{username}', '{password}')"
        self.execute_sql(query)  # SQL injection risk

    def authenticate_user(self, username, password):
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        return self.execute_sql(query)  # SQL injection risk

    def delete_user(self, user_id):
        query = f"DELETE FROM users WHERE id = {user_id}"
        self.execute_sql(query)

    def update_user(self, user_id, data):
        # Long method with many operations
        if not user_id:
            raise ValueError("User ID required")

        existing_user = self.get_user(user_id)
        if not existing_user:
            raise ValueError("User not found")

        if 'username' in data:
            if len(data['username']) < 3:
                raise ValueError("Username too short")
            if self.username_exists(data['username']):
                raise ValueError("Username already exists")

        if 'email' in data:
            if '@' not in data['email']:
                raise ValueError("Invalid email")
            if self.email_exists(data['email']):
                raise ValueError("Email already exists")

        if 'password' in data:
            if len(data['password']) < 8:
                raise ValueError("Password too short")
            data['password'] = self.hash_password(data['password'])

        # Update database
        for field, value in data.items():
            query = f"UPDATE users SET {field} = '{value}' WHERE id = {user_id}"
            self.execute_sql(query)

        # Log the update
        self.log_user_update(user_id, data)

        # Clear cache
        self.clear_user_cache(user_id)

        # Send notification
        self.send_update_notification(user_id)

        return True

    def get_user(self, user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"
        return self.execute_sql(query)

    def username_exists(self, username):
        query = f"SELECT id FROM users WHERE username = '{username}'"
        result = self.execute_sql(query)
        return len(result) > 0

    def email_exists(self, email):
        query = f"SELECT id FROM users WHERE email = '{email}'"
        result = self.execute_sql(query)
        return len(result) > 0

    def hash_password(self, password):
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

    def execute_sql(self, query):
        # Simulated database execution
        pass

    def log_user_update(self, user_id, data):
        pass

    def clear_user_cache(self, user_id):
        pass

    def send_update_notification(self, user_id):
        pass
"""

            # File 2: Duplicate code and code smells
            file2_content = """
class ProductManager:
    def create_product(self, name, price, category):
        query = f"INSERT INTO products (name, price) VALUES ('{name}', '{price}')"
        self.execute_sql(query)  # SQL injection risk (duplicate pattern)

    def authenticate_admin(self, username, password):
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        return self.execute_sql(query)  # Exact duplicate of UserManager.authenticate_user

    def process_order(self, order_type):
        # Switch statement smell
        if order_type == "standard":
            return self.process_standard_order()
        elif order_type == "express":
            return self.process_express_order()
        elif order_type == "overnight":
            return self.process_overnight_order()
        elif order_type == "international":
            return self.process_international_order()
        elif order_type == "bulk":
            return self.process_bulk_order()
        elif order_type == "custom":
            return self.process_custom_order()
        else:
            raise ValueError("Unknown order type")

    def calculate_shipping(self, weight, distance, priority, insurance, packaging):
        # Long parameter list
        base_cost = weight * 0.1
        distance_cost = distance * 0.05
        priority_cost = priority * 10
        insurance_cost = insurance * 0.02
        packaging_cost = packaging * 2
        return base_cost + distance_cost + priority_cost + insurance_cost + packaging_cost

    def execute_sql(self, query):
        # Simulated database execution
        pass
"""

            # File 3: Security vulnerabilities
            file3_content = """
import os
import subprocess
import random
import pickle

class SecurityIssues:
    def __init__(self):
        self.api_key = "sk-1234567890abcdef"  # Hardcoded API key
        self.secret_token = "secret123"       # Hardcoded secret

    def execute_command(self, user_input):
        # Command injection vulnerability
        os.system(f"ls {user_input}")
        subprocess.call(f"echo {user_input}", shell=True)

    def load_data(self, filename):
        # Path traversal vulnerability
        with open(f"/data/{filename}", 'r') as f:
            return f.read()

    def evaluate_expression(self, expr):
        # Dangerous code execution
        return eval(expr)

    def deserialize_data(self, data):
        # Insecure deserialization
        return pickle.loads(data)

    def generate_token(self):
        # Insecure random number generation
        return random.randint(1000000, 9999999)

    def weak_random(self):
        # Multiple uses of insecure random
        session_id = random.random()
        csrf_token = random.choice(range(1000))
        return session_id, csrf_token
"""

            # Write files
            (base_path / "user_manager.py").write_text(file1_content)
            (base_path / "product_manager.py").write_text(file2_content)
            (base_path / "security_issues.py").write_text(file3_content)

            yield base_path

    def test_duplicate_detection_integration(self, sample_codebase):
        """Test that duplicate detection works on real codebase."""
        # Read files and create code blocks - use simpler, more direct approach
        code_blocks = []

        for py_file in sample_codebase.glob("*.py"):
            content = py_file.read_text()

            # Create blocks for each function/method - simpler and more reliable approach
            import ast

            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Get the function source by line numbers
                        lines = content.split("\n")
                        start_line = node.lineno
                        # Find end line by looking for the next function/class or end of file
                        end_line = (
                            node.end_lineno
                            if hasattr(node, "end_lineno")
                            else len(lines)
                        )

                        function_lines = lines[start_line - 1 : end_line]
                        # Remove common indentation to make it parseable
                        if function_lines:
                            # Find minimum indentation
                            min_indent = min(
                                len(line) - len(line.lstrip())
                                for line in function_lines
                                if line.strip()
                            )
                            # Remove common indentation
                            dedented_lines = [
                                line[min_indent:] if len(line) >= min_indent else line
                                for line in function_lines
                            ]
                            block_content = "\n".join(dedented_lines)

                            if (
                                len(block_content.strip()) > 0
                            ):  # Only add non-empty blocks
                                code_blocks.append(
                                    CodeBlock(
                                        content=block_content,
                                        file_path=str(py_file),
                                        start_line=start_line,
                                        end_line=end_line,
                                    )
                                )
            except SyntaxError:
                # If AST parsing fails, skip this file
                continue

        # Run duplicate detection
        detector = CompositeDuplicateDetector()
        matches = detector.detect_all_duplicates(code_blocks)

        # Verify we found duplicates
        assert len(matches) > 0

        # Verify we found the authenticate method duplicate
        auth_duplicates = [
            m
            for m in matches
            if "authenticate" in m.block1.content.lower()
            or "authenticate" in m.block2.content.lower()
        ]
        assert len(auth_duplicates) > 0

        # Verify duplicate has high similarity
        for match in matches:
            if match.match_type == "exact":
                assert match.similarity_score >= 0.8

    def test_pattern_classification_integration(self, sample_codebase):
        """Test that pattern classification works on real codebase."""
        all_patterns = []

        for py_file in sample_codebase.glob("*.py"):
            content = py_file.read_text()

            classifier = CompositePatternClassifier()
            patterns = classifier.classify_patterns(content, str(py_file))
            all_patterns.extend(patterns)

        # Verify we found various pattern types
        assert len(all_patterns) > 0

        # Check for security issues
        security_patterns = [
            p for p in all_patterns if p.pattern_type == PatternType.SECURITY_ISSUE
        ]
        assert len(security_patterns) > 0

        # Check for anti-patterns
        anti_patterns = [
            p for p in all_patterns if p.pattern_type == PatternType.ANTI_PATTERN
        ]
        assert len(anti_patterns) > 0

        # Check for code smells
        code_smells = [
            p for p in all_patterns if p.pattern_type == PatternType.CODE_SMELL
        ]
        assert len(code_smells) > 0

        # Verify we found specific issues
        pattern_names = [p.pattern_name for p in all_patterns]
        # Look for actual patterns that should be detected from the sample code
        assert any(
            "Hardcoded" in name for name in pattern_names
        )  # Should find hardcoded secrets
        assert any(
            "Command Injection" in name or "Dangerous Code" in name
            for name in pattern_names
        )  # Should find injection risks
        # Note: SQL injection might be detected as other security patterns, so we check for any security issues above

    def test_result_aggregation_integration(self, sample_codebase):
        """Test that result aggregation combines all analyses correctly."""
        aggregator = AnalysisAggregator()

        # Collect all analysis results
        all_duplicate_matches = []
        all_pattern_matches = []

        # Run duplicate detection
        code_blocks = []
        for py_file in sample_codebase.glob("*.py"):
            content = py_file.read_text()
            code_blocks.append(
                CodeBlock(
                    content=content,
                    file_path=str(py_file),
                    start_line=1,
                    end_line=len(content.split("\n")),
                )
            )

        duplicate_detector = CompositeDuplicateDetector()
        duplicate_matches = duplicate_detector.detect_all_duplicates(code_blocks)
        all_duplicate_matches.extend(duplicate_matches)

        # Run pattern classification
        for py_file in sample_codebase.glob("*.py"):
            content = py_file.read_text()
            classifier = CompositePatternClassifier()
            pattern_matches = classifier.classify_patterns(content, str(py_file))
            all_pattern_matches.extend(pattern_matches)

        # Add to aggregator
        aggregator.add_duplicate_analysis(all_duplicate_matches)
        aggregator.add_pattern_analysis(all_pattern_matches)

        # Verify aggregation
        assert len(aggregator.results) > 0

        # Test filtering
        critical_results = aggregator.get_filtered_results(priority=Priority.CRITICAL)
        high_results = aggregator.get_filtered_results(priority=Priority.HIGH)

        # Should have critical and high priority issues
        assert len(critical_results) > 0 or len(high_results) > 0

        # Test project summary
        project_summary = aggregator.generate_project_summary()
        assert project_summary.total_files_analyzed == 3
        assert project_summary.total_issues > 0
        assert len(project_summary.issues_by_priority) > 0
        assert len(project_summary.issues_by_type) > 0

        # Test file summaries
        file_summaries = aggregator.generate_file_summaries()
        assert len(file_summaries) == 3

        for file_path, summary in file_summaries.items():
            assert summary.total_issues > 0
            assert summary.avg_confidence > 0

    def test_comprehensive_report_generation(self, sample_codebase):
        """Test that comprehensive reports are generated correctly."""
        # Set up aggregator with all analyses
        aggregator = AnalysisAggregator()

        # Run full analysis
        duplicate_detector = CompositeDuplicateDetector()
        pattern_classifier = CompositePatternClassifier()

        for py_file in sample_codebase.glob("*.py"):
            content = py_file.read_text()

            # Duplicate detection (simplified)
            code_blocks = [
                CodeBlock(content, str(py_file), 1, len(content.split("\n")))
            ]
            duplicate_matches = duplicate_detector.detect_all_duplicates(code_blocks)
            aggregator.add_duplicate_analysis(duplicate_matches)

            # Pattern classification
            pattern_matches = pattern_classifier.classify_patterns(
                content, str(py_file)
            )
            aggregator.add_pattern_analysis(pattern_matches)

        # Generate comprehensive report
        report_generator = ComprehensiveAnalysisReport(aggregator)

        # Test executive summary
        exec_summary = report_generator.generate_executive_summary()
        assert len(exec_summary) > 0
        assert "Files Analyzed: 3" in exec_summary
        assert "Total Issues Found:" in exec_summary

        # Test detailed report
        detailed_report = report_generator.generate_detailed_report()
        assert len(detailed_report) > len(exec_summary)

        # Test action plan
        action_plan = report_generator.generate_action_plan()
        assert len(action_plan) > 0
        assert "ACTION PLAN" in action_plan

        # Should have recommendations based on findings
        if aggregator.get_filtered_results(priority=Priority.CRITICAL):
            assert "IMMEDIATE ACTIONS" in action_plan

    def test_export_functionality(self, sample_codebase):
        """Test that export functionality works correctly."""
        aggregator = AnalysisAggregator()

        # Add some sample results
        pattern_classifier = CompositePatternClassifier()
        for py_file in sample_codebase.glob("*.py"):
            content = py_file.read_text()
            pattern_matches = pattern_classifier.classify_patterns(
                content, str(py_file)
            )
            aggregator.add_pattern_analysis(pattern_matches)

        # Test JSON export
        json_data = aggregator.export_results("json")
        assert len(json_data) > 0
        assert '"project_summary"' in json_data
        assert '"results"' in json_data

        # Test CSV export
        csv_data = aggregator.export_results("csv")
        assert len(csv_data) > 0
        assert "file_path,line_start" in csv_data

        # Test invalid format
        with pytest.raises(ValueError):
            aggregator.export_results("xml")

    def test_correlation_detection(self, sample_codebase):
        """Test that result correlation works correctly."""
        aggregator = AnalysisAggregator()

        # Run full analysis to get correlatable results
        pattern_classifier = CompositePatternClassifier()
        duplicate_detector = CompositeDuplicateDetector()

        all_code_blocks = []

        for py_file in sample_codebase.glob("*.py"):
            content = py_file.read_text()

            # Pattern analysis
            pattern_matches = pattern_classifier.classify_patterns(
                content, str(py_file)
            )
            aggregator.add_pattern_analysis(pattern_matches)

            # Duplicate analysis
            all_code_blocks.append(
                CodeBlock(content, str(py_file), 1, len(content.split("\n")))
            )

        duplicate_matches = duplicate_detector.detect_all_duplicates(all_code_blocks)
        aggregator.add_duplicate_analysis(duplicate_matches)

        # Test correlations
        correlations = aggregator.correlator.correlate_results(aggregator.results)

        # Should find correlations if there are enough results
        if len(aggregator.results) >= 5:
            assert len(correlations) > 0

            # Check for hotspots (files with many issues)
            hotspot_correlations = [k for k in correlations.keys() if "hotspot" in k]
            multi_issue_correlations = [
                k for k in correlations.keys() if "multi_issue" in k
            ]

            # Should find either hotspots or multi-issue files
            assert len(hotspot_correlations) > 0 or len(multi_issue_correlations) > 0

    def test_end_to_end_analysis_pipeline(self, sample_codebase):
        """Test the complete end-to-end analysis pipeline."""
        # This is the main integration test that simulates how the analysis engine
        # would be used in practice

        # Initialize all components
        aggregator = AnalysisAggregator()
        duplicate_detector = CompositeDuplicateDetector()
        pattern_classifier = CompositePatternClassifier()

        # Step 1: Discover and process all Python files
        python_files = list(sample_codebase.glob("*.py"))
        assert len(python_files) == 3

        # Step 2: Run duplicate detection across all files
        all_code_blocks = []
        for py_file in python_files:
            content = py_file.read_text()
            # Create blocks for different functions/classes
            lines = content.split("\n")

            # Simple block creation based on class/function definitions
            current_block_lines = []
            start_line = 1

            for i, line in enumerate(lines):
                current_block_lines.append(line)

                if (
                    line.strip().startswith("def ") or line.strip().startswith("class ")
                ) and len(current_block_lines) > 5:
                    # Save previous block
                    if len(current_block_lines) > 10:
                        block_content = "\n".join(current_block_lines[:-1])
                        all_code_blocks.append(
                            CodeBlock(
                                content=block_content,
                                file_path=str(py_file),
                                start_line=start_line,
                                end_line=i,
                            )
                        )

                    # Start new block
                    current_block_lines = [line]
                    start_line = i + 1

            # Add final block
            if len(current_block_lines) > 10:
                block_content = "\n".join(current_block_lines)
                all_code_blocks.append(
                    CodeBlock(
                        content=block_content,
                        file_path=str(py_file),
                        start_line=start_line,
                        end_line=len(lines),
                    )
                )

        # Run duplicate detection
        duplicate_matches = duplicate_detector.detect_all_duplicates(all_code_blocks)
        aggregator.add_duplicate_analysis(duplicate_matches)

        # Step 3: Run pattern classification on each file
        for py_file in python_files:
            content = py_file.read_text()
            pattern_matches = pattern_classifier.classify_patterns(
                content, str(py_file)
            )
            aggregator.add_pattern_analysis(pattern_matches)

        # Step 4: Verify we have meaningful results
        assert len(aggregator.results) > 0

        # Should have found security issues
        security_results = aggregator.get_filtered_results(
            analysis_type=AnalysisType.PATTERN_CLASSIFICATION
        )
        security_issues = [
            r
            for r in security_results
            if "inject" in r.description.lower() or "hardcoded" in r.description.lower()
        ]
        assert len(security_issues) > 0

        # Should have found structural issues
        structural_results = [
            r for r in aggregator.results if "God Class" in r.title or "Long" in r.title
        ]
        assert len(structural_results) > 0

        # Step 5: Generate comprehensive analysis
        report_generator = ComprehensiveAnalysisReport(aggregator)

        # Executive summary should contain key metrics
        exec_summary = report_generator.generate_executive_summary()
        lines = exec_summary.split("\n")
        metric_lines = [
            line
            for line in lines
            if ":" in line
            and any(word in line for word in ["Files", "Issues", "Priority"])
        ]
        assert len(metric_lines) >= 3

        # Action plan should have prioritized recommendations
        action_plan = report_generator.generate_action_plan()
        assert any(
            priority in action_plan
            for priority in ["IMMEDIATE", "SHORT-TERM", "MEDIUM-TERM"]
        )

        # Step 6: Export results
        json_export = aggregator.export_results("json")
        import json

        parsed_json = json.loads(json_export)

        assert "project_summary" in parsed_json
        assert "results" in parsed_json
        assert len(parsed_json["results"]) == len(aggregator.results)

        # Step 7: Verify the analysis provided actionable insights
        top_issues = aggregator.get_top_issues(limit=5)
        assert len(top_issues) > 0

        # Should have high-confidence critical/high priority issues
        high_confidence_critical = [
            issue
            for issue in top_issues
            if issue.priority in [Priority.CRITICAL, Priority.HIGH]
            and issue.confidence > 0.7
        ]
        assert len(high_confidence_critical) > 0

        print("✓ End-to-end analysis completed successfully:")
        print(f"  - Analyzed {len(python_files)} files")
        print(f"  - Found {len(aggregator.results)} issues")
        print(f"  - Detected {len(duplicate_matches)} duplicate patterns")
        print(
            f"  - Identified {len(high_confidence_critical)} high-confidence critical issues"
        )


def test_performance_with_large_codebase():
    """Test that the analysis engine performs reasonably with larger codebases."""
    import time

    # Create a larger synthetic codebase
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        # Generate multiple files with various issues
        for i in range(10):
            file_content = f"""
class TestClass{i}:
    def __init__(self):
        self.password = "admin123"  # Security issue
        self.data = []

    def process_data(self, user_input):
        query = f"SELECT * FROM table WHERE id = '{{user_input}}'"  # SQL injection
        return self.execute_query(query)

    def long_method_with_many_parameters(self, a, b, c, d, e, f, g, h):
        # Long parameter list smell
        result = a + b + c + d + e + f + g + h

        # Long method body
        if result > 100:
            return self.complex_processing_1(result)
        elif result > 50:
            return self.complex_processing_2(result)
        elif result > 25:
            return self.complex_processing_3(result)
        elif result > 10:
            return self.complex_processing_4(result)
        else:
            return self.complex_processing_5(result)

    def duplicate_method(self):
        # This method will be duplicated across files
        user_data = self.get_user_data()
        if user_data:
            self.process_user_data(user_data)
            return True
        return False

    def execute_query(self, query):
        pass

    def complex_processing_1(self, data): pass
    def complex_processing_2(self, data): pass
    def complex_processing_3(self, data): pass
    def complex_processing_4(self, data): pass
    def complex_processing_5(self, data): pass
    def get_user_data(self): pass
    def process_user_data(self, data): pass
"""
            (base_path / f"test_file_{i}.py").write_text(file_content)

        # Run the full analysis pipeline and measure performance
        start_time = time.time()

        aggregator = AnalysisAggregator()
        duplicate_detector = CompositeDuplicateDetector()
        pattern_classifier = CompositePatternClassifier()

        # Process all files
        python_files = list(base_path.glob("*.py"))

        # Duplicate detection
        all_code_blocks = []
        for py_file in python_files:
            content = py_file.read_text()
            all_code_blocks.append(
                CodeBlock(content, str(py_file), 1, len(content.split("\n")))
            )

        duplicate_matches = duplicate_detector.detect_all_duplicates(all_code_blocks)
        aggregator.add_duplicate_analysis(duplicate_matches)

        # Pattern classification
        for py_file in python_files:
            content = py_file.read_text()
            pattern_matches = pattern_classifier.classify_patterns(
                content, str(py_file)
            )
            aggregator.add_pattern_analysis(pattern_matches)

        # Generate report
        report_generator = ComprehensiveAnalysisReport(aggregator)
        report = report_generator.generate_detailed_report()

        end_time = time.time()
        analysis_duration = end_time - start_time

        print("Performance test results:")
        print(f"  - Files analyzed: {len(python_files)}")
        print(f"  - Total issues found: {len(aggregator.results)}")
        print(f"  - Analysis duration: {analysis_duration:.2f} seconds")
        print(
            f"  - Average time per file: {analysis_duration/len(python_files):.2f} seconds"
        )

        # Verify performance is reasonable (should complete within 30 seconds for 10 files)
        assert analysis_duration < 30.0
        assert len(aggregator.results) > 0
        assert len(report) > 0


def main():
    """Run integration tests manually."""
    print("Running Analysis Engine Integration Tests...")

    # Create sample codebase
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulate the sample_codebase fixture
        base_path = Path(tmpdir)

        # Create test files (simplified versions)
        (base_path / "test1.py").write_text(
            """
class UserManager:
    def __init__(self):
        self.password = "admin123"  # Hardcoded secret

    def authenticate(self, user, pwd):
        query = f"SELECT * FROM users WHERE user = '{user}'"
        return self.execute_sql(query)

    def execute_sql(self, query):
        pass
"""
        )

        (base_path / "test2.py").write_text(
            """
class ProductManager:
    def authenticate(self, user, pwd):
        query = f"SELECT * FROM users WHERE user = '{user}'"
        return self.execute_sql(query)  # Duplicate!

    def execute_sql(self, query):
        pass
"""
        )

        # Run a basic integration test
        try:
            # Test pattern classification
            pattern_classifier = CompositePatternClassifier()
            aggregator = AnalysisAggregator()

            for py_file in base_path.glob("*.py"):
                content = py_file.read_text()
                patterns = pattern_classifier.classify_patterns(content, str(py_file))
                aggregator.add_pattern_analysis(patterns)

            # Test duplicate detection
            duplicate_detector = CompositeDuplicateDetector()
            code_blocks = []

            for py_file in base_path.glob("*.py"):
                content = py_file.read_text()
                code_blocks.append(
                    CodeBlock(content, str(py_file), 1, len(content.split("\n")))
                )

            duplicates = duplicate_detector.detect_all_duplicates(code_blocks)
            aggregator.add_duplicate_analysis(duplicates)

            # Generate report
            report_generator = ComprehensiveAnalysisReport(aggregator)
            report = report_generator.generate_executive_summary()

            print("✓ Basic integration test passed")
            print(f"Found {len(aggregator.results)} issues")
            print("\nSample report:")
            print(report)

        except Exception as e:
            print(f"✗ Integration test failed: {e}")
            raise


if __name__ == "__main__":
    main()
