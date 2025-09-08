# General coding rules

## Design Principles:

- **NEVER implement backward compatibility** never refactor code to handle its new objective AND its legacy objective, all legacy code should be removed.
- **NEVER create fallbacks** we never build fallback mechanisms, our code should be designed to work as intended without fallbacks.
- **NEVER over engineer** only action what the user has requested, if you dont have approval for an action you must ask the user.
- **ALWAYS use `mcp__serena` for codebase search** its more efficient than grep or glob.
- **ALWAYS prefer established libraries over bespoke code** only produce bespoke code if no established library exists.
- **Follow these architectural guidelines**:
  - **Single Responsibility**: Each class/function should have one responsibility
  - **Extract common logic** into reusable functions, classes, or modules when used 3+ times
  - **Refactoring Code**: When refactoring do not add prefixes/suffixes like "Refactored", "Updated", "New", or "V2" to symbol names to indicate changes.

# Behaviour Rules

## **CRITICAL** Must follow Protocols:

### Context Gathering:

- **MUST**: Read the entire contents of a file - when supplied one to review or have identified one for your current task objective.

### Security Requirements:

- **NEVER**: commit secrets, API keys, or credentials to version control
- **NEVER**: expose sensitive information like api keys, secrets or credentials in any log or database entries

### Core Prohibitions:

- **NEVER** use placeholders, mocking, hardcoded values, or stub implementations outside test contexts
- **NEVER** suppress, bypass, handle with defaults, or work around quality gate failures, errors, or test failures
- **NEVER** alter, disable, suppress, add permissive variants to, or conditionally bypass quality gates or tests
- **NEVER** comment out, conditionally disable, rename to avoid calling, or move to unreachable locations any failing code
- **NEVER** delegate prohibited behaviors to external services, configuration files, or separate modules
- **NEVER** bypass, skip or change a task if it fails without the users permission
- **NEVER** implement fallback modes or temporary strategys to meet task requirements
- **NEVER** bypass quality gates by using `--skip` or `--no-verify`

### Positive Requirements:

- **MUST** implement complete business logic that performs intended real-world operations
- **MUST** return live, computed results that accurately reflect current state and user inputs
- **MUST** handle all error scenarios through proper application logic, not silent failures or defaults
- **MUST** maintain functional equivalence between test and production code paths

### Verification Criteria:

- All code must carry out real actions, no placeholder or mock code
- All integrations must connect to real services or databases (not mocks/stubs in production)
- All error handling must provide meaningful feedback and maintain system integrity

---
