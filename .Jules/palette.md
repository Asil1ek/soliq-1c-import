## 2023-10-21 - Accessible focus states for visually hidden file inputs
**Learning:** Visually hidden inputs (`opacity: 0` styled over dropzones) inherently lose visible focus indicators, making keyboard navigation difficult for screen reader and keyboard-only users.
**Action:** When creating completely transparent input overlays in file dropzones, always apply `onfocus` and `onblur` events directly to the input to trigger visual state changes (like adding/removing `.dragover` classes) on the visible parent container. Also ensure proper `aria-label`s exist since the native text is hidden.
