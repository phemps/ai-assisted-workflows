# Improve GPT-5 Prompt

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

```
<request>
[Refined request with clear objectives]
</request>

<instructions>
1. First, create a brief plan outlining your approach
2. Explain your reasoning for this approach
3. Execute the plan step by step
4. Validate each major output against requirements
5. Provide final summary confirming all objectives met
</instructions>

<constraints>
- Verbosity: [appropriate level]
- Style: [matched to use case]
- Format: [optimal structure]
</constraints>

[Additional spec blocks if needed]
```

## Special Considerations

- For ongoing context: "Be prepared to handle follow-up questions without losing context"
- For transparency: "Every so often, explain notable actions you're taking"
- For TODO tracking: Implement mental checklist structure
- For complex workflows: Use decomposition and validation checkpoints

$ARGUMENTS
