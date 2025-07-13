#!/bin/bash

# Test script for install.sh fixes
# Tests path handling and backup functionality

set -e

echo "Testing install.sh fixes..."

# Create temporary test directory
TEST_DIR="/tmp/claude-workflows-test-$$"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Function to cleanup
cleanup() {
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Test 1: Path ending with .claude
echo ""
echo "Test 1: Path ending with .claude"
echo "--------------------------------"
mkdir -p test1/.claude
cd "$REPO_PATH" # Need to be set to the repo path
./install.sh "$TEST_DIR/test1/.claude" --dry-run -v 2>&1 | grep -q "Target path already ends with .claude, using it directly"
if [[ $? -eq 0 ]]; then
    echo "✓ Path handling test passed"
else
    echo "✗ Path handling test failed"
    exit 1
fi

# Test 2: Normal path (should append .claude)
echo ""
echo "Test 2: Normal path"
echo "-------------------"
cd "$REPO_PATH"
./install.sh "$TEST_DIR/test2" --dry-run -v 2>&1 | grep -q "Appending .claude to target path"
if [[ $? -eq 0 ]]; then
    echo "✓ Normal path test passed"
else
    echo "✗ Normal path test failed"
    exit 1
fi

# Test 3: Backup creation (dry run)
echo ""
echo "Test 3: Backup creation (dry run)"
echo "---------------------------------"
mkdir -p test3/.claude
touch test3/.claude/test-file.txt
cd "$REPO_PATH"
./install.sh "$TEST_DIR/test3" --dry-run 2>&1 | grep -q "Would create automatic backup before proceeding"
if [[ $? -eq 0 ]]; then
    echo "✓ Backup dry run test passed"
else
    echo "✗ Backup dry run test failed"
    exit 1
fi

echo ""
echo "All automated tests passed!"
echo ""
echo "Note: To run these tests, set REPO_PATH to your ClaudeWorkflows directory:"
echo "  export REPO_PATH=/path/to/ClaudeWorkflows"
echo "  ./test_install_fixes.sh"