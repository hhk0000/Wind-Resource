# Project collaboration instructions

This repository contains a Chinese wind-resource analysis platform in its requirements/design phase. The user wants ongoing collaborative GUI development and remote Git version management.

- Read README.md, docs/设计方案.md, docs/架构文档.md, and docs/协作与版本管理.md before substantial changes.
- Use this existing checkout. Do not create Git worktrees unless the user explicitly requests one.
- Preserve different proposed designs using named design branches and immutable published tags. Keep main usable; do not force-push or move published tags.
- Ordinary user-requested changes may be implemented and pushed without asking the same permission again. Preserve pre-existing work and avoid unrelated edits.
- Keep the GUI's white rounded style unless the user changes direction. Distinguish synthetic examples, local real-file results, and unimplemented production functions.
- Never claim cloud upload, engineering calculations, compliance decisions, or DOCX report generation works until actually implemented and tested.
- Do not commit uploaded customer files, confidential measurement data, credentials or .env. gh-pages must contain only gui/ public assets.
- For GUI changes update gui/version.json, CHANGELOG.md and any affected usage instructions. Rebuild optional offline HTML using python tools/export_standalone.py.
- Run node --check gui/app.js. For interaction changes start Python's static server and run tests/smoke.py using the existing Playwright/Chromium tools when available. Tests regenerate tracked screenshots; inspect whether the changes are expected before committing.
- main GUI changes trigger the publish-gui workflow, which updates gh-pages with normal non-forced commits. Confirm push separately from actual Pages deployment; do not describe an unverified expected URL as live.
- Report concise Chinese outcomes, tested behavior, remaining limitations and the relevant commit/version so the user can continue giving feedback.
