## **GLOBAL TEXTAREA RULES (FOR ALL SITE SECTIONS)**

> These rules apply to **every `<textarea>`** on the site: profile bios, messages, descriptions, feedback, admin notes, forms, etc.
> No exceptions unless explicitly documented.

---

## 1. **Character Limits (MANDATORY)**

Every textarea **must have a hard max limit** + live counter.

| Use case               | Min | Optimal | Max   |
| ---------------------- | --- | ------- | ----- |
| Short description      | 20  | 80–120  | 150   |
| Bio / About            | 80  | 300–500 | 600   |
| Message / Chat         | 1   | —       | 2,000 |
| Feedback / Review      | 20  | 150–300 | 500   |
| Admin / Internal notes | 0   | —       | 3,000 |

**Rules**

* `maxlength` enforced at HTML + backend
* Live counter: `123 / 500`
* Show warning at **80%**, error at **100%**

---

## 2. **Clear Intent Labeling (NO GENERIC LABELS)**

❌ Bad

> “Description”
> “Text”
> “Message”

✅ Good

> “Tell students what you can help with”
> “Short bio (shown on your public profile)”
> “Message to tutor (visible only to them)”

**Rule:**
Every textarea label must answer:

> **Who will read this + where it appears**

---

## 3. **Placeholder = Guidance, NOT EXAMPLES**

❌ Bad (AI-looking, copyable)

> “I am a passionate professional…”

✅ Good (directional)

> “What problem do you solve? What result does the user get?”

**Rule**

* Placeholders describe **structure**, not content
* Never include marketing fluff
* Never include full sentences users can blindly copy

---

## 4. **Text Quality Constraints (ENFORCED)**

Apply validation rules globally:

* ❌ No ALL CAPS messages over 10 characters
* ❌ No repeated characters: `!!!!!!`, `?????`, `-----`
* ❌ No emoji-only submissions (unless chat)
* ❌ Trim leading/trailing whitespace
* ❌ Collapse multiple blank lines into max **2**

---

## 5. **Visual & Interaction Rules**

Every textarea must:

* Auto-resize vertically (no internal scroll by default)
* Min height: **3 lines**
* Max visible height: **10–12 lines**, then scroll
* Monospace font ❌
* Same font as body text ✅
* Line height ≥ **1.5**

---

## 6. **Error & Helper Text Rules**

* Helper text always **below** textarea
* Error text:

  * Specific
  * Actionable
  * Never judgmental

❌ Bad

> “Invalid input”

✅ Good

> “Bio must be at least 80 characters”

---

## 7. **Save & Exit Safety**

If textarea content is:

* changed
* not saved

Then:

* Warn on navigation
* Prevent accidental loss
* Autosave if possible (draft state)

---

## 8. **Accessibility (NON-NEGOTIABLE)**

* `<label for>` always linked
* Screen reader announces:

  * Label
  * Character limit
  * Error state
* Color is never the only error signal
* Keyboard navigation fully supported

---

## 9. **Backend Enforcement (CRITICAL)**

Frontend validation **does NOT replace** backend rules.

Backend must:

* Re-validate length
* Sanitize input
* Reject HTML/script
* Normalize newlines

---

## 10. **Design Consistency Rule**

> If two textareas serve the same purpose,
> **they must have identical limits, rules, and UI.**

No:

* “Bio” = 500 chars on one page, 1,000 on another
* Different helper texts for same field

---

## TL;DR — One-Line Law

> **Every textarea must clearly explain its purpose, strictly limit length, guide structure (not content), prevent junk input, and never allow users to lose text accidentally.**