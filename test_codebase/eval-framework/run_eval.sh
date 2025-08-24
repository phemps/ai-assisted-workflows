#!/bin/bash
set -e

# Security Analysis Evaluation Runner
# ==================================
# 
# PURPOSE: Convenience script to run security analysis evaluation and generate reports

echo "🔍 Security Analysis Evaluation"
echo "==============================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "run_evaluations.py" ]]; then
    log_error "run_evaluations.py not found. Make sure you're in the eval-framework directory."
    exit 1
fi

# Check Python availability
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed"
    exit 1
fi

# Check if vulnerable apps exist
VULNERABLE_APPS_DIR="../vulnerable-apps"
if [[ ! -d "$VULNERABLE_APPS_DIR" ]]; then
    log_error "Vulnerable apps directory not found: $VULNERABLE_APPS_DIR"
    log_info "Run: cd ../vulnerable-apps && ./setup.sh"
    exit 1
fi

# Parse command line arguments
ANALYZER=""
APPLICATION=""
VERBOSE=false
OUTPUT_FORMAT="both"

while [[ $# -gt 0 ]]; do
    case $1 in
        --analyzer)
            ANALYZER="$2"
            shift 2
            ;;
        --application)
            APPLICATION="$2" 
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --analyzer NAME     Run specific analyzer only"
            echo "  --application NAME  Run against specific application only"
            echo "  --verbose          Show detailed output"
            echo "  --format FORMAT    Report format: markdown, html, both (default: both)"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run full evaluation"
            echo "  $0 --analyzer semgrep                # Test semgrep only"
            echo "  $0 --application nodegoat             # Test NodeGoat only" 
            echo "  $0 --analyzer semgrep --verbose      # Detailed semgrep testing"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command line arguments
EVAL_ARGS=""
if [[ -n "$ANALYZER" ]]; then
    EVAL_ARGS="$EVAL_ARGS --analyzer $ANALYZER"
fi
if [[ -n "$APPLICATION" ]]; then
    EVAL_ARGS="$EVAL_ARGS --application $APPLICATION"
fi
if [[ "$VERBOSE" == true ]]; then
    EVAL_ARGS="$EVAL_ARGS --verbose"
fi

# Create results directory
mkdir -p results

# Generate timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_FILE="results/evaluation_results_${TIMESTAMP}.json"
REPORT_PREFIX="results/evaluation_report_${TIMESTAMP}"

echo ""
log_info "Starting evaluation..."
log_info "Results will be saved to: $RESULTS_FILE"

# Run the evaluation
echo ""
log_info "Running security analysis evaluation..."
python3 run_evaluations.py --output "$RESULTS_FILE" $EVAL_ARGS

# Check if evaluation was successful
if [[ $? -eq 0 && -f "$RESULTS_FILE" ]]; then
    log_success "Evaluation completed successfully"
    
    # Generate reports
    echo ""
    log_info "Generating reports..."
    python3 generate_report.py --results "$RESULTS_FILE" --output "$REPORT_PREFIX" --format "$OUTPUT_FORMAT"
    
    if [[ $? -eq 0 ]]; then
        log_success "Reports generated successfully"
        
        echo ""
        echo "📊 Results Summary:"
        echo "=================="
        
        # Extract and display key metrics from results
        if command -v jq &> /dev/null; then
            echo ""
            echo "📈 Key Metrics:"
            jq -r '
                .summary | 
                "Total Evaluations: " + (.total_evaluations | tostring) + "\n" +
                "Successful Runs: " + (.successful_runs | tostring) + "\n" +  
                "Failed Runs: " + (.failed_runs | tostring) + "\n" +
                (if .average_metrics then
                    "Average Precision: " + (.average_metrics.precision | tostring | .[0:5]) + "\n" +
                    "Average Recall: " + (.average_metrics.recall | tostring | .[0:5]) + "\n" +
                    "Average F1-Score: " + (.average_metrics.f1_score | tostring | .[0:5])
                else
                    "No metrics calculated"
                end)
            ' "$RESULTS_FILE" 2>/dev/null || {
                log_info "Install jq for detailed metrics display"
            }
        fi
        
        echo ""
        echo "📁 Generated Files:"
        if [[ "$OUTPUT_FORMAT" == "markdown" || "$OUTPUT_FORMAT" == "both" ]]; then
            echo "  📄 Markdown Report: ${REPORT_PREFIX}.md"
        fi
        if [[ "$OUTPUT_FORMAT" == "html" || "$OUTPUT_FORMAT" == "both" ]]; then
            echo "  🌐 HTML Report: ${REPORT_PREFIX}.html"
        fi
        echo "  📊 Raw Results: $RESULTS_FILE"
        
        # Quick links for latest results
        ln -sf "$(basename "$RESULTS_FILE")" results/latest_results.json 2>/dev/null || true
        if [[ -f "${REPORT_PREFIX}.html" ]]; then
            ln -sf "$(basename "${REPORT_PREFIX}.html")" results/latest_report.html 2>/dev/null || true
        fi
        if [[ -f "${REPORT_PREFIX}.md" ]]; then
            ln -sf "$(basename "${REPORT_PREFIX}.md")" results/latest_report.md 2>/dev/null || true  
        fi
        
        echo ""
        log_success "✅ Evaluation complete!"
        echo ""
        echo "Quick access to latest results:"
        echo "  📊 Latest JSON: results/latest_results.json"
        if [[ -f "results/latest_report.html" ]]; then
            echo "  🌐 Latest HTML: results/latest_report.html"
        fi
        if [[ -f "results/latest_report.md" ]]; then
            echo "  📄 Latest Markdown: results/latest_report.md"
        fi
        
    else
        log_error "Report generation failed"
        exit 1
    fi
    
else
    log_error "Evaluation failed"
    exit 1
fi

echo ""
log_info "Next steps:"
echo "  1. Review the generated reports"
echo "  2. Identify areas for analyzer improvement"
echo "  3. Update analyzer rules based on findings"
echo "  4. Re-run evaluation to measure improvements"