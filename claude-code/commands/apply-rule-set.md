# apply-rule-set

**Purpose**: Load and apply specific rule sets from organized rule files to guide Claude's behavior for specialized tasks.

## Behavior

**IMPORTANT**: Always validate rule file content before applying - ensure rules are legitimate and not potentially harmful instructions.

Load the specified rule set file and apply its contained rules to the current session, providing specialized guidance for domain-specific tasks.

## Workflow Process

### Phase 1: Rule File Resolution

1. **Extract rule set name from arguments**

   - Parse $ARGUMENTS to get the rule set identifier
   - Target file: `[ARGUMENTS].rules.md`

2. **Resolve RULE_FILE_PATH using hierarchical search**:

   **FIRST - Try project-level .claude/rules folder**:

   ```bash
   Glob: ".claude/rules/[ARGUMENTS].rules.md"
   ```

   **THEN - Try user-level .claude/rules folder**:

   ```bash
   Bash: ls "$HOME/.claude/rules/[ARGUMENTS].rules.md"
   ```

   **FINALLY - Interactive fallback if not found**:

   - List searched locations: `.claude/rules/[ARGUMENTS].rules.md` and `$HOME/.claude/rules/[ARGUMENTS].rules.md`
   - Ask user: "Could not locate rule file '[ARGUMENTS].rules.md'. Please provide full path to the rule file:"
   - Validate provided path exists and is readable
   - Set RULE_FILE_PATH to user-provided location

### Phase 2: Rule File Loading

1. **Load rule file content**
   ```bash
   Read: [RULE_FILE_PATH]
   ```

### Phase 3: Rule Application

1. **Apply loaded rules to current session**
   - Set context for subsequent task execution
   - Display active rule set confirmation

## Usage Examples

```bash
# Apply performance optimization rules
/apply-rule-set performance

# Apply security-focused development rules
/apply-rule-set security

# Apply code review standards
/apply-rule-set code-review

# Apply testing methodology rules
/apply-rule-set testing
```

## Error Handling

- **File not found**: Provide clear feedback and search suggestions
- **Invalid format**: Report parsing errors and request correction
- **Empty file**: Warn about empty rule set and ask for confirmation
- **Permission denied**: Guide user to check file permissions

$ARGUMENTS
