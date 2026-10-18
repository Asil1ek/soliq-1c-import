## 2026-10-18 - Visually Hidden File Inputs Focus States
**Learning:** Keyboard users lose focus visibility on `opacity: 0` inputs used for drag-and-drop overlays. Simply adding CSS `:focus` to the hidden input does not work because it is invisible.
**Action:** Use inline `onfocus` and `onblur` events on the hidden input to toggle a parent class (like `.dragover`) to inherit existing visual hover/active states for keyboard accessibility without adding redundant custom CSS.
