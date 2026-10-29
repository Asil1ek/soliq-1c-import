## 2025-01-20 - Keyboard Accessibility for File Dropzones
**Learning:** File inputs made invisible (`opacity: 0`) to cover a dropzone lose their native focus ring, making them inaccessible for keyboard users trying to tab through the page.
**Action:** Used the existing hover class (`.dragover`) and toggled it via inline `onfocus` and `onblur` events directly on the file inputs. This provides a visible focus state matching the hover state without adding custom CSS. Added ARIA labels in Uzbek for screen reader context.
