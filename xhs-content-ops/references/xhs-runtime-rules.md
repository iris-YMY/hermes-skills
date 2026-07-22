# XHS Runtime Rules (Hermes Browser Adapted)

These rules govern browser automation behavior during all XHS operations. They are adapted from the original runtime rules for use with Hermes browser tools.

## 0.1 Token & Snapshot Constraints

- Prefer `browser_console` for targeted data extraction over full-page dumps
- Only take `browser_snapshot` at key checkpoints:
  - Login confirmation
  - Arriving at publish page
  - After filling content
  - Pre-publish pause point
- Avoid `fullPage` snapshots unless user requests full-page archival
- Reuse same tab/session — don't repeatedly open new tabs
- Each action retries at most **once**; on second failure, switch to stable path and report
- Record key evidence: account name, page state, button visibility, character counts; return actionable signals

## 0.2 Browser Stability Rules (Highest Priority)

- Use Hermes browser tools exclusively:
  - `browser_navigate` — open URLs
  - `browser_snapshot` — capture page state
  - `browser_console` — execute JavaScript
  - `browser_click` — click elements
  - `browser_type` — input text
- Before each action, confirm the target tab is active and connected
- If `no tab is connected` or similar errors appear:
  1. Re-navigate to the target URL
  2. Take a `browser_snapshot` to verify connection
  3. Retry the failed action once
- After **2 consecutive** click/navigation failures:
  - Switch to stable path (e.g., use `browser_console` with DOM queries instead of direct `browser_click`)
  - Never blind-retry the same failing action
- Maintain awareness of current page URL at all times

## 3.5 Search & Browse Core Constraints

1. **Only enter posts from search results page** — never navigate directly to `/explore/<id>`
   - Exception: when user provides a specific URL for viral copy analysis
2. **Default: skip own account's content** (avoid self-browsing detection)
3. After entering a post, verify:
   - Not a 404 page
   - Comments/engagement info visible
   - Title or author identifiable
4. **Entry method:** Click card body, avoid clicking avatar/author name (prevents wrong page navigation)
5. If comment input is `contenteditable` or `p.content-input`:
   - Use `browser_console` to trigger proper input events (input, change) before attempting send
6. After **two click failures or 404s** on the same link:
   - Return to search page
   - Try next result
   - Don't retry the same failed link

## 6.0 Recovery & Degradation

- **If search page structure changes:**
  - Take `browser_snapshot` to update selectors
  - Identify new element structure before continuing
  - Don't blindly run old selector paths

- **Tab reuse:**
  - Key pages (creator page, explore page, user page) — reuse already-open tabs
  - Don't repeatedly `browser_navigate` to the same page

- **Anomaly handling:**
  - Before proceeding past an anomaly, tell user: "reached exception point"
  - Avoid meaningless continued operations that could cause accidental publishing

- **Publish page critical action failures:**
  1. `browser_snapshot` to refresh element references
  2. Retry same action at most once more
  3. If still failing: switch to stable path
     - Try alternative entry point (different tab/button for same action)
     - As last resort: prompt user to manually click the final action button

- **Carousel image extraction:**
  - **NEVER** take first `.img-container` (often gets wrong/duplicate slide)
  - **Always** use: `.swiper-slide-active:not(.swiper-slide-duplicate) .img-container img`
  - Fallback: `.swiper-slide-active .img-container img`
  - After extraction, verify URL key segment matches expected cover
    - Example: check for `.../1040g3k...` pattern in URL
    - If mismatch, re-extract from active slide

- **Image generation similarity check:**
  - If user reports generated image elements are "too similar" to source:
    - Switch to style-only prompt immediately
    - Regenerate with divergent visual elements
    - Don't argue with user's assessment

- **File upload:**
  - Ensure files are in accessible temporary path (e.g., `/tmp/hermes-uploads/`)
  - Copy files to temp path before attempting upload
  - Verify file exists before upload attempt

## Error Recovery Decision Tree

```
Action fails
├── First failure → Retry same action once
│   ├── Succeeds → Continue
│   └── Fails again → Stable path
│       ├── browser_console alternative → Continue
│       ├── Alternative entry point → Continue
│       └── All alternatives fail → Report to user, await instructions
├── Network error → Wait 5s, retry navigation
│   ├── Succeeds → Continue
│   └── Fails → Report to user
└── Rate limit detected → STOP immediately, report to user
```
