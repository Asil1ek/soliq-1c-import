## 2024-05-24 - Hidden File Inputs Focus States
**Learning:** Hidden file inputs inside custom drag-and-drop zones completely lose keyboard focus visibility, making them invisible to keyboard-only users who try to tab through forms.
**Action:** Use the CSS `:has(:focus-visible)` pseudo-class on the parent wrapper element to elegantly restore focus rings without breaking the custom design of the drop zone.
