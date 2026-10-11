## 2026-10-11 - Unlabelled file and search inputs
**Learning:** File inputs visually hidden inside descriptive drag-and-drop cards are completely unidentifiable to screen readers unless explicitly labelled. The same goes for search inputs relying solely on placeholders.
**Action:** Always add `aria-label` attributes to `<input>` elements that lack an explicit, programmatically associated `<label>`.
