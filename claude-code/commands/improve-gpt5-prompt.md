---
argument-hint: <prompt-text>
---

# Improve GPT-5 Prompt

This command takes a user's initial request and transforms it into a sophisticated GPT-5 prompt that leverages advanced reasoning patterns, structured thinking, and comprehensive planning phases. The resulting prompt will be more likely to produce thorough, accurate, and well-structured responses.

## Process Overview

Transform the user's prompt in $ARGUMENTS into an optimized GPT-5 prompt following these steps:

## 1. Apply Core GPT-5 Principles

- Add explicit style instructions for tone, verbosity, and format
- Include planning phase with pre-execution reasoning
- Use consistent structure and formatting
- Define all parameters and expectations clearly

## 2. Implement Structured Format

Convert to spec format when appropriate:

```
<task_spec>
  Definition: [Core task extracted from original prompt]
  When Required: [Conditions for execution]
  Format & Style: [Output structure requirements]
  Sequence: [Step-by-step operations]
  Prohibited: [What to avoid]
  Handling Ambiguity: [How to handle unclear inputs]
</task_spec>
```

## 3. Add Reasoning and Validation Layers

```
Before responding, please:
1. Decompose the request into core components
2. Identify any ambiguities that need clarification
3. Create a structured approach to address each component
4. Validate your understanding before proceeding
```

## 4. Enable Agentic Behavior

For complex tasks:

```
Remember: Continue working until the entire request is fully resolved.
- Decompose the query into ALL required sub-tasks
- Confirm each sub-task is completed before moving on
- Only conclude when you're certain the problem is fully solved
```

## 5. Optimize for Task Type

**Research/Analysis**:

- Add comprehensive data gathering phase
- Include structured findings format
- Require summary of key insights

**Creative Work**:

- Establish tone/style parameters upfront
- Require outline before execution
- Add consistency review step

**Problem-Solving**:

- Include multiple solution generation
- Add pros/cons evaluation
- Require justified recommendation

**Educational Content**:

- Add audience assessment
- Structure from foundational to advanced
- Include understanding checkpoints

## 6. Add Parallel Processing When Beneficial

```
Process these tasks in parallel:
- [Independent task 1]
- [Independent task 2]
Note: Only serialize tasks with dependencies
```

## 7. Include Error Prevention

```
Before providing your final response:
1. Verify all requirements have been addressed
2. Check for internal consistency
3. Ensure output format matches specifications
4. Confirm no prohibited elements are included
```

## Output Template

Always output the complete optimized prompt within XML tags for clarity:

```xml
<optimized_prompt>
[Complete GPT-5 optimized prompt here - include all original context, URLs, and resources]
</optimized_prompt>
```

## Implementation Steps

When processing the user's prompt in $ARGUMENTS:

1. **Extract Resources First**: Scan for and preserve all URLs, repository links, file paths, or specific examples
2. **Apply GPT-5 Structure**: Transform using the principles above while retaining all original context
3. **Validate Completeness**: Ensure no resources or requirements are lost
4. **Output Cleanly**: Provide only the XML-wrapped optimized prompt

## Key Requirements

- **Preserve ALL URLs and resources** mentioned in the original prompt
- **Maintain original intent** while applying GPT-5 improvements
- **Use structured format** with clear sections and instructions
- **Include validation steps** for comprehensive responses
- **Output complete prompt** within `<optimized_prompt>` XML tags only

$ARGUMENTS
