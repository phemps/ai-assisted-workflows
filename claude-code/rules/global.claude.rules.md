# Monitor User Request For Flags Enabled User Mode

- If user request contains flag `--prototype` → <rapid_prototype> = enabled
- If user request contains flag `--tdd` → <tdd> = enabled
- If user request contains flag `--seq` → <seq> = enabled
- If user request contains flag `--gitgrep` → <git_grep> = enabled
- if user request contains flag `--critique` → <critique> = enabled

## User Modes

**IMPORTANT**: User mode is only applied if it has been enabled

<rapid_prototype>

## rapid_prototype = enabled

You must follow and apply the below ways of working to your current task(s)

**Purpose**: Quick proof-of-concept development with minimal setup and rapid iteration

## Core Principles:

- Prioritize speed and iteration over perfection
- Use existing libraries and frameworks instead of building from scratch
- Mock external dependencies rather than implementing full integrations
- Focus on demonstrating core functionality
- Use hardcoded values where configuration would slow development
- Implement happy path scenarios first with minimal testing

## Library Selection:

- Choose well-established component libraries with extensive pre-built components
- Prefer opinionated frameworks that provide structure out-of-the-box
- Use starter templates and boilerplates when available
- Leverage UI component libraries for rapid interface development

## Data Handling:

- Use mock data and fixtures for all external service calls
- Implement data persistence with in-memory stores or local storage
- Create realistic test data that demonstrates all use cases
- Avoid complex database setup or migrations

## Testing Approach:

- Run type checking and build compilation after each feature addition
- Use language-appropriate tools (TypeScript tsc, Python mypy, Go build, etc.)
- Fix all type errors and build failures before proceeding
- All other automated testing is avoided

## Output Requirements:

- Working prototype accessible with minimal setup (single command ideally)
  </rapid_prototype>
  <tdd>

## tdd = enabled

You must follow and apply the below ways of working to your current task(s)

**Purpose**: Systematic test-driven development with comprehensive test coverage and quality assurance

## Core Principles:

- Write tests before implementation code
- Every new feature starts with a failing test
- Tests define the specification and expected behavior
- Implementation should be minimal to pass tests
- Never alter or suppress test behaviour to achieve a pass
- Tests must run in under 10 seconds for development cycle
- Use test doubles (mocks, stubs) for external dependencies
- Assertions must be specific and provide clear failure messages

## Test Creation Standards:

- Test names must clearly describe the expected behavior
- Each test should verify one specific behavior
- Tests must be independent and runnable in any order
- Test use cases must be 100% unique, no duplication or overlapping of test effort

## Test Coverage Requirements:

- 100% coverage for business logic and critical paths, but not external libraries
- Edge cases and error scenarios must have explicit tests
- Integration tests for all external dependencies

## Implementation Process:

1. **Red Phase**: Write failing test that defines desired behavior
2. **Green Phase**: Write minimal code to make test pass
3. **Refactor Phase**: Improve code design while keeping tests green
4. **Repeat**: Continue cycle for each new requirement

## Test Types Required:

- **Unit Tests**: For all public methods and functions
- **Integration Tests**: For component interactions
- **Acceptance Tests**: For user-facing features
  </tdd>
  <seq_mode>

## seq_mode = enabled

You must use the sequential-thinking MCP tool for complex, multi-step analysis to break down the task(s)

## How to use this tool:

- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out
  </seq_mode>
  <git_grep>

## git_grep = enabled

You must use the grep MCP tool to search highly rated GitHub repositories

## How to use this tool:

- Finding code examples from popular repositories
- Discovering libraries for specific functionality
- Learning implementation patterns from established projects
- Researching best practices in the ecosystem
  </grit_grep>
  <critique>

</critique>

# **IMPORTANT** Must Follow Global Coding Rules:

- **Avoid backward compatibility** let git handle versioning and just design for the current task, dont try and preserve old code unless asked.
- **Never use placeholders, mock or hardcoded code** all code must carry out real actions and return real results that reflect its intention.
- **Minimise bespoke code** we should always favour established libraries over bespoke code.
- **NEVER over engineer** only action what the user has approved, if you dont have approval for an action ask the user.
- **Always use `mcp__serena` for codebase search** its more efficient than grep or glob.
- **Always follow these design principles**:
  - Create base classes for shared behavior
  - Single Responsibility: Each class/function should have one reason to change
  - Interface Segregation: Many specific interfaces over one general interface
  - Keep functions under 30 lines
  - Keep Class files under 300 lines
  - Extract common logic into reusable functions, classes, or modules

---
