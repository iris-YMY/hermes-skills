# Render Review Rubric

Review slide renders, not only object coordinates. Inspect each slide at full size and inspect a montage for deck-level rhythm.

## 1. Hard failures

Fix every occurrence before showing a draft:

- clipped, overflowing, missing, or unexpectedly wrapped text;
- unintended overlap or an object outside the canvas;
- broken, blurry, stretched, or severely mis-cropped image;
- unreadable contrast or text directly on a busy image without protection;
- unresolved placeholder or inconsistent template residue;
- chart labels, categories, values, or visual marks that disagree with source data;
- title intended as one line wrapping to multiple lines.

## 2. Composition failures

Fix when clearly present:

- no obvious focal point, or several elements compete equally;
- primary image is too small to perform its intended role;
- text block dominates an image-led slide without narrative reason;
- excessive density solved by shrinking type instead of editing content;
- empty space has no compositional purpose;
- page weight is visibly biased without intentional tension;
- caption is detached from its image or chart;
- aligned elements drift from their shared grid;
- repeated components have visibly inconsistent spacing or size;
- neighboring slides repeat the same silhouette mechanically;
- decorative vocabulary makes the slide resemble a web UI rather than a presentation.

## 3. Measurable checks

Use these as diagnostic signals, not automatic design laws:

- Same-column or same-row alignment drift should normally stay within roughly 4 px in a 1280×720 render.
- Repeated gaps should not differ by more than about 5% without intent.
- Chinese letter spacing should normally remain at or below 2% of font size.
- Within one body block, line spacing should usually be about 1.15–1.35× the font size.
- A caption should normally sit within about 60 px of the related image in a 1280×720 render.
- A meaningful primary image should normally occupy at least 30% of slide width and typically 40–60% on image-led pages.
- Check that the visually strongest element matches the slide's intended message.

## 4. Review order

For each slide, review in this order:

1. Can the main message be identified in three seconds?
2. Is the dominant visual element appropriate and sufficiently prominent?
3. Is the typography hierarchy clear and comfortable?
4. Do image framing, aspect ratio, and crop support the message?
5. Are alignment, spacing, and whitespace intentional?
6. Is every element necessary?

Then review the montage for pacing, consistency, and silhouette variation.

## 5. Finding format

Record only actionable findings:

```text
Slide: 4
Severity: revise
Finding: Primary image occupies about 24% of the page and reads as decoration.
Action: Change to a 52/48 split, preserve the subject, and reduce body copy to six lines.
Verify: Re-render slide 4 and inspect it beside slides 3 and 5.
```

Use `pass`, `revise`, or `block`:

- `pass`: no material visual issue;
- `revise`: aesthetic or hierarchy issue that should be fixed;
- `block`: hard failure that prevents delivery.

## 6. Attachment-free review loop

- Keep the working PPTX internal.
- Render all slides for the first review.
- Show inline renders or a montage rather than a draft PPTX attachment.
- Apply feedback to the same working deck.
- Re-render affected slides and adjacent context only.
- Deliver one PPTX after approval or explicit export request.
