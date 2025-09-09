# fix-performance v0.4

**Mindset**: "Optimize systematically" - Targeted performance issue resolution with measurable improvement validation.

## Behavior

Systematic performance issue resolution combining automated bottleneck detection with optimization implementation and validation.

### Performance Optimization Strategy

- **Issue Identification**: Specific performance bottleneck isolation and measurement
- **Root Cause Analysis**: Systematic investigation of performance degradation causes
- **Solution Implementation**: Targeted optimization with minimal system impact
- **Performance Validation**: Before/after measurement and improvement verification
- **Monitoring Setup**: Ongoing performance monitoring and alerting implementation

## Performance Fix Framework (Diagnosis 30% | Analysis 25% | Implementation 30% | Validation 15%)

### Performance Diagnosis

- **Bottleneck Identification**: CPU, memory, I/O, and network bottleneck detection
- **Profiling Analysis**: Application profiling and resource utilization assessment
- **Query Optimization**: Database query performance analysis and optimization
- **Load Testing**: Performance testing under realistic load conditions

### Root Cause Analysis

- **Algorithm Analysis**: Algorithmic complexity assessment and optimization opportunities
- **Resource Usage**: Memory leaks, CPU utilization, and resource contention analysis
- **Database Performance**: Query execution plans, indexing, and connection pooling
- **Network Optimization**: Request optimization, caching, and CDN utilization

### Implementation Strategy

- **Targeted Optimization**: Minimal changes with maximum performance impact
- **Caching Strategy**: Application-level, database, and CDN caching implementation
- **Code Optimization**: Algorithm improvements and resource usage optimization
- **Infrastructure Optimization**: Server configuration, load balancing, and scaling

### Performance Validation

- **Benchmark Comparison**: Before/after performance measurement and comparison
- **Load Testing**: Performance validation under expected and peak load conditions
- **Regression Testing**: Ensure performance improvements don't introduce functional issues
- **Monitoring Implementation**: Performance metrics, alerts, and trend analysis

## Script Integration

Execute performance analysis scripts via Bash tool for systematic bottleneck detection:

```bash
# Set paths and execute the analyzers
export PYTHONPATH="$(pwd)/.claude/scripts"
VENV_PYTHON="$(pwd)/.claude/venv/bin/python"

"$VENV_PYTHON" -m analyzers.performance.flake8_performance_analyzer . --output-format json
"$VENV_PYTHON" -m analyzers.performance.analyze_frontend . --output-format json
"$VENV_PYTHON" -m analyzers.performance.sqlfluff_analyzer . --output-format json
```

## Performance Areas

Database, Frontend, Algorithms, Memory, Network, Caching

## Output Requirements

- Performance issue analysis with specific bottleneck identification
- Optimization implementation with measurable improvement targets
- Before/after performance comparison with validation results
- Ongoing monitoring strategy for performance regression prevention

$ARGUMENTS
