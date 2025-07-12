# Review the following command files with the user to see if they are fit for purpose and potentially discard or make improvements: build-feature, build-plan, plan-architecture, plan-datamodel, plan-feature, plan-refactor

**Status:** In Progress
**Started:** 2025-07-12T16:49:30
**Created:** 2025-07-12T16:44:09
**Agent PID:** 738

## Description
Review command files for fitness and make improvements. Focus on transforming plan-architecture to plan-solution using solution-design.md methodology - changing from generic workflow to specific technical challenge solving with investigation, research, and 3 solution options.

## Implementation Plan
- [x] **Analyze current command overlap and issues** - Identified 70% overlap between plan-feature/build-feature, and generic workflows vs problem-solving approach
- [x] **Rename plan-architecture.md to plan-solution.md** - Better reflects problem-solving focus vs generic architecture planning
- [x] **Redesign plan-solution with solution-design methodology** - Transform to user challenge → investigation → 3 options → recommendation workflow
- [x] **Integrate existing analysis scripts appropriately** - Keep pattern_evaluation.py, scalability_check.py, coupling_analysis.py as context for solution design
- [x] **Update README.md command references** - Change plan-architecture to plan-solution in documentation
- [ ] **Test new workflow structure** - Verify the solution-design approach works effectively
- [ ] **User review**: Validate the transformed command meets expectations

## Notes
- Successfully renamed and completely redesigned plan-architecture to plan-solution
- Transformed from generic architecture planning to specific technical challenge solving
- Integrated solution-design.md methodology: context gathering → current system analysis → research → 3 solutions → comparative analysis → recommendation
- Retained existing analysis scripts as valuable context for understanding current system
- Updated README.md to reflect new command name and purpose
- New approach follows investigative consultant model rather than prescriptive workflow

## Original Todo
Review the following command files with the user to see if they are fit for purpose and potentially discard or make improvements:
  build-feature
  build-plan
  plan-architecture
  plan-datamodel
  plan-feature
  plan-refactor