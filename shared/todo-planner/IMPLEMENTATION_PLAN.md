# Todo-Planner Enhancement Implementation Plan

## Executive Summary

Based on comprehensive analysis and recent fixes to the todo-planner system, this plan outlines targeted enhancements to achieve PRP-level context richness while maintaining the solid API-driven architecture and template system foundation.

**Status**: Current system generates correct code structure but needs PRP-level implementation guidance at the task level.

## Recent Fixes Completed ✅

### Template System Overhaul

- ✅ Aligned template directories with better-t-stack naming conventions
- ✅ Fixed all Jinja2 syntax errors (`.lower()` → `|lower`, complex conditionals)
- ✅ Eliminated compound stack profiles, using individual tech stack fields
- ✅ Improved template lookup logic with mapping exceptions
- ✅ Created comprehensive better-t-stack compatibility reference

### Infrastructure Improvements

- ✅ Built `better_t_stack_reference.py` with validation functions
- ✅ Created `stack_selection_guide.py` for LLM-guided stack selection
- ✅ Removed hardcoded compatibility restrictions (Convex + auth now works)
- ✅ Added proper error handling and fallback mechanisms

## Phase 1: Enhanced Task Generation 🎯

**Priority**: High | **Effort**: Medium | **Timeline**: 1-2 weeks

### Objective

Transform sparse task descriptions into rich, contextual implementation guides comparable to PRP blueprints.

### Current State

```markdown
- [ ] **packages/backend/convex/scans.ts**:`createScan()` [feat-001, feat-005]
  - **Purpose**: Create new scan record in database
  - **Return Type**: Promise<Id<"scans">>
```

### Target State

````markdown
- [ ] **packages/backend/convex/scans.ts**:`createScan()` [feat-001, feat-005]

  - **Purpose**: Create new scan record in database with validation and quota checking
  - **Return Type**: Promise<Id<"scans">>

  **Context & Guidance:**

  - Similar functions: `createReport()`, `createUser()` in users.ts
  - Business rules: URL validation, quota checking, duplicate prevention
  - Integration: Called by API route `/api/analyze`, triggers job queue
  - Validation: Use Convex validators for input sanitization
  - Error handling: Return meaningful errors for quota exceeded, invalid URLs

  **Implementation Pattern:**

  ```typescript
  // 1. Validate inputs using Convex validators
  // 2. Check user quota and permissions
  // 3. Create database record with audit fields
  // 4. Trigger background job for URL analysis
  // 5. Return scan ID for tracking
  ```
````

**Completion Criteria:**

- [ ] Input validation with proper error messages
- [ ] Quota checking integration
- [ ] Database record created with all required fields
- [ ] Background job triggered successfully
- [ ] Unit tests cover error cases

````

### Implementation Tasks
1. **Update `generate_tasks.py`**
   - Add context analysis functions
   - Enhance task description templates
   - Include implementation patterns and completion criteria

2. **Create Context Extraction Module**
   - Function similarity detection
   - Business rule extraction from PRD
   - Integration point identification
   - Common pattern recognition

3. **Template Enhancement**
   - Add guidance injection points in templates
   - Include completion criteria templates
   - Create implementation pattern libraries

### Success Metrics
- Task descriptions average 200+ words vs current 20-30 words
- 90% of tasks include relevant context and examples
- Implementation time reduced by 30% due to better guidance

## Phase 2: Function Cross-Reference System 🔗
**Priority**: High | **Effort**: Medium | **Timeline**: 1-2 weeks

### Objective
Prevent function duplication and improve awareness of existing code through comprehensive function registry and cross-referencing.

### Implementation
1. **Extend Skeleton Manifest**
   ```json
   {
     "function_registry": {
       "createScan": {
         "similar_functions": ["createReport", "createAudit"],
         "calls": ["validateUrl", "checkQuota", "triggerJob"],
         "called_by": ["POST /api/analyze"],
         "business_rules": ["feat-001: URL validation", "feat-005: Quota limits"],
         "integration_points": ["job_queue", "notification_system"],
         "implementation_hints": ["Use Convex validators", "Check user quota first"]
       }
     }
   }
````

2. **Function Dependency Analysis**

   - Static analysis of existing codebase functions
   - Cross-reference with PRD requirements
   - Identify call patterns and dependencies
   - Generate function interaction maps

3. **Duplication Prevention**
   - Pre-implementation function existence checks
   - Similarity warnings in task descriptions
   - Suggested function reuse recommendations

### Success Metrics

- Zero duplicate function implementations
- 100% of functions have documented dependencies
- Developers reference existing functions before creating new ones

## Phase 3: Smart Context Injection 🧠

**Priority**: Medium | **Effort**: High | **Timeline**: 2-3 weeks

### Objective

Automatically inject relevant contextual information from codebase analysis and pattern recognition into task descriptions.

### Implementation Approach

1. **Codebase Analysis Engine**

   - Scan existing codebase for similar functions and patterns
   - Extract implementation approaches and error handling strategies
   - Build pattern library for common operations
   - Index business logic and integration patterns

2. **Context Injection Pipeline**

   - Pattern matching for similar implementations
   - Business rule extraction from PRD sections
   - Integration requirement identification
   - Best practice recommendation engine

3. **Smart Template Selection**
   - Context-aware template enhancement
   - Dynamic guidance based on project patterns
   - Technology-specific best practice injection
   - Error handling pattern suggestions

### Technical Implementation

```python
class ContextInjector:
    def enhance_task(self, task_spec, codebase_analysis, prd_context):
        # Find similar functions
        similar = self.find_similar_functions(task_spec, codebase_analysis)

        # Extract business rules
        rules = self.extract_business_rules(task_spec.prd_references, prd_context)

        # Generate implementation guidance
        patterns = self.suggest_implementation_patterns(task_spec, similar)

        # Create enhanced task description
        return self.build_rich_task_description(task_spec, similar, rules, patterns)
```

### Success Metrics

- 95% of tasks include relevant contextual examples
- Implementation consistency across similar functions improved by 80%
- Developer satisfaction with task guidance increased significantly

## Phase 4: Template Example Documentation 📚

**Priority**: Medium | **Effort**: Low | **Timeline**: 3-5 days

### Objective

Document working examples of properly fixed Jinja2 templates to serve as few-shot examples in `TEMPLATING_APPROACH.md`.

### Implementation Tasks

1. **Capture Successful Template Patterns**

   - Document the Convex mutation template fixes (`.lower()` → `|lower`)
   - Show proper conditional handling with set variables
   - Demonstrate complex logic replacement patterns

2. **Create Template Fix Examples**

   ```jinja2
   {# ❌ INCORRECT - Python syntax not valid in Jinja2 #}
   {% if not functions or not any('table' in f.name.lower() for f in functions) %}

   {# ✅ CORRECT - Proper Jinja2 pattern #}
   {% set has_table_function = false %}
   {% for f in functions %}
     {% if 'table' in f.name|lower or 'schema' in f.name|lower %}
       {% set has_table_function = true %}
     {% endif %}
   {% endfor %}
   {% if not functions or not has_table_function %}
   ```

3. **Update TEMPLATING_APPROACH.md**

   - Add "Common Jinja2 Syntax Fixes" section
   - Include before/after examples of all fixes applied
   - Document best practices for complex conditionals
   - Add validation checklist for template authors

4. **Template Validation Guidelines**
   - Checklist for Jinja2 syntax validation
   - Common pitfalls and their solutions
   - Testing procedures for new templates

### Deliverables

- Enhanced `TEMPLATING_APPROACH.md` with working examples
- Template syntax validation checklist
- Best practices guide for template authors
- Documented patterns for complex logic handling

## Implementation Timeline

### Week 1-2: Phase 1 - Enhanced Task Generation

- [ ] Update `generate_tasks.py` with rich descriptions
- [ ] Create context extraction module
- [ ] Test with landing-conversion-scorer project
- [ ] Validate task quality improvements

### Week 3-4: Phase 2 - Function Cross-Reference System

- [ ] Extend manifest with function registry
- [ ] Implement dependency analysis
- [ ] Add duplication prevention checks
- [ ] Test function awareness improvements

### Week 5-7: Phase 3 - Smart Context Injection

- [ ] Build codebase analysis engine
- [ ] Implement context injection pipeline
- [ ] Create smart template enhancement
- [ ] Performance optimization and testing

### Week 8: Phase 4 - Template Documentation

- [ ] Document working template examples
- [ ] Update TEMPLATING_APPROACH.md
- [ ] Create validation guidelines
- [ ] Final documentation review

## Success Criteria

### Quantitative Metrics

- **Task Richness**: Average task description increases from 30 to 200+ words
- **Context Accuracy**: 95% of tasks include relevant contextual examples
- **Function Duplication**: Reduced to zero through awareness system
- **Implementation Speed**: 30% faster development due to better guidance
- **Template Quality**: 100% Jinja2 syntax compliance

### Qualitative Metrics

- Developers can implement tasks without external research
- Task descriptions feel comprehensive and actionable
- Function awareness prevents duplicate implementations
- Template system is maintainable and extensible
- Documentation serves as effective reference material

## Risk Mitigation

### Technical Risks

- **Performance Impact**: Context analysis may slow skeleton generation
  - _Mitigation_: Implement caching and optimize analysis algorithms
- **Complexity Creep**: Rich context may overcomplicate simple tasks
  - _Mitigation_: Tiered context depth based on task complexity
- **Template Maintenance**: More sophisticated templates harder to maintain
  - _Mitigation_: Comprehensive documentation and validation tools

### Process Risks

- **Scope Expansion**: Feature requests may derail focused improvements
  - _Mitigation_: Strict adherence to phased implementation plan
- **Quality Regression**: Changes may break existing functionality
  - _Mitigation_: Comprehensive testing and gradual rollout

## Conclusion

This implementation plan builds upon the solid foundation of the todo-planner system while addressing the key gaps identified in comparison to PRP. The focus on enhanced task generation and function awareness will bring the system to PRP-level guidance quality while maintaining the superior architectural approach of progressive pipeline execution with quality gates.

The phased approach ensures steady progress with measurable improvements at each stage, while the template documentation phase captures the valuable lessons learned from our recent syntax fixes.
