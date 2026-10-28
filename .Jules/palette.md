## 2024-05-24 - Visually Hidden File Inputs Focus State
**Learning:** File inputs in this app are styled with `opacity: 0` to allow custom drop zones, making default focus outlines invisible to keyboard users.
**Action:** Apply `onfocus` and `onblur` inline events to these inputs to toggle the existing `.dragover` CSS class on their parent cards, providing clear visual feedback during keyboard navigation without requiring new custom CSS.
