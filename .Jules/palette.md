## 2024-06-25 - Visible Focus for Hidden Inputs
**Learning:** When styling file inputs with `opacity: 0` over a drop zone, keyboard users lose the visible focus indicator. Toggling existing hover classes on the parent container (e.g., `.dragover`) using `onfocus` and `onblur` restores this vital feedback without requiring new CSS rules.
**Action:** Apply inline `onfocus` and `onblur` handlers to hidden inputs that toggle parent hover states to maintain keyboard accessibility in custom input components.
