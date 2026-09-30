## 2026-09-30 - Keyboard Focus on Visually Hidden Drag-and-Drop Inputs
**Learning:** Visually hiding file inputs (`opacity: 0`) inside drag-and-drop zones removes their native focus indicators. This breaks keyboard navigation because users tabbing through the interface can't see when the drop zone has focus.
**Action:** Use `:focus-within` on the parent container (e.g., `.upload-drop-card:focus-within`) to proxy the focus state. This restores the essential navigational context for keyboard users without breaking the visual design of the drop zone.
