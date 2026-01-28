
# MOBILE-OPTIMIZED PRACTICE CHECK

*(Web apps, PWAs, mobile-first SaaS, responsive sites)*

---

## 1. MOBILE FIRST REALITY CHECK

Ask **before anything else**:

* Was this screen **designed for mobile first**, or shrunk from desktop?

Checklist:

* [ ] No horizontal scrolling
* [ ] No “desktop thinking” (tables, tiny controls)
* [ ] Content stacked vertically, not compressed
* [ ] Mobile flow makes sense standalone

🔴 Red flag: “Works fine if you rotate / zoom”.

---

## 2. TOUCH & TAP SAFETY (CRITICAL)

Checklist:

* [ ] Tap targets ≥ **44×44 px**
* [ ] Adequate spacing between interactive elements
* [ ] No accidental taps near destructive actions
* [ ] Icons + text where meaning matters

Rule:

> If a thumb can miss it → redesign.

🔴 Red flag: links close together or tiny icons.

---

## 3. THUMB ZONE & REACHABILITY

Checklist:

* [ ] Primary actions in **thumb-reachable zone**
* [ ] Bottom navigation for frequent actions
* [ ] No critical actions only at top
* [ ] Floating CTAs don’t cover content

Best practice:

* Primary CTA → bottom
* Secondary → contextual / hidden

---

## 4. MOBILE NAVIGATION

Checklist:

* [ ] Max 3–5 primary nav items
* [ ] Labels clear (icons alone are risky)
* [ ] Back action predictable
* [ ] No hidden critical routes

Avoid:
❌ Hamburger + deep nesting for core flows
✅ Bottom tabs or visible primary actions

---

## 5. MOBILE TYPOGRAPHY & READABILITY

Checklist:

* [ ] Base font ≥ **16px**
* [ ] Line length comfortable
* [ ] No dense paragraphs
* [ ] Clear headings hierarchy
* [ ] Contrast readable outdoors

🔴 Red flag: user needs zoom to read.

---

## 6. FORMS ON MOBILE (MAKE OR BREAK)

Checklist:

* [ ] Minimal fields only
* [ ] Correct keyboard type per input
* [ ] Inline validation
* [ ] Labels always visible
* [ ] Sticky submit button if long form
* [ ] Autofill enabled

Golden rule:

> One question per screen > many fields per screen.

---

## 7. MOBILE FEEDBACK & STATES

Checklist:

* [ ] Tap feedback (visual or haptic)
* [ ] Loading indicators after every action
* [ ] Disabled states explained
* [ ] Errors shown near inputs
* [ ] Success confirmation visible

🔴 Red flag: “Did it register my tap?”

---

## 8. RESPONSIVE LAYOUT SAFETY

Checklist:

* [ ] No overlapping elements
* [ ] No fixed heights breaking content
* [ ] Modals fit small screens
* [ ] Safe area padding respected (notches)
* [ ] Sticky elements don’t hide CTAs

Test widths:

* 320px
* 360px
* 390px

---

## 9. PERFORMANCE ON MOBILE NETWORKS

Checklist:

* [ ] Fast first content paint
* [ ] Skeletons instead of spinners
* [ ] Lazy loading images
* [ ] No layout shifts after load
* [ ] Interactions respond instantly

Rule:

> Mobile users forgive less than desktop users.

---

## 10. EMPTY, ERROR & OFFLINE STATES (MOBILE-SPECIFIC)

Checklist:

* [ ] Empty states explain what to do
* [ ] Offline mode handled gracefully
* [ ] Network errors retryable
* [ ] No white screens

Good empty state:

1. What this is
2. Why empty
3. What to do next

---

## 11. GESTURES & SCROLL BEHAVIOR

Checklist:

* [ ] Scroll direction obvious
* [ ] No accidental horizontal scroll
* [ ] Pull-to-refresh intentional
* [ ] Gestures have visual affordances
* [ ] Gestures are optional, not required

🔴 Red flag: hidden gestures with no hint.

---

## 12. MOBILE ACCESSIBILITY

Checklist:

* [ ] Works one-handed
* [ ] Works with screen readers
* [ ] Focus visible
* [ ] Color not sole indicator
* [ ] Motion reduced when needed

Quick test:

> Can I use this on a bus with one hand?

---

## 13. MOBILE EMOTIONAL UX

Checklist:

* [ ] Friendly, calm microcopy
* [ ] Errors reduce stress
* [ ] Success moments acknowledged
* [ ] No aggressive popups

Avoid:
❌ Modal spam
❌ Forced sign-ups mid-flow

---

## 14. FINAL MOBILE SHIP TEST (NON-NEGOTIABLE)

Answer **YES** to all:

* [ ] Usable with one hand
* [ ] Clear in 5 seconds
* [ ] No precision tapping
* [ ] Works on slow network
* [ ] No zoom needed

If one “no” → don’t ship.

---

## QUICK MOBILE RELEASE CHECK (ONE SCREEN)

* [ ] Tap targets safe
* [ ] Primary CTA reachable
* [ ] Text readable
* [ ] No overlap
* [ ] Feedback visible
* [ ] Fast enough
