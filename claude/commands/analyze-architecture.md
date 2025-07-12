# Architecture Review Command

**Mindset**: "Design for scale and maintainability" - Evaluate system architecture for scalability, maintainability, and best practices.

## Behavior
Comprehensive system architecture evaluation combining automated analysis with design pattern assessment for scalable, maintainable systems.

### Automated Architecture Analysis
Execute architecture analysis scripts via Bash tool for measurable design metrics:
```bash
# Architecture pattern and scalability analysis
python claude/scripts/analyze/architecture/pattern_evaluation.py --target . --format json
python claude/scripts/analyze/architecture/scalability_check.py --target . --format json
python claude/scripts/analyze/architecture/coupling_analysis.py --target . --format json
```

### Architecture Assessment Areas
- **Service Boundaries**: Microservice decomposition and responsibility definition
- **Design Pattern Compliance**: SOLID principles, GoF patterns, architectural patterns
- **Coupling Analysis**: Inter-service dependencies and communication patterns
- **Scalability Bottlenecks**: Infrastructure limitations and growth constraints
- **Data Flow Architecture**: State management and data consistency patterns

## Analysis Process
1. **Execute automated scripts** for quantitative architecture metrics
2. **Evaluate design patterns** against established best practices
3. **Assess scalability** through bottleneck identification
4. **Analyze coupling** between components and services
5. **Generate recommendations** for architectural improvements

## Optional Flags
--c7: Use when you need to validate your architecture decisions against current industry standards for your specific tech stack (e.g., microservices patterns for Node.js, serverless best practices for AWS)
--seq: Use when architecture analysis involves multiple concerns - breaks down into clear steps like 'analyze service boundaries', 'evaluate scalability bottlenecks', 'assess security architecture', 'review data flow patterns'

## Assessment Areas
Coupling, Cohesion, Scalability, Maintainability, Testability, Deployment

## Output Requirements
- Architecture metrics report with automated analysis results
- Design pattern compliance assessment
- Scalability bottleneck identification with mitigation strategies
- Architectural improvement roadmap with implementation priorities

$ARGUMENTS