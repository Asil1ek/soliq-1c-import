## 2023-10-26 - Keyboard Focus for Invisible Inputs within Drop Zones
**Learning:** When using invisible `<input type="file">` elements overlaid on custom styled drop-zones (like `.upload-drop-card`), keyboard focus given to the hidden input is invisible to the user. This severely degrades accessibility for keyboard navigators who cannot see when the drop-zone is active.
**Action:** Always apply `:focus-within` to the parent container of the visually hidden input to trigger the container's active visual states (e.g., hover/dragover styles), making keyboard navigation intuitive and visible.
