## 2024-05-15 - Visually Hidden File Inputs Focus State
**Learning:** File inputs with `opacity: 0` are visually hidden but still focusable by keyboard, leading to a "ghost focus" where keyboard users cannot see where their focus is.
**Action:** Use inline `onfocus="this.parentElement.classList.add('dragover')"` and `onblur="this.parentElement.classList.remove('dragover')"` on hidden inputs to leverage existing CSS classes for focus indicators without writing custom CSS.
