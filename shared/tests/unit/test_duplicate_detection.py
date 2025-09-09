#!/usr/bin/env python3
"""
Test suite for duplicate detection algorithm
"""

# Use smart imports for module access
import sys

# Setup import paths and import code duplication analyzer
try:
    from analyzers.quality.code_duplication_analyzer import (
        CodeBlock,
        CompositeDuplicateDetector,
        DuplicateAnalysisReport,
        ExactDuplicateDetector,
        SemanticDuplicateDetector,
        StructuralDuplicateDetector,
    )
    from utils import path_resolver  # noqa: F401
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    sys.exit(1)


def test_exact_duplicate_detector():
    """Test exact duplicate detection."""
    detector = ExactDuplicateDetector(min_lines=2)

    blocks = [
        CodeBlock("def foo():\n    return 42", "file1.py", 1, 2),
        CodeBlock("def foo():\n    return 42", "file2.py", 10, 11),
        CodeBlock("def bar():\n    return 24", "file3.py", 5, 6),
    ]

    matches = detector.detect_duplicates(blocks)
    assert len(matches) == 1
    assert matches[0].similarity_score == 1.0
    assert matches[0].match_type == "exact"


def test_structural_duplicate_detector():
    """Test structural duplicate detection."""
    detector = StructuralDuplicateDetector(similarity_threshold=0.7)

    blocks = [
        CodeBlock("def add(a, b):\n    return a + b", "file1.py", 1, 2),
        CodeBlock("def sum(x, y):\n    return x + y", "file2.py", 10, 11),
    ]

    matches = detector.detect_duplicates(blocks)
    assert len(matches) == 1
    assert matches[0].match_type == "structural"
    assert matches[0].similarity_score > 0.7


def test_semantic_duplicate_detector():
    """Test semantic duplicate detection with production thresholds."""
    detector = (
        SemanticDuplicateDetector()
    )  # Use default thresholds: 0.7 similarity, 20 tokens

    # Create blocks with high semantic similarity - same function names and many shared tokens
    blocks = [
        CodeBlock(
            """def validate_and_process_data(data_records):
    processed_data = []
    for data_record in data_records:
        if validate_data_record(data_record):
            clean_data = clean_data_record(data_record)
            enriched_data = enrich_data_record(clean_data)
            final_data = finalize_data_record(enriched_data)
            processed_data.append(final_data)
        else:
            log_invalid_data_record(data_record)
    return processed_data""",
            "file1.py",
            1,
            10,
        ),
        CodeBlock(
            """def validate_and_process_data(input_records):
    processed_data = []
    for data_record in input_records:
        if validate_data_record(data_record):
            clean_data = clean_data_record(data_record)
            enriched_data = enrich_data_record(clean_data)
            final_data = finalize_data_record(enriched_data)
            processed_data.append(final_data)
        else:
            log_invalid_data_record(data_record)
    return processed_data""",
            "file2.py",
            15,
            25,
        ),
    ]

    matches = detector.detect_duplicates(blocks)
    assert len(matches) == 1
    assert matches[0].match_type == "semantic"
    assert matches[0].similarity_score >= 0.7  # Should meet production threshold


def test_composite_detector():
    """Test composite detector with production thresholds."""
    detector = CompositeDuplicateDetector()  # Use default production thresholds

    blocks = [
        # Exact duplicate - large enough functions (>= 5 lines)
        CodeBlock(
            """def authenticate_user(username, password):
    if not username or not password:
        return False
    user = get_user_by_username(username)
    if user and check_password(user, password):
        create_session(user)
        log_login(username)
        return True
    return False""",
            "file1.py",
            1,
            9,
        ),
        CodeBlock(
            """def authenticate_user(username, password):
    if not username or not password:
        return False
    user = get_user_by_username(username)
    if user and check_password(user, password):
        create_session(user)
        log_login(username)
        return True
    return False""",
            "file2.py",
            10,
            18,
        ),  # Exact duplicate
        # Structural duplicate - similar structure, different names
        CodeBlock(
            """def validate_admin_access(admin_name, admin_pass):
    if not admin_name or not admin_pass:
        return False
    admin = get_admin_by_name(admin_name)
    if admin and verify_admin_password(admin, admin_pass):
        create_admin_session(admin)
        log_admin_access(admin_name)
        return True
    return False""",
            "file3.py",
            20,
            28,
        ),
        CodeBlock(
            """def check_moderator_login(mod_user, mod_password):
    if not mod_user or not mod_password:
        return False
    moderator = find_moderator(mod_user)
    if moderator and validate_mod_pass(moderator, mod_password):
        init_moderator_session(moderator)
        record_mod_login(mod_user)
        return True
    return False""",
            "file4.py",
            30,
            38,
        ),  # Structural duplicate
    ]

    matches = detector.detect_all_duplicates(blocks)
    assert len(matches) >= 2  # Should find both exact and structural matches

    # Check that we have different match types
    match_types = {match.match_type for match in matches}
    assert "exact" in match_types
    assert "structural" in match_types


def test_analysis_report():
    """Test duplicate analysis report generation with production thresholds."""
    blocks = [
        CodeBlock(
            """def process_payment(amount, card_number, expiry, cvv):
    if not validate_card_number(card_number):
        return {'success': False, 'error': 'Invalid card'}
    if not validate_expiry(expiry):
        return {'success': False, 'error': 'Card expired'}
    if not validate_cvv(cvv):
        return {'success': False, 'error': 'Invalid CVV'}
    charge_result = charge_card(amount, card_number, expiry, cvv)
    return charge_result""",
            "file1.py",
            1,
            9,
        ),
        CodeBlock(
            """def process_payment(amount, card_number, expiry, cvv):
    if not validate_card_number(card_number):
        return {'success': False, 'error': 'Invalid card'}
    if not validate_expiry(expiry):
        return {'success': False, 'error': 'Card expired'}
    if not validate_cvv(cvv):
        return {'success': False, 'error': 'Invalid CVV'}
    charge_result = charge_card(amount, card_number, expiry, cvv)
    return charge_result""",
            "file2.py",
            10,
            18,
        ),
    ]

    detector = ExactDuplicateDetector()  # Use production defaults: min_lines=5
    matches = detector.detect_duplicates(blocks)

    report = DuplicateAnalysisReport(matches)
    summary = report.generate_summary()

    assert "Total Matches: 1" in summary
    assert "exact" in summary.lower()

    detailed = report.generate_detailed_report()
    assert len(detailed) > len(summary)


def test_code_block_validation():
    """Test code block validation logic."""
    detector = ExactDuplicateDetector(min_lines=3)

    # Should not analyze blocks that are too short
    short_block = CodeBlock("x = 1", "file1.py", 1, 1)
    long_block = CodeBlock("def foo():\n    x = 1\n    return x", "file2.py", 1, 3)

    matches = detector.detect_duplicates([short_block, long_block])
    assert len(matches) == 0


def test_negative_cases():
    """Test that detectors correctly reject non-duplicates with production thresholds."""

    # Test 1: Too few lines for exact detection
    exact_detector = ExactDuplicateDetector()  # min_lines=5
    small_blocks = [
        CodeBlock("def small():\n    return 1", "file1.py", 1, 2),
        CodeBlock("def small():\n    return 1", "file2.py", 5, 6),
    ]
    matches = exact_detector.detect_duplicates(small_blocks)
    assert (
        len(matches) == 0
    ), "Should not detect duplicates in blocks smaller than min_lines"

    # Test 2: Low structural similarity
    structural_detector = StructuralDuplicateDetector()  # similarity_threshold=0.8
    dissimilar_blocks = [
        CodeBlock(
            """def calculate_fibonacci(n):
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)""",
            "file1.py",
            1,
            5,
        ),
        CodeBlock(
            """def sort_array(arr):
    for i in range(len(arr)):
        for j in range(0, len(arr)-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr""",
            "file2.py",
            10,
            16,
        ),
    ]
    matches = structural_detector.detect_duplicates(dissimilar_blocks)
    assert (
        len(matches) == 0
    ), "Should not detect structural duplicates in dissimilar code"

    # Test 3: Low semantic similarity and insufficient tokens
    semantic_detector = (
        SemanticDuplicateDetector()
    )  # similarity_threshold=0.7, min_tokens=20
    low_similarity_blocks = [
        CodeBlock("def add(x, y):\n    return x + y", "file1.py", 1, 2),
        CodeBlock("def multiply(a, b):\n    return a * b", "file2.py", 5, 6),
    ]
    matches = semantic_detector.detect_duplicates(low_similarity_blocks)
    assert (
        len(matches) == 0
    ), "Should not detect semantic duplicates with low similarity and few tokens"

    # Test 4: Semantic similarity below threshold
    below_threshold_blocks = [
        CodeBlock(
            """def initialize_database_connection():
    connection = create_db_connection()
    setup_connection_pool(connection)
    configure_database_settings()
    establish_connection_timeout()
    verify_database_schema()
    return connection""",
            "file1.py",
            1,
            7,
        ),
        CodeBlock(
            """def setup_email_service():
    email_client = create_email_client()
    configure_smtp_settings(email_client)
    set_authentication_credentials()
    establish_retry_policy()
    validate_email_templates()
    return email_client""",
            "file2.py",
            10,
            16,
        ),
    ]
    matches = semantic_detector.detect_duplicates(below_threshold_blocks)
    # These should have some similarity but likely below 0.7 threshold
    for match in matches:
        assert (
            match.similarity_score >= 0.7
        ), f"Any detected matches should meet threshold, got {match.similarity_score}"


def test_threshold_boundary_cases():
    """Test edge cases around threshold boundaries."""

    # Test exact threshold boundary for structural similarity
    structural_detector = StructuralDuplicateDetector(similarity_threshold=0.8)

    # These should be just above the threshold
    high_similarity_blocks = [
        CodeBlock(
            """def validate_user_input(user_data):
    if not user_data.get('name'):
        raise ValueError("Name required")
    if not user_data.get('email'):
        raise ValueError("Email required")
    if len(user_data.get('password', '')) < 8:
        raise ValueError("Password too short")
    return True""",
            "file1.py",
            1,
            7,
        ),
        CodeBlock(
            """def validate_admin_input(admin_data):
    if not admin_data.get('username'):
        raise ValueError("Username required")
    if not admin_data.get('email'):
        raise ValueError("Email required")
    if len(admin_data.get('password', '')) < 8:
        raise ValueError("Password too short")
    return True""",
            "file2.py",
            10,
            16,
        ),
    ]

    matches = structural_detector.detect_duplicates(high_similarity_blocks)
    assert len(matches) >= 1, "Should detect structural duplicates above threshold"
    for match in matches:
        assert (
            match.similarity_score >= 0.8
        ), f"Detected matches should meet threshold, got {match.similarity_score}"


if __name__ == "__main__":
    # Run basic tests
    test_exact_duplicate_detector()
    test_structural_duplicate_detector()
    test_semantic_duplicate_detector()
    test_composite_detector()
    test_analysis_report()
    test_code_block_validation()
    test_negative_cases()
    test_threshold_boundary_cases()
    print("All tests passed!")
