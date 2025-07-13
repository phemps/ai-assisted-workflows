#!/bin/bash
# Test script to verify all migrated scripts work with new argparse + --output-format

echo "=== Testing Script Migrations ==="
echo "Testing all scripts that were migrated to use argparse and --output-format"
echo

# Test target directory
TEST_TARGET="test_codebase"
SCRIPT_BASE="claude/scripts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

test_script() {
    local script_path="$1"
    local script_name="$2"
    local description="$3"
    
    echo -e "${YELLOW}Testing: $script_name${NC}"
    echo "Description: $description"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Test 1: Help flag
    echo -n "  Help flag (--help): "
    if python "$script_path" --help >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Test 2: JSON output format (default)
    echo -n "  JSON output (default): "
    if python "$script_path" "$TEST_TARGET" --output-format json 2>/dev/null | head -5 | grep -q '"analysis_type"'; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Test 3: Console output format
    echo -n "  Console output format: "
    if python "$script_path" "$TEST_TARGET" --output-format console 2>/dev/null | head -5 | grep -q "ANALYSIS"; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${RED}FAIL${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Test 4: Summary mode (if supported)
    if python "$script_path" --help 2>&1 | grep -q "\-\-summary"; then
        echo -n "  Summary mode: "
        if python "$script_path" "$TEST_TARGET" --summary 2>/dev/null | head -5 | grep -q '"analysis_type"'; then
            echo -e "${GREEN}PASS${NC}"
        else
            echo -e "${RED}FAIL${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    fi
    
    # Test 5: Min severity (if supported)
    if python "$script_path" --help 2>&1 | grep -q "\-\-min-severity"; then
        echo -n "  Min severity high: "
        if python "$script_path" "$TEST_TARGET" --min-severity high 2>/dev/null | head -5 | grep -q '"analysis_type"'; then
            echo -e "${GREEN}PASS${NC}"
        else
            echo -e "${RED}FAIL${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    fi
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "  ${GREEN}✓ All tests passed for $script_name${NC}"
    echo
}

echo "Starting script migration tests..."
echo

# Test migrated Code Quality scripts
test_script "$SCRIPT_BASE/analyze/code_quality/complexity_metrics.py" \
    "complexity_metrics.py" \
    "Code complexity metrics and quality issues analysis"

test_script "$SCRIPT_BASE/analyze/code_quality/complexity_lizard.py" \
    "complexity_lizard.py" \
    "Lizard-based code complexity analysis"

# Test migrated Architecture scripts
test_script "$SCRIPT_BASE/analyze/architecture/coupling_analysis.py" \
    "coupling_analysis.py" \
    "Code coupling and dependency pattern analysis"

# Test migrated Performance scripts  
test_script "$SCRIPT_BASE/analyze/performance/profile_database.py" \
    "profile_database.py" \
    "Database usage patterns and performance analysis"

# Test migrated Root Cause scripts
test_script "$SCRIPT_BASE/analyze/root_cause/trace_execution.py" \
    "trace_execution.py" \
    "Execution patterns and dependencies for debugging"

test_script "$SCRIPT_BASE/analyze/root_cause/recent_changes.py" \
    "recent_changes.py" \
    "Recent code changes and their patterns"

test_script "$SCRIPT_BASE/analyze/root_cause/error_patterns.py" \
    "error_patterns.py" \
    "Error patterns and debug traces in codebase"

# Test migrated Run All Analysis script (special case - different output format)
echo -e "${YELLOW}Testing: run_all_analysis.py${NC}"
echo "Description: Comprehensive code analysis across multiple dimensions"

# Test help
echo -n "  Help flag (--help): "
if python "$SCRIPT_BASE/run_all_analysis.py" --help 2>&1 | grep -q "output-format"; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test JSON output (different format for run_all_analysis.py)
echo -n "  JSON output (default): "
if python "$SCRIPT_BASE/run_all_analysis.py" "$TEST_TARGET" --output-format json 2>/dev/null | head -5 | grep -q '"combined_analysis"'; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test Console output
echo -n "  Console output format: "
if python "$SCRIPT_BASE/run_all_analysis.py" "$TEST_TARGET" --output-format console 2>/dev/null | head -5 | grep -q "COMPREHENSIVE ANALYSIS"; then
    echo -e "${GREEN}PASS${NC}"
    echo -e "  ${GREEN}✓ All tests passed for run_all_analysis.py${NC}"
else
    echo -e "${RED}FAIL${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

TOTAL_TESTS=$((TOTAL_TESTS + 1))
if [ $FAILED_TESTS -eq 0 ]; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi

# Final results
echo "=== TEST RESULTS ==="
echo "Total scripts tested: $((TOTAL_TESTS))"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED! Script migration successful.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check the output above for details.${NC}"
    exit 1
fi