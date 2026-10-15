## 2026-10-15 - File Input Accessibility in Custom Dropzones
**Learning:** When styling custom file dropzones using `opacity: 0` on the `input[type="file"]`, the element becomes visually invisible but remains keyboard focusable. This creates a "ghost focus" where keyboard users cannot see where their focus is, violating WCAG guidelines.
**Action:** Always pair `opacity: 0` file inputs with `:focus-within` on their visible container, and ensure an explicit `aria-label` since the visual instructions aren't inherently linked to the invisible input for screen readers.
