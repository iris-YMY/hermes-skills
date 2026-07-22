---
name: xhs-knowledge-base
description: |
  Xiaohongshu (XHS/小红书) structured knowledge base for social media operations. Defines 5 record
  types (account, topic, pattern, action, review), templates, naming conventions, search methodology,
  relevance scoring, and write rules. Enables persistent learning across content analysis, publishing,
  commenting, and viral copy tasks.
metadata:
  hermes:
    tags:
      - social-media
      - xiaohongshu
      - knowledge-management
      - persistent-memory
      - operations
---

# XHS Knowledge Base

This skill defines the core knowledge base capability: capture effective information from every analysis, topic ideation, publish, reply, and review into structured, searchable, reusable records.

The goal is NOT to store a pile of logs, but to let future decisions quickly answer three questions:
- How did we handle this type of content before?
- Which actions worked, which failed?
- What should we directly reuse next time?

## Knowledge Base Location

- Overview entry: `knowledge-base/README.md` (relative to this skill's directory)
- Record directories: `knowledge-base/accounts/`, `knowledge-base/topics/`, `knowledge-base/patterns/`, `knowledge-base/actions/`, `knowledge-base/reviews/`
- Git strategy: detailed records are saved locally only; `.gitignore` excludes accumulated md files, keeping only directory scaffolding and the overview entry in version control

## 0. Core Principles

- Only store "reusable information" — no running logs
- Prefer structured fields over long-form descriptions
- Conclusions must include evidence pointers: source notes, post URLs, screenshots, timestamps, action results
- Separate analysis results from action records — avoid mixing too many layers in one entry
- If KB is temporarily unwritable, complete the user task first, then return a structured summary for later entry

## 1. Directory & Data Structure

### 1.1 Directory Hierarchy

```
knowledge-base/
├── README.md          # Overview: current focus, fixed index, search hints
├── accounts/          # Account positioning, diagnostics, competitor analysis
├── topics/            # Topic candidates, controversy points, title skeletons, content directions
├── patterns/          # Viral structures, cover hierarchies, engagement mechanisms, reusable patterns
├── actions/           # Publish, reply, download, scrape, replicate operation records
└── reviews/           # Result reviews, failure reasons, rollback strategies, next corrections
```

### 1.2 Five Record Types

1. **`account`** — Account positioning, persona, content pillars, style constraints
2. **`topic`** — Topic candidates, applicable scenarios, controversy points, title templates
3. **`pattern`** — Reusable viral structures, engagement hooks, cover hierarchies, comment mechanisms
4. **`action`** — Specific operation records: analysis, publish, reply, download, replicate
5. **`review`** — Result reviews: what worked, what didn't, how to adjust next time

### 1.3 Common Fields (Every Record)

```yaml
id: 2026-03-19-confirmation-comment-hook
type: pattern
status: active  # active | deprecated | experimental
created_at: 2026-03-19T10:20:00+08:00
updated_at: 2026-03-19T10:45:00+08:00
source:
  kind: xhs_post  # xhs_post | notification | publish_flow | manual
  url: "https://www.xiaohongshu.com/explore/..."
  account: "Account Name"
  note_id: "optional"
summary: "One-line conclusion"
evidence:
  - "Screenshot or snapshot description"
  - "Key fields or page state"
tags:
  - drama-watch
  - title-hook
confidence: medium  # low | medium | high
next_action: "How to use this next time"
```

### 1.4 Type-Specific Fields

- **`account`**: `audience`, `content_pillars`, `tone_rules`, `red_lines`
- **`topic`**: `problem`, `angle`, `supporting_signals`, `risk_level`
- **`pattern`**: `title_template`, `cover_template`, `body_template`, `cta_template`, `fit_conditions`
- **`action`**: `task_type`, `input`, `steps_taken`, `result`, `blocker`
- **`review`**: `what_worked`, `what_failed`, `why`, `fix_next_time`

## 2. Record Templates

### 2.1 Analysis Record Template

For feed analysis, account analysis, topic ideation:

```markdown
---
id: 2026-03-19-taipingnian-argument-patterns
type: review
status: active
created_at: 2026-03-19T10:20:00+08:00
source_url: https://www.xiaohongshu.com/explore/...
account: Account Name
tags: [topic, hook, pattern]
---

# Conclusion
One sentence on the most important finding from this analysis.

# Evidence
- Key posts / accounts
- Key title or cover features
- Engagement signals

# Reusable Points
- Title template
- Cover structure
- Body rhythm
- Comment trigger words

# Risks
- Areas prone to violations
- Parts unsuitable for reuse

# Next Steps
- What to directly reuse next time
- What to avoid next time
```

### 2.2 Action Record Template

For publish, reply, download, scrape, replicate operations:

```markdown
---
id: 2026-03-19-publish-taipingnian-note
type: action
status: active
created_at: 2026-03-19T10:30:00+08:00
task_type: publish
input: "Drama discussion topic"
result: success
---

# Action
What was done, 3-5 items in chronological order.

# Result
Success / Failure / Partial success.

# Key Blockers
If failed, which step was the blocker.

# Reuse Recommendations
How to prioritize for similar tasks next time.
```

### 2.3 File Naming Convention

For easy agentic search, name detailed records as "date + brief":

```
knowledge-base/accounts/2026-03-19-drama-watch-positioning.md
knowledge-base/topics/2026-03-19-taipingnian-argument-hooks.md
knowledge-base/patterns/2026-03-19-confirmation-comment-hook.md
knowledge-base/actions/2026-03-19-publish-taipingnian-note.md
knowledge-base/reviews/2026-03-19-reply-flow-retrospective.md
```

**Naming rules:**
- Date first for chronological sorting
- Brief should include account name, topic keywords, action words, or conclusion words
- One file = one core conclusion or one complete action

## 3. Update Timing

Write to KB at these checkpoints:

1. **Before task** — Read `knowledge-base/README.md`, search historical records to avoid repeating mistakes
2. **During task** — When new conclusions, structures, cover templates, or risk signals appear, record a temporary entry immediately
3. **After task** — After completing analysis, publish, reply, or replication, write the results
4. **After failure** — Failure reasons, rollback strategies, and alternative paths must be recorded separately
5. **Periodic review** — Merge temporary records into stable patterns; downgrade or deprecate expired content

## 4. Search Methodology

Goal: "quickly find something directly usable", not blind full-text searching.

### 4.1 Recommended Search Dimensions

- By account: `account = xxx`
- By topic: `tags contains drama-watch`
- By type: `type = pattern | review | action`
- By status: `status = active`
- By risk: `risk_level = high`
- By result: `result = success` or `blocker exists`

### 4.2 Recommended Search Order

1. Read `knowledge-base/README.md` "Current Focus" and "Fixed Index"
2. Find similar records from the last 7-14 days
3. Find records for the same account, same topic
4. Find same-structure patterns
5. Finally check historical failure records

### 4.3 Relevance Scoring

When multiple records match, prioritize by:
- **Recency** (last 7 days > last 30 days > older)
- **Status** (`active` > `experimental` > `deprecated`)
- **Confidence** (`high` > `medium` > `low`)
- **Direct applicability** (same topic > similar topic > related topic)
- **Result quality** (`success` > `partial` > `failure`)

### 4.4 Return Format

Search results should return:
- Match count
- Top 3 most relevant entries
- Reusable points from each
- Recommended actions for current task

## 5. Write Rules

- One record addresses one problem only
- Conclusions must be actionable — avoid vague statements like "felt good"
- Evidence: prefer summaries, don't preserve large blocks of original text
- When duplicate entries appear, update old entries first, then add new ones
- Mark verified-ineffective patterns as `deprecated` — don't delete them

## 6. Failure Degradation

If KB is unavailable or write fails:

1. Complete the current user task first — don't block the main flow
2. Return a structured summary containing at minimum:
   - Conclusion
   - Evidence
   - Action
   - Risk
   - Next step
3. Mark this record as pending write
4. If write fails twice consecutively, stop attempting; notify user that KB storage is currently unavailable
5. If only subdirectory writes fail but `knowledge-base/README.md` is writable, append the summary to the overview's "Pending" section

If search fails:

1. Fall back to current session context
2. Use the most recent analysis result as temporary knowledge
3. Mark "KB not hit" to avoid falsely assuming no history exists

## 7. Integration with Other Skills

This knowledge base serves as the persistent memory layer for the entire XHS operations ecosystem:

| Skill | Primary KB Usage | Record Types |
|-------|-----------------|--------------|
| **xhs-viral-copy** | Viral structure analysis, cover patterns, rewrite results | `pattern`, `review` |
| **xhs-publish** | Publish success/failure records, error handling patterns | `action`, `review` |
| **viral-video-studio** | Video content patterns, script structures, engagement hooks | `pattern`, `topic` |
| **social-account-doctor** | Account diagnostics, positioning analysis, competitor benchmarks | `account`, `review` |
| **xhs-writer** (if exists) | Writing style patterns, tone rules, body templates | `pattern`, `account` |

### Cross-Skill KB Workflow

1. **xhs-viral-copy** analyzes a viral note → writes `pattern` record
2. **social-account-doctor** reviews account health → writes `account` record
3. **xhs-publish** publishes content → writes `action` record
4. After 24-48h → write `review` record with engagement results
5. Next **xhs-viral-copy** run reads all above before generating new content

## 8. Minimum Executable Output

When KB results need to be presented directly to the user:

1. `Conclusion` — What we learned
2. `Reusable Rules` — What to apply
3. `Risk Points` — What to avoid
4. `Next Action` — What to do next

This ensures analysis results are both human-readable and consumable by downstream skill flows.
