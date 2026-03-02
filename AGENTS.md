# AGENTS.md

This file defines the working contract for contributors and coding agents in this repository.

## Scope
- Keep all changes minimal and focused on the requested task.
- Do not modify unrelated files or behavior without explicit approval.
- Do not remove or revert user changes unless explicitly requested.

## Language
- Use English for code, comments, logs, config, UI strings, and commit messages.
- Use Traditional Chinese (Taiwan) for planning/explanations in assistant responses.

## Default Flow
Follow this order unless the user explicitly allows otherwise:
1. Clarify
2. Plan
3. TDD
4. Implement
5. Summary

If TDD is not applicable (for example CI/workflow/docs-only changes), state why and provide deterministic verification steps.

## Security Rules (Always On)
- Never hardcode secrets, tokens, credentials, or environment-specific sensitive data.
- Use environment variables or secret managers only.
- Validate external inputs.
- Do not swallow errors silently.
- Do not log secrets or PII.
- Do not run experiments directly in production.

## Backend/API Rules (When Applicable)
- Keep API changes backward compatible unless explicitly approved.
- Return stable error shape with `trace_id` for API failures:
```json
{
  "error": "Human readable message",
  "code": "ERR_xxx",
  "trace_id": "uuid-v4"
}
```

## UI/UX Rules (When Applicable)
- Do not alter user-facing interaction patterns without explicit intent.
- Handle loading, empty, error, disabled, and success states.
- Keep user messages clear and non-technical.
- Avoid layout shifts and accessibility regressions.

## File Handling Rules
- Check file size first (`wc -l`) before reading.
- Use partial reads (`rg`, `sed`, `jq`, `yq`) for large files.
- Do not dump large files blindly.

## Testing Rules
- Prefer deterministic and isolated tests (Arrange, Act, Assert).
- For UI/manual checks, verify:
  1. Functionality
  2. UI/UX states and feedback
  3. Regressions
- For backend/API changes, verify response schema, error code, and `trace_id`.

## Release and Publish (Desktop Binaries)
- GitHub Actions workflow: `.github/workflows/release-desktop.yml`
- Trigger paths:
  - Push a tag that starts with `v` (example: `v0.1.0`)
  - Manual workflow dispatch with an existing tag input
- Build targets:
  - Linux (`ubuntu-24.04`)
  - macOS (`macos-latest`)
- Output:
  - Tauri-generated release assets are uploaded to the matching GitHub Release.

Recommended publish flow:
1. Commit changes to `main`.
2. Create a release tag: `git tag vX.Y.Z`.
3. Push branch and tag: `git push origin main --follow-tags`.

## Rollback Guidance
- Revert the specific commit that introduced the workflow/config changes.
- Avoid destructive git commands unless explicitly approved.
