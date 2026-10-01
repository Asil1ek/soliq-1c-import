## 2023-11-20 - Invisible File Input Accessibility Focus
**Learning:** When using custom styled file dropzones with `opacity: 0` on the actual `<input type="file">`, keyboard users cannot see when the element receives focus because it's invisible. Screen readers still announce it (if it has an aria-label), but keyboard-only sighted users get lost.
**Action:** Always use the `:focus-within` pseudo-class on the parent dropzone container (e.g., `.upload-drop-card:focus-within`) to apply focus styles (like hover styles) when the hidden input receives focus.
