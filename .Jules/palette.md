## 2024-05-24 - Invisible File Input Focus States
**Learning:** A common pattern here is using `opacity: 0` on `<input type="file">` within custom upload cards. This hides the element but keeps it focusable, leading to invisible focus states for keyboard users.
**Action:** Reuse existing hover/drag states (like `.dragover`) triggered via `onfocus` and `onblur` events on the file input to instantly provide visual keyboard focus without adding custom CSS.
