## 2026-10-13 - [Focus visibility for visually hidden elements]
**Learning:** [Visually hidden interactive elements (like file inputs using `opacity: 0` stretched over a card component) completely destroy native keyboard focus visibility because the element focused is fully transparent.]
**Action:** [Map the hidden input's native `focus` and `blur` events to the parent visual container (e.g. adding a `.dragover` or `.focus-visible` CSS class) to restore highly visible focus states for keyboard users.]
