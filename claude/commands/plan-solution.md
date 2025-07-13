# Solution Planning Command

**Mindset**: "Research, investigate, and present options" - Technical consultant approach to solving specific engineering challenges through systematic analysis and solution comparison.

## Behavior

When presented with a technical challenge or feature requirement, conduct comprehensive investigation using current best practices, analyze existing system context, and present three distinct solution approaches with detailed comparative analysis and recommendations.

## Initial Context Gathering

**FIRST:** Before beginning analysis, ask the user to provide their technical challenge and additional context:

"To ensure my analysis addresses your specific situation, please provide:

**1. Technical Challenge:**
- Describe the specific problem, feature, or system requirement you need to address
- Include any current pain points or limitations you're experiencing

**2. Technical Environment Constraints:**
- Existing technology stack, platforms, or infrastructure requirements
- Legacy system integration requirements  
- Compliance, security, or regulatory constraints
- Team skill sets and technology preferences

**3. Development Approach Preferences:**
- Do you prefer leveraging established libraries/frameworks vs custom development?
- Priority: speed to market, cost optimization, technical control, or long-term maintainability?
- Available development resources and timeline constraints

Please provide your technical challenge and any relevant constraints, or confirm if you'd like me to proceed with general assumptions."

## Investigation Process

### Phase 1: Current System Analysis

Execute existing architecture analysis to understand current context:

**Note**: LLM must locate the script installation directory dynamically using Glob tool to find script paths, then execute with correct absolute paths.

```bash
# Example execution format (LLM will determine actual paths):
python [SCRIPT_PATH]/pattern_evaluation.py . --output-format json
python [SCRIPT_PATH]/scalability_check.py . --output-format json  
python [SCRIPT_PATH]/coupling_analysis.py . --output-format json
```

**Script Location Process:**
1. Use Glob tool to find script paths: `**/scripts/analyze/architecture/*.py`
2. Verify script availability and determine correct absolute paths
3. Execute scripts with resolved paths

**Analysis Integration:**
- Identify current architectural patterns and constraints
- Assess existing system scalability and coupling characteristics  
- Understand integration points and technical debt considerations
- Document current technology stack and infrastructure

### Phase 2: Research & Investigation

**Deep Dive Research:** Perform comprehensive web search targeting:

1. **Official Documentation:** Current APIs, framework guides, platform docs
2. **GitHub Repositories:** Well-maintained projects, examples, reference implementations
3. **Technical Publications:** Recent articles from reputable sources and experts
4. **Community Insights:** Recent discussions, emerging trends, best practices

**Research Focus:**
- Current versions and capabilities of relevant technologies
- Recent security updates and best practice changes
- Performance benchmarks and optimization techniques
- Integration patterns and compatibility considerations
- Community adoption trends and known issues

### Phase 3: Solution Development

## Solution 1: [Descriptive Name]

**Technical Approach:**
- Describe the core technical architecture and implementation strategy
- Explain key components, technologies, and design patterns
- Detail how this integrates with existing system architecture
- Outline implementation phases and deployment approach

**Technology Stack:**
- Primary technologies and frameworks required
- Integration requirements with current system
- Infrastructure and operational requirements
- Development tooling and testing approach

**Implementation Complexity:**
- Development effort and timeline estimation
- Required team skills and resources
- Risk factors and mitigation strategies
- Maintenance and operational considerations

## Solution 2: [Descriptive Name]

**Technical Approach:**
- Present alternative architectural strategy and design patterns
- Highlight different technology choices and implementation methods
- Explain unique integration approach with existing systems
- Detail alternative deployment and operational strategies

**Technology Stack:**
- Different technology choices and their justifications
- Alternative integration patterns and methodologies
- Infrastructure and scaling considerations
- Development and testing framework differences

**Implementation Complexity:**
- Comparative development effort and resource requirements
- Different skill requirements and learning curves
- Alternative risk profile and mitigation approaches
- Long-term maintenance and evolution considerations

## Solution 3: [Descriptive Name]

**Technical Approach:**
- Introduce innovative or emerging technology approach
- Emphasize cutting-edge methodologies or architectural patterns
- Explain differentiated integration and deployment strategies
- Address future-proofing and scalability advantages

**Technology Stack:**
- Modern or emerging technologies and frameworks
- Advanced integration patterns and methodologies
- Cloud-native or serverless considerations
- Developer experience and productivity tools

**Implementation Complexity:**
- Investment in new technology adoption
- Team capability development requirements
- Technology maturity and ecosystem risks
- Innovation benefits vs stability trade-offs

## Comparative Analysis

### Technical Feasibility Comparison

| Aspect | Solution 1 | Solution 2 | Solution 3 |
|--------|------------|------------|------------|
| **Development Complexity** | [Assessment] | [Assessment] | [Assessment] |
| **Integration Effort** | [Assessment] | [Assessment] | [Assessment] |
| **Technology Risk** | [Assessment] | [Assessment] | [Assessment] |
| **Team Readiness** | [Assessment] | [Assessment] | [Assessment] |

### Performance & Scalability

**Solution 1 Performance:**
- Expected performance characteristics and bottlenecks
- Scalability limitations and scaling strategies
- Resource utilization and infrastructure costs
- Monitoring and optimization approaches

**Solution 2 Performance:**
- Alternative performance profile and trade-offs
- Different scaling approaches and limitations
- Resource efficiency and cost considerations
- Operational complexity and monitoring needs

**Solution 3 Performance:**
- Advanced performance capabilities and innovations
- Modern scaling patterns and elasticity features
- Cost-performance optimization opportunities
- Next-generation monitoring and observability

## Final Recommendation

**Recommended Solution:** [Selected Solution]

**Technical Justification:**
- Clear reasoning based on current system analysis and research findings
- Alignment with stated constraints and preferences
- Balance of technical excellence and practical implementation
- Risk mitigation and long-term viability considerations

**Implementation Roadmap:**
- Phase 1: [Critical path priorities and foundational work]
- Phase 2: [Core implementation and integration]
- Phase 3: [Optimization and advanced features]
- Risk mitigation strategies and contingency planning

**Success Criteria:**
- Technical performance benchmarks and acceptance criteria
- Integration success metrics and validation approaches
- Operational readiness indicators and monitoring setup
- Long-term maintenance and evolution planning

## Optional Flags

--c7: Use to validate solution approaches against current industry standards and best practices for your specific domain and technology stack
--seq: Use for systematic solution analysis - breaks down into clear steps: 'analyze current system', 'research best practices', 'evaluate solution options', 'compare trade-offs', 'recommend approach'

## Task List Transfer

**Final Step:** After presenting the solution recommendation and implementation roadmap, ask the user:

"Are you satisfied with this solution approach and ready to proceed with implementation? If yes, I'll transfer the implementation roadmap to your project's todo.md file for tracking."

**If user confirms:**
1. Check if `./docs/todo.md` exists
2. If it exists, append the implementation tasks from the roadmap
3. If it doesn't exist, create it with the implementation tasks
4. Format tasks as actionable items with clear deliverables
5. Confirm to user that tasks have been added to todo.md

**Task Format Example:**
```markdown
## [Solution Name] Implementation Tasks

### Phase 1: Foundation
- [ ] Set up development environment for [selected solution]
- [ ] Create initial project structure following [pattern]
- [ ] Implement core [feature] with basic functionality

### Phase 2: Core Implementation  
- [ ] Build [main component] with full feature set
- [ ] Integrate with existing [system/API]
- [ ] Add comprehensive error handling

### Phase 3: Optimization
- [ ] Performance optimization for [identified bottlenecks]
- [ ] Add monitoring and observability
- [ ] Documentation and deployment preparation
```

## Output Requirements

- Three distinct, well-researched solution approaches with technical depth
- Comprehensive comparative analysis based on current research
- Evidence-based recommendation aligned with user constraints
- Practical implementation roadmap with risk mitigation
- Integration with existing system architecture analysis
- Transfer approved tasks to todo.md for implementation tracking

$ARGUMENTS