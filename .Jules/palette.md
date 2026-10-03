## 2024-05-17 - File Input Focus Trap
**Learning:** Setting `opacity: 0` on file inputs to stretch them over custom dropzone areas completely removes the native browser focus ring for keyboard users, rendering the input completely invisible during keyboard navigation.
**Action:** Always apply `:focus-within` styles to the parent dropzone container (e.g., using `box-shadow` or `outline`) to ensure the focus state is clearly communicated visually when the hidden input receives focus.
