## 2024-05-14 - File Input Accessibility
**Learning:** Found that visually hidden file inputs in custom dropzone UI elements lack descriptive labels, making them inaccessible to screen reader users who cannot see the surrounding visual context.
**Action:** Adding `aria-label` attributes to the visually hidden `input[type="file"]` elements to explicitly describe their purpose to assistive technologies.
