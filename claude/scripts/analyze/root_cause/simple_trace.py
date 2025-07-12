#!/usr/bin/env python3
"""
Simple root cause analysis script: Basic execution tracing.
Part of SuperCopilot scriptable workflows.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add utils to path for imports
script_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(script_dir / "utils"))

from output_formatter import ResultFormatter, Severity, AnalysisType, Finding, AnalysisResult

def main():
    """Main execution function."""
    start_time = time.time()
    
    # Get target directory
    target_dir = Path(os.getcwd())
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    
    # Initialize result
    result = AnalysisResult(AnalysisType.ARCHITECTURE, "simple_trace.py", str(target_dir))
    
    # Simple analysis - just count files and basic info
    python_files = list(target_dir.rglob('*.py'))
    
    # Filter out common excludes
    python_files = [f for f in python_files if not any(exclude in str(f) for exclude in [
        'node_modules', '.git', '__pycache__', '.pytest_cache',
        'venv', 'env', 'build', 'dist'
    ])]
    
    # Basic analysis
    for i, file_path in enumerate(python_files[:5]):  # Limit to 5 files
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                line_count = len(content.split('\n'))
                
            finding_obj = Finding(
                finding_id=f"file_info_{i}",
                title=f"Python File Analysis",
                description=f"File {file_path.name} has {line_count} lines",
                severity=Severity.INFO,
                file_path=str(file_path),
                evidence={"line_count": line_count, "file_size": len(content)}
            )
            result.add_finding(finding_obj)
            
        except Exception as e:
            continue
    
    # Set execution time and add metadata
    result.set_execution_time(start_time)
    result.metadata.update({
        "python_files_found": len(python_files),
        "files_analyzed": min(5, len(python_files))
    })
    
    # Output results
    print(result.to_json())

if __name__ == "__main__":
    main()