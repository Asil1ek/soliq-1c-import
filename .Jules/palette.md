## 2026-11-08 - Focus Indicators for Visually Hidden Inputs
**Learning:** When inputs are visually hidden (e.g., `opacity: 0` for custom file upload zones), native keyboard focus outlines are also hidden, breaking accessibility.
**Action:** Use inline `onfocus` and `onblur` event handlers on the hidden input to toggle existing interactive classes (like `.dragover`) on the parent container, providing a visible focus state without adding new custom CSS.
