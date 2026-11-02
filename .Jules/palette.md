## 2024-03-20 - Keyboard Accessibility Pattern
**Learning:** Keyboard navigation requires visible focus states, particularly for invisible file inputs layered over drop zones.
**Action:** Use inline 'onfocus' and 'onblur' handlers to toggle existing hover classes (like '.dragover') on the parent container, ensuring the hidden input receives focus and provides visual feedback without writing new custom CSS.
