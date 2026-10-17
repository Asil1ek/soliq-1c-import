## 2024-05-18 - Visible Focus States for Hidden File Inputs
**Learning:** In this application, file inputs are hidden (`opacity: 0`) and overlaid on a custom card. Keyboard users previously had no visible focus state when tabbing.
**Action:** For hidden inputs, toggle an existing hover/drag CSS class (like `.dragover`) on the parent container via `onfocus` and `onblur` events to provide clear focus indicators without adding custom CSS.
