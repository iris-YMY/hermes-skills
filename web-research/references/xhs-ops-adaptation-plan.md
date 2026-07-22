# Xiaohongshu-Ops-Skill → Hermes Agent Adaptation Plan

**Source:** https://github.com/Xiangyu-CAS/xiaohongshu-ops-skill (2,103 ⭐)
**Analyzed:** 2026-07-13
**Status:** ✅ EXECUTED 2026-07-13 — All skills installed and adapted. See below for installed skill inventory.

### Installed Skills (Result)

| Skill | Path | Files | Source |
|-------|------|-------|--------|
| `social-account-doctor` | `social-media/social-account-doctor/` | 38 | JuneYaooo/social-account-doctor (GitHub) |
| `viral-video-studio` | `social-media/viral-video-studio/` | 6 | SinKry/viral-video-studio-skill (GitHub) |
| `xhs-viral-copy` | `social-media/xhs-viral-copy/` | 2 | Extracted from xiaohongshu-ops `references/xhs-viral-copy-flow.md` |
| `xhs-knowledge-base` | `social-media/xhs-knowledge-base/` | 7 | Extracted from xiaohongshu-ops `references/xhs-knowledge-base.md` |
| `xhs-publish` | `social-media/xhs-publish/` | 3 | Extracted from xiaohongshu-ops `references/xhs-publish-flows.md` |
| `xhs-writer` | `social-media/xhs-writer-skill/` | 26 | JuneYaooo/xhs-writer-skill (GitHub) |
| `humanizer` | `creative/humanizer/` | existing | Pre-installed |

### OpenClaw → Hermes Tool Mapping (Applied)
- `profile="openclaw"` → removed (Hermes needs no profile)
- `evaluate` → `browser_console`
- `snapshot` → `browser_snapshot`
- `type`/`fill` → `browser_type`
- `browser.upload` → `browser_click` + temp path
- `clawhub install` → removed
- Nano Banana image gen → `gpt-image-2`
- All 3 adapted skills verified: 0 OpenClaw references remaining

---

## Executive Summary

The `xiaohongshu-ops-skill` is designed for **OpenClaw** (a different AI agent platform), NOT Hermes Agent. This plan describes how to adapt it into two deliverables:

### Deliverable A: New standalone skill `xhs-ops`
Browser-based XHS platform operations (account diagnostics, feed analysis, comment ops, publishing, knowledge base)

### Deliverable B: Enhance existing `xhs-writer-skill`
Transfer persona.md + topic ideation as pre-generation references

---

## A. OpenClaw-Specific Parts (Remove/Replace — ~35 references)

### A.1 Browser Profile
| Location | OpenClaw Pattern | Hermes Equivalent |
|----------|-----------------|-------------------|
| SKILL.md, runtime-rules, account-analysis, feed-analysis | `profile="openclaw"` | Remove; Hermes uses `browser_navigate` without profiles |

### A.2 Tool References
| OpenClaw Tool | Hermes Equivalent |
|--------------|-------------------|
| `evaluate` (JS execution) | `browser_console` |
| `snapshot` (page state) | `browser_snapshot` |
| `type`/`fill` | `browser_type` |
| `browser.upload` | `browser_click` on upload element |
| `clawhub install` | Remove; use Hermes skill management |

### A.3 Files to Delete Entirely
- `Openclaw一键安装.md` (172 lines, irrelevant)

---

## B. High-Value Transferable Parts (Keep As-Is)

### B.1 Analytical Frameworks ⭐
| Framework | File | Transferability |
|-----------|------|-----------------|
| Account Analysis (5-dim scoring) | xhs-account-analysis.md | 100% |
| Home Feed Analysis | xhs-home-feed-analysis.md | 95% |
| Topic Ideation | xhs-topic-ideation.md | 100% |
| Viral Copy Flow | xhs-viral-copy-flow.md | 90% |

### B.2 Knowledge Base System ⭐
- 5 record types, templates, naming conventions
- Directory structure: accounts/, topics/, patterns/, actions/, reviews/
- Search methodology with priority-ordered retrieval

### B.3 Persona System
- persona.md: XHS-specific voice (傲娇嘴硬型), anti-social-engineering rules
- Reply structure: 接梗 → 立场 → 有用一句 → 收尾

### B.4 Operational SOPs
- Comment operations with risk controls and rate limiting
- Publishing flow (4 types, pre-publish checklist)
- Runtime rules (search constraints, degradation patterns)

---

## C. Merge Analysis vs Existing Skills

### vs `xhs-writer-skill`
- **Overlap**: ~25% (title formulas, content structure)
- **Verdict**: Complementary — writer makes content, ops runs the platform
- **Action**: Transfer persona.md + topic-ideation.md into xhs-writer

### vs `viral-video-studio`
- **Overlap**: ~15% (different media types)
- **Verdict**: Keep separate

### vs `humanizer`
- **Overlap**: ~5%
- **Verdict**: Keep separate; they work in sequence (generate → humanize → persona)

---

## D. Proposed Final Structure

```
social-media/
├── xhs-writer-skill/          # Enhanced with persona + topic ideation
│   ├── persona.md             # NEW from xiaohongshu-ops
│   ├── references/
│   │   ├── xhs-topic-ideation.md  # NEW from xiaohongshu-ops
│   │   ├── reply-examples.md      # NEW from xiaohongshu-ops
│   │   └── ... (existing)
│
├── xhs-ops/                   # NEW standalone skill
│   ├── SKILL.md               # Adapted (Hermes browser tools)
│   ├── references/
│   │   ├── xhs-account-analysis.md
│   │   ├── xhs-home-feed-analysis.md
│   │   ├── xhs-comment-ops.md
│   │   ├── xhs-publish-flows.md
│   │   ├── xhs-viral-copy-flow.md
│   │   ├── xhs-knowledge-base.md
│   │   ├── xhs-runtime-rules.md   # MAJOR REWRITE
│   │   └── xhs-eval-patterns.md   # MAJOR REWRITE
│   ├── knowledge-base/
│   └── examples/
│
└── viral-video-studio/        # Unchanged
```

## E. Rewrite Priority

| Priority | File | Effort |
|----------|------|--------|
| 🔴 P1 | xhs-runtime-rules.md | Complete rewrite |
| 🔴 P1 | SKILL.md | Remove OpenClaw, adapt startup |
| 🔴 P1 | xhs-eval-patterns.md | Adapt for browser_console |
| 🟡 P2 | xhs-account-analysis.md | Remove profile refs |
| 🟡 P2 | xhs-home-feed-analysis.md | Remove profile refs |
| 🟡 P2 | xhs-comment-ops.md | type/fill → browser_type |
| 🟡 P2 | xhs-publish-flows.md | Remove clawhub, fix paths |
| 🟢 P3 | xhs-topic-ideation.md | Near-zero changes |
| 🟢 P3 | xhs-viral-copy-flow.md | Replace Nano Banana ref |
| 🟢 P3 | xhs-knowledge-base.md | No changes |
| 🟢 P3 | persona.md | No changes |

## F. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| XHS web UI changes break selectors | High | Keep selectors in runtime-rules, not hardcoded |
| Hermes browser lacks persistent login | Medium | First-run QR scan; session cookies |
| Anti-bot detection | High | Keep rate limits + random delays |
| Nano Banana replacement | Medium | Use gpt-image-2 from xhs-writer |
