## 2025-01-20 - Visually Hidden File Inputs Focus State
**Learning:** File inputs with `opacity: 0` are accessible to keyboards, but lack visual feedback when focused (tabbing), leaving screen reader and keyboard users lost. Using existing hover classes (like `.dragover`) via inline `onfocus` and `onblur` provides a clean keyboard focus ring without needing new CSS.
**Action:** When making file inputs invisible (opacity: 0) to restyle them, always ensure a focus indicator is preserved by toggling an active/hover class on the parent container during `focus`/`blur` events.
