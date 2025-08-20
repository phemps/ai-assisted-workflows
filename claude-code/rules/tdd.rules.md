**CRITICAL** You must follow and apply the below ways of working to your current task(s)

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
