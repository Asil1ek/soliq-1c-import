
## 2024-05-24 - File Input Keyboard Focus Patterns
**Learning:** Invisible file inputs (`opacity: 0`) used for drag-and-drop zones create accessibility issues because keyboard focus is entirely invisible when users tab to them.
**Action:** Always map the file input's `focus` and `blur` events to the parent container's existing drag-and-drop hover/active classes (e.g., `.dragover`). This provides an immediate, zero-CSS keyboard focus indicator that fits the existing design system perfectly.
