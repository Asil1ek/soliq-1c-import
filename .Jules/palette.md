## 2026-10-20 - Invisible File Input Accessibility
**Learning:** Visually hidden file inputs (`opacity: 0`) overlaid on stylized drop zones must utilize the same hover states (e.g., `.dragover`) for focus states to ensure keyboard accessibility. Otherwise, keyboard users cannot perceive focus.
**Action:** Always add `onfocus`/`onblur` to toggle hover/drag classes on parent wrappers for hidden file inputs.
