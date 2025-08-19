# Monitor User Request For Flags Enabled User Mode

- If user request contains flag `--prototype` → <rapid_prototype> = enabled
- If user request contains flag `--tdd` → <tdd> = enabled

## User Modes

**IMPORTANT**: User mode is only applied if it has been enabled

<rapid_prototype>

## rapid_prototype = enabled

You must follow and apply the below ways of working to your current task(s)

**Purpose**: Quick proof-of-concept development with minimal setup and rapid iteration

### Core Principles:

- Prioritize speed and iteration over perfection
- Use existing libraries and frameworks instead of building from scratch
- Mock external dependencies rather than implementing full integrations
- Focus on demonstrating core functionality
- Use hardcoded values where configuration would slow development
- Implement happy path scenarios first with minimal testing

### Library Selection:

- Choose well-established component libraries with extensive pre-built components
- Prefer opinionated frameworks that provide structure out-of-the-box
- Use starter templates and boilerplates when available
- Leverage UI component libraries for rapid interface development

### Data Handling:

- Use mock data and fixtures for all external service calls
- Implement data persistence with in-memory stores or local storage
- Create realistic test data that demonstrates all use cases
- Avoid complex database setup or migrations

### Testing Approach:

- Run type checking and build compilation after each feature addition
- Use language-appropriate tools (TypeScript tsc, Python mypy, Go build, etc.)
- Fix all type errors and build failures before proceeding
- All other automated testing is avoided

### Output Requirements:

- Working prototype accessible with minimal setup (single command ideally)

</rapid_prototype>

<tdd>

## tdd = enabled

You must follow and apply the below ways of working to your current task(s)

**Purpose**: Systematic test-driven development with comprehensive test coverage and quality assurance

### Core Principles:

- Write tests before implementation code
- Every new feature starts with a failing test
- Tests define the specification and expected behavior
- Implementation should be minimal to pass tests
- Never alter or suppress test behaviour to achieve a pass
- Tests must run in under 10 seconds for development cycle
- Use test doubles (mocks, stubs) for external dependencies
- Assertions must be specific and provide clear failure messages

### Test Creation Standards:

- Test names must clearly describe the expected behavior
- Each test should verify one specific behavior
- Tests must be independent and runnable in any order
- Test use cases must be 100% unique, no duplication or overlapping of test effort

### Test Coverage Requirements:

**Tiered Testing Strategy**:

- **Fast Unit Tests** (CI presubmit): 90-95% coverage for business logic, must run under 10 seconds total
- **Integration Tests** (scheduled CI): Cover all external service integrations, allowed longer runtime
- **Acceptance Tests** (release gates): End-to-end user scenarios, can be slower

**Coverage Targets**:

- **Critical Business Logic**: 100% coverage required (payment processing, security validations, data integrity)
- **Standard Business Logic**: 80-95% coverage target
- **UI/Presentation Layer**: 70% coverage minimum
- **External Library Wrappers**: Test integration points only, not library internals

**Exception Process**: Document any coverage gaps below targets in PR description with business justification

### Implementation Process:

1. **Red Phase**: Write failing test that defines desired behavior
2. **Green Phase**: Write minimal code to make test pass
3. **Refactor Phase**: Improve code design while keeping tests green
4. **Repeat**: Continue cycle for each new requirement

### Test Types Required:

- **Unit Tests**: For all public methods and functions
- **Integration Tests**: For component interactions
- **Acceptance Tests**: For user-facing features

</tdd>

# **IMPORTANT** Must Follow Global Coding Rules:

## General coding rules

- **🚫 No Trailing Whitespace Policy**: Never leave spaces or tabs at the end of any line in any file.

## Security Requirements:

- **Secrets Management**: Never commit secrets, API keys, or credentials to version control
- **Data Minimization**: Log only necessary data, avoid logging PII without explicit approval
- **Least Privilege**: External integrations require documented threat model and minimal access scope

## Design Principles:

- **Avoid backward compatibility** let git handle versioning and just design for the current task, dont try and preserve old code unless asked.
- **Minimise bespoke code** we should always favour established libraries over bespoke code.
- **NEVER over engineer** only action what the user has approved, if you dont have approval for an action ask the user.
- **Always use `mcp__serena` for codebase search** its more efficient than grep or glob.
- **Follow these architectural guidelines**:
  - **Prefer composition over inheritance**: Only create base classes when shared behavior is substantial and stable
  - **Justify abstractions**: Document in PR why abstraction adds value over direct implementation
  - **Single Responsibility**: Each class/function should have one reason to change
  - **Interface Segregation**: Many specific interfaces over one general interface
  - **Function/Class Size Guidelines**: Keep functions under 30 lines and class files under 300 lines (exceptions allowed with justification in PR description)
  - **Extract common logic** into reusable functions, classes, or modules when used 3+ times

# **CRITICAL** ANTI Reward Hacking Protocol:

**META EXCEPTION**: These rules are BYPASSED when `<rapid_prototype>` mode is enabled (user request contains `--prototype` flag)

### Core Prohibitions:

- **NEVER** use placeholders, mocking, hardcoded values, or stub implementations outside test contexts
- **NEVER** suppress, bypass, handle with defaults, or work around quality gate failures, errors, or test failures
- **NEVER** alter, disable, add permissive variants to, or conditionally bypass quality gate or test rules
- **NEVER** comment out, conditionally disable, rename to avoid calling, or move to unreachable locations any failing code
- **NEVER** delegate prohibited behaviors to external services, configuration files, or separate modules

### Positive Requirements:

- **MUST** implement complete business logic that performs intended real-world operations
- **MUST** return live, computed results that accurately reflect current state and user inputs
- **MUST** handle all error scenarios through proper application logic, not silent failures or defaults
- **MUST** maintain functional equivalence between test and production code paths

### Verification Criteria:

- All code must demonstrate actual business value when executed
- All integrations must connect to real services or databases (not mocks/stubs in production)
- All user-facing features must work end-to-end without manual intervention
- All error handling must provide meaningful feedback and maintain system integrity

### Meta-Rule:

- **PROHIBITED**: Any technical approach, architectural pattern, or creative interpretation designed to circumvent the spirit of these rules while satisfying their letter

## Strategic Agent Delegation for Session Optimization

### **IMPORTANT** Agent Maximization Strategy

To extend Claude Code session uptime and preserve subscription usage, proactively delegate appropriate tasks to free tier AI agents:

#### **@agent-gemini-handler - Context-Heavy Analysis**

**Use When:**

- Task requires analysis of >5 files simultaneously
- Context window would exceed 50k tokens in Claude Code
- Comprehensive codebase analysis or documentation review needed
- Multi-file refactoring or large-scale architectural changes
- Research tasks requiring broad information synthesis

#### **@agent-qwen-handler - Tool-Heavy Operations**

**Use When:**

- Task requires >100 tool operations across multiple files
- Complex batch processing (file migrations, bulk edits)
- Multi-step development workflows with testing and validation
- File system operations requiring careful sequencing
- Iterative development tasks with extensive tool usage

### **Delegation Decision Matrix**

| Task Type                    | Primary Agent         | Rationale                                        |
| ---------------------------- | --------------------- | ------------------------------------------------ |
| Codebase analysis (>5 files) | @agent-gemini-handler | Leverage 1M token context window                 |
| Bulk file operations         | @agent-qwen-handler   | 2,000 daily requests for tool-heavy tasks        |
| Research & synthesis         | @agent-gemini-handler | Large context for comprehensive analysis         |
| Multi-step workflows         | @agent-qwen-handler   | Request-based billing ideal for tool sequences   |
| Architecture review          | @agent-gemini-handler | 1M token context for holistic understanding      |
| File migrations/refactoring  | @agent-qwen-handler   | Tool-intensive operations within generous limits |

### **Fallback Mechanism**

**CRITICAL**: If agent delegation fails for any reason (usage limits, errors, unavailability), immediately fallback your normal execution:

**Fallback Triggers:**

- Agent reports usage limit reached (daily/rate limits)
- Agent execution fails with errors
- Agent becomes unavailable or unresponsive
- Agent cannot complete task within reasonable timeframe

**Fallback Protocol:**

1. **Immediate Handoff**: Resume task execution yourself using your available tools
2. **Context Preservation**: Maintain all gathered context and progress made by the agent
3. **Task Adaptation**: Adjust approach as needed for your execution
4. **No Task Abandonment**: NEVER abandon a user task due to agent limitations

**Implementation:**

- Monitor agent execution status continuously
- Set reasonable timeout thresholds for agent completion
- Seamlessly transition to direct execution without user interruption
- Preserve user experience and task completion commitment

---
