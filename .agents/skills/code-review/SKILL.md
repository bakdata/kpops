---
name: code-review
description: Review code changes in this repository, such as a pull request or a branch against main. Use when asked to review changes.
---

# Code review

Find what should be fixed before merge: bugs, regressions, missed call sites, unhandled edge cases and security issues. Most of them sit outside the diff, in callers, shared code and tests. Also point out concrete improvements when they are clearly better, e.g. reusing an existing helper.

Only report what you verified in the code. Skip what linters, type checks and tests catch, style preferences, praise and summaries of the change. If nothing is worth raising, say so.

## Writing findings

Write like a colleague leaving a short review comment: direct, plain words, one to three sentences. State the problem and the concrete case where it breaks, then the fix. One finding per problem. No headings, bold titles or emoji.
