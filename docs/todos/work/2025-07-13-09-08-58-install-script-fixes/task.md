# install script fixes: check whether the .claude folder is included in the user specified folder (use that as target instead of creating .claude folder) and verify install doesn't lose existing commands

**Status:** Refining
**Created:** 2025-07-13T09:08:58
**Agent PID:** 36629

## Original Todo
install script fixes: check whether the .claude folder is included in the user specified folder (use that as target instead of creating .claude folder) and verify install doesn't lose existing commands

## Description
The install script has two issues that need to be fixed:

1. **Path handling issue**: When users specify a target path that already ends with `.claude` (e.g., `./install.sh /path/to/.claude`), the script incorrectly creates a nested `.claude/.claude` directory instead of using the provided path directly.

2. **Preserving existing commands**: While the script has a "merge mode" that uses `cp -rn` to avoid overwriting files, we need to verify this works correctly for custom command files that users may have added to their `.claude/commands/` directory.

The fixes will ensure that:
- If a user specifies a path ending with `.claude`, that exact path is used as the installation directory
- User's custom commands are preserved during updates/reinstalls when merge mode is selected

## Implementation Plan
- [ ] Add path checking logic to prevent .claude/.claude nesting (install.sh:242)
- [ ] Add automatic backup of existing .claude directory before any installation (install.sh:245-250)
- [ ] Update user prompts to inform about automatic backup (install.sh:260-265)
- [ ] Modify the merge mode to show which files are being preserved (install.sh:351)
- [ ] Add verification that custom commands are preserved after installation (install.sh:380-390)
- [ ] Automated test: Test path handling with various input paths
- [ ] Automated test: Test backup creation and restoration
- [ ] User test: Run install with path ending in .claude
- [ ] User test: Run install update and verify custom commands preserved

## Notes