## 2026-11-10 - Focus Visibility for Hidden Inputs
**Learning:** When inputs are visually hidden (`opacity: 0`) but functionally accessible, keyboard users lose visible focus states.
**Action:** Toggled existing `.dragover` parent CSS class via inline `onfocus` and `onblur` events to provide visual focus indication without adding custom CSS.
