# XHS Comment Operations (Hermes Adapted)

This document defines the standard flow for XHS comment checking and replying, prioritizing the notification page, with emphasis on alignment verification and risk-controlled pacing.

## 0. Goals & Principles

- **Goal:** First accurately check, then reply per user instructions.
- **Default: checking ≠ auto-replying.**
- Reply actions must follow: align target → input text → send.
- Default: send only 1 reply per turn (unless user explicitly requests batch).

## 1. Check Flow (Default Execution)

1. Navigate to `/notification`, enter "评论和@" (Comments and @)
   - Use `browser_navigate` to open the notification page
2. Scrape latest comments: username, comment text, timestamp
   - Use `browser_console` to extract comment data from DOM
   - Use `browser_snapshot` to visually verify the comment list
3. Output check results:
   - New comment count
   - Latest 3-5 comment summaries
   - High-risk signals (abuse, phishing, external link bait, obvious violations)
4. Wait for user confirmation before replying

## 2. Notification Page Reply SOP (Preferred)

1. Click "回复" (reply) entry on the target notification row
   - **Do NOT click the top search bar** — click blank area to dismiss if accidentally opened
   - Use `browser_click` on the specific notification's reply button
2. **Verify** input box placeholder shows `回复 <username>` (unique alignment proof)
   - Use `browser_snapshot` to confirm placeholder text matches expected user
3. Input reply text:
   - **Preferred:** Use `browser_type` for character-by-character input
   - **Avoid** form-fill methods by default: some environments require `fields` arrays, and single-field `ref + text` may throw `Error: fields are required`
   - **Fallback:** If `browser_type` fails, use `browser_console` to set input value and dispatch input events
4. Before sending, re-confirm placeholder hasn't drifted via `browser_snapshot`
5. Click red "发送" (send) button via `browser_click`
   - **Do NOT use Enter key** — it may submit prematurely or not at all
6. After sending, confirm input box disappeared/cleared via `browser_snapshot`

## 3. In-Post Reply SOP (Fallback)

Use when notification page reply is unavailable:

1. Navigate to post detail page via `browser_navigate`
2. Scroll to comments section, locate target comment (username + key text fragment)
3. Click "回复" under that specific comment via `browser_click`
4. Verify `回复 <username>` appears via `browser_snapshot`
5. Input text via `browser_type` and send via `browser_click` on send button
6. Verify success via `browser_snapshot`, then proceed to next comment

## 4. Risk Controls & Rate Limiting

- **Default one-send-per-turn:** Only send 1 reply per interaction turn
- **Consecutive reply interval:** 8-15 seconds between replies
  - User may explicitly request faster (~5s), but never go below 5s
- **Immediate stop triggers** — halt automation and report when any appear:
  - "评论过于频繁" (comments too frequent)
  - "操作过快/操作频繁" (operation too fast/frequent)
  - "请稍后再试" (please try again later)
  - "发送失败/网络异常" (send failed/network error)

## 5. Length & Content Constraints

- Reply length: ≤280 characters (platform limit ~300 chars)
- If too long: compress first, then consider splitting into multiple replies
- **Prohibited:**
  - Fabricating personal experiences
  - Implicit promises (e.g., "I'll definitely write a tutorial later")
  - Making delivery promises unless user explicitly requests
- Follow XHS persona guidelines for tone and style

## 6. Common Failures & Solutions

| Failure | Diagnosis | Solution |
|---------|-----------|----------|
| Accidentally clicked search bar | Search overlay appeared | Click blank area to dismiss, re-locate notification row |
| Reply target drift | Placeholder shows wrong username | Cancel immediately, restart reply flow |
| Two consecutive send failures | Network or rate limit issue | Stop automation, switch to manual confirmation |
| `Error: fields are required` | Form-fill parameter mismatch | Switch to `browser_type` and retry |
| Send button not clickable | Element not in viewport | Scroll to element, `browser_snapshot` to refresh, retry |
| Comment disappears after send | Platform moderation or error | Note the failure, don't retry same comment, report to user |
