---
name: consulting-deck-strategist
description: Plan hypothesis-led business consulting decks before production. Use only when a request involves strategy, market, growth, investment, operating-model, or management analysis and needs an evidence-backed storyline, issue tree, claim-evidence map, or page blueprint. Do not use for routine PPT creation, formatting, template filling, visual redesign, or editing. Hand the resulting blueprint to ppt-master (or rw-consulting-ppt for full-slide images) for production.
---

# Consulting Deck Strategist

Structure the business argument before slide production. Own problem framing, hypotheses, evidence boundaries, and page logic; never own PPTX implementation.

## Workflow

1. Infer the decision, audience, scope, evidence, and intended use from supplied context. Ask only when a missing choice would materially change the argument.
2. State one decision question and a provisional answer or set of competing hypotheses.
3. Build a compact MECE issue tree. Prioritize branches that could change the decision.
4. Classify material claims as fact, calculation, hypothesis, scenario, constraint, or recommendation.
5. Create a claim-evidence map and mark missing or insufficient evidence. Never render a hypothesis as established fact.
6. Create a page blueprint ordered by argument dependency. Give every page one action title, one narrative job, one proof object, and an explicit evidence boundary.
7. Continue directly when the requested direction is clear. Request confirmation only for a material unresolved choice such as mutually exclusive storylines or delivery formats.
8. Hand the settled blueprint, source ledger, calculations, brand direction, and editing requirements to `ppt-master` for production. If the user explicitly requires full-slide images with no editable objects, hand off to `rw-consulting-ppt` instead (it owns the full-slide-image route and uses image_gen for images, PPTX packaging, and QA).

## Routing Boundary

- Use `ppt-master` alone for routine creation, editing, template filling, redesign, rendering, or QA.
- Use this Skill before ppt-master only for hypothesis-led consulting or management analysis.
- If the user explicitly requires full-slide images with no editable objects, use `rw-consulting-ppt` for the full-slide-image route (images via image_gen, PPTX packaging and QA included). Do not create another PPT production workflow.
- Hand off to `ppt-master`, `ppt-workflow`, or `rw-consulting-ppt` as production owners — this skill never owns PPTX implementation. Final output passes `ppt-production-qa` before formal delivery.

## Reference

Read [references/consulting-blueprint.md](references/consulting-blueprint.md) when building the issue tree, claim-evidence map, blueprint, or final argument QA.
