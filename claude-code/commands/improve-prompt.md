# Improve Prompt

## 1. Understanding the Codebase

- Use `mcp__serena__list_dir` to understand directory structure
- Use `mcp__serena__search_for_pattern` as your primary flexible tool to find patterns across the codebase
- Use `mcp__serena__get_symbols_overview` to understand file-level code structure
- Use `mcp__serena__find_symbol` for precise symbol location and analysis
- Prefer Serena MCP tools over generic file exploration for code-related searches

## 2. Context Preparation

- Read and understand the user's instructions and supplied context
- Use Serena tools to search for additional relevant files if current context is insufficient
- Keep analysis focused and token-efficient by using symbolic tools rather than reading entire files
- Use `mcp__serena__think_about_collected_information` after exploration phases

## 3. Clarification and Decision Making

When your analysis reveals unclear intentions or multiple valid approaches:

- **Ask clarifying questions** before proceeding with implementation
- Present discovered **architectural choices** and their trade-offs
- Highlight **ambiguous requirements** that need user input
- Offer **multiple implementation paths** when analysis uncovers alternatives
- **Stop and ask** rather than making assumptions about user preferences

Examples of when to seek clarification:

- Multiple similar patterns found with different approaches
- Existing code suggests conflicting architectural styles
- User request could be implemented in several valid ways
- Dependencies or constraints discovered that affect the approach
- Unclear scope or boundaries for the requested changes

## 4. Implementation Strategy

- Begin with a clear plan using TodoWrite to outline the implementation approach
- Use `mcp__serena__find_referencing_symbols` to understand code dependencies before making changes
- Maintain context throughout the task using Serena's symbolic analysis tools

**Code Analysis Limitations**:

- Always prefer symbolic tools over reading entire files
- Use `mcp__serena__get_symbols_overview` first, then targeted `mcp__serena__find_symbol` calls
- Leverage `mcp__serena__search_for_pattern` for cross-file pattern discovery

## 5. Mode Switching Guidelines

- **Start with Analysis** for: Understanding existing code structure and dependencies
- **Use Planning Tools** when: Multi-file changes, architectural decisions, complex logic design
- **Move to Implementation** when: Design is clear, dependencies understood, ready for specific changes
- **Return to Analysis** if: Implementation reveals design issues or missing dependencies

## 6. Error Handling & Recovery

- Use `mcp__serena__find_referencing_symbols` to understand impact before fixing errors
- If changes break references: Use symbolic tools to locate and update all affected code
- For failed implementations: Use `mcp__serena__search_for_pattern` to find similar patterns for guidance

## 7. Implementation Process

- Use `mcp__serena__think_about_task_adherence` before major code changes
- Specify exact symbol paths using `name_path` format for precise targeting
- Use `mcp__serena__replace_symbol_body` for clean symbol-level replacements
- Use `mcp__serena__insert_after_symbol` or `mcp__serena__insert_before_symbol` for additions

## 8. Output Template

Always output the complete improved prompt within XML tags for clarity:

```xml
<improved_prompt>
[Complete improved prompt here - include all original context, URLs, and resources]
</improved_prompt>
```

## 9. Resource Preservation Requirements

When processing the user's prompt in $ARGUMENTS:

1. **Extract Resources First**: Scan for and preserve all URLs, repository links, file paths, or specific examples mentioned
2. **Apply Improvement Principles**: Transform using the guidelines above while retaining all original context
3. **Validate Completeness**: Ensure no resources, requirements, or context are lost
4. **Output Cleanly**: Provide only the XML-wrapped improved prompt

## Key Requirements

- **Preserve ALL URLs and resources** mentioned in the original prompt
- **Maintain original intent** while applying improvements
- **Use Serena tools** for codebase-related analysis and understanding
- **Include clarification points** when ambiguity exists
- **Output complete prompt** within `<improved_prompt>` XML tags only

$ARGUMENTS
