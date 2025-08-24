# **IMPORTANT** Must Follow Global Coding Rules:

## General coding rules

- **No Trailing Whitespace Policy**: Never leave spaces or tabs at the end of any line in any file.
- **Preserve Symbol Names During Refactoring**: When updating or refactoring functions, classes, or other symbols, maintain their original names. Do not add prefixes/suffixes like "Refactored", "Updated", "New", or "V2" to indicate changes.
- **Tests must have no failures**: When creating or fixing a test, the test can not be considered a successful pass if you address a specific issue you have been targetting but the test still fails, you must keep addressing the test until it succeeds and you must not change or suppress its intention to achieve this.
- **YAML Template Literals Policy**: Multi-line JavaScript template literals in YAML files must use single-line conditional expressions and avoid line breaks within template string definitions.

## Security Requirements:

- **Secrets Management**: Never commit secrets, API keys, or credentials to version control

## Design Principles:

- **NEVER plan for backward compatibility** never refactor code to handle its new objective AND its legacy objective, all legacy code should be removed.
- **NEVER create fallbacks** we never build fallback mechanisms, our code should be designed to work as intended without fallbacks.
- **NEVER over engineer** only action what the user has requested, if you dont have approval for an action ask the user.
- **Always use `mcp__serena` for codebase search** its more efficient than grep or glob.
- **ALWAYS use established libraries over bespoke code** we should always favour established libraries over bespoke code.
- **Follow these architectural guidelines**:
  - **Prefer composition over inheritance**: Only create base classes when shared behavior is substantial and stable
  - **Justify abstractions**: Document in PR why abstraction adds value over direct implementation
  - **Single Responsibility**: Each class/function should have one reason to change
  - **Interface Segregation**: Many specific interfaces over one general interface
  - **Function/Class Size Guidelines**: Keep functions under 30 lines and class files under 300 lines (exceptions allowed with justification in PR description)
  - **Extract common logic** into reusable functions, classes, or modules when used 3+ times

# Behaviour Rules

## **CRITICAL** Must follow ANTI Reward Hacking Protocol:

### Core Prohibitions:

- **NEVER** use placeholders, mocking, hardcoded values, or stub implementations outside test contexts
- **NEVER** suppress, bypass, handle with defaults, or work around quality gate failures, errors, or test failures
- **NEVER** alter, disable, add permissive variants to, or conditionally bypass quality gate or test rules
- **NEVER** comment out, conditionally disable, rename to avoid calling, or move to unreachable locations any failing code
- **NEVER** delegate prohibited behaviors to external services, configuration files, or separate modules
- **NEVER** bypass or skip a task and move on to the next because a task failed once or repeatedly
- **NEVER** implement fallback modes or temporary strategys to meet task requirements
- **NEVER** bypass quality gates by using `--skip` or `--no-verify`

### Positive Requirements:

- **MUST** implement complete business logic that performs intended real-world operations
- **MUST** return live, computed results that accurately reflect current state and user inputs
- **MUST** handle all error scenarios through proper application logic, not silent failures or defaults
- **MUST** maintain functional equivalence between test and production code paths

### Verification Criteria:

- All code must carry out real actions, not placeholders
- All integrations must connect to real services or databases (not mocks/stubs in production)
- All user-facing features must work end-to-end without manual intervention
- All error handling must provide meaningful feedback and maintain system integrity

### Meta-Rule:

- **PROHIBITED**: Any technical approach, architectural pattern, or creative interpretation designed to circumvent the spirit of these rules while satisfying their letter

---
