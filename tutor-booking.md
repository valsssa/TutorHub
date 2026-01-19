### 🎯 Goal

Make the **session duration strictly fixed to 25 or 50 minutes**, and reflect that clearly on the **student booking UI** and **tutor pricing displays**, replacing ambiguous “price/hour” with **“price per 50 min”** (and optionally **“price per 25 min”** where relevant).

The change must be consistent across:

1. Tutor listings
2. Tutor detail page
3. Booking modal
4. Dashboard bookings view

---

## 🧱 Step-by-Step Implementation (Frontend, Next.js 15)

### 1️⃣ Tutor Listing (`frontend/app/tutors/page.tsx`)

#### What to change:

Replace `price/hr` label in each tutor card.

#### File to edit:

`frontend/components/TutorCard.tsx`

```tsx
// Before:
<p className="text-sm text-gray-500">{tutor.hourlyRate} USD / hr</p>

// After:
<p className="text-sm text-gray-500">
  {tutor.hourlyRate} USD / 50 min
</p>
```

✅ **Design note:**
Add a tooltip or small subtext:

> “All sessions last 25 or 50 minutes.”

---

### 2️⃣ Tutor Detail Page (`frontend/app/tutors/[id]/page.tsx`)

Replace all mentions of “hourly rate” → “per 50 min”.

Example:

```tsx
// Before
<div className="text-gray-500 text-sm">Price: ${tutor.hourlyRate}/hr</div>

// After
<div className="text-gray-500 text-sm">Price: ${tutor.hourlyRate}/50 min</div>
```

If the tutor has multiple pricing tiers (like trial/regular), ensure:

```tsx
<span>{price.trialPrice} USD / 25 min Trial</span>
<span>{price.regularPrice} USD / 50 min Lesson</span>
```

---

### 3️⃣ Booking Modal (`frontend/components/ModernBookingModal.tsx`)

#### Add duration selector — two fixed options only.

Replace any existing duration input with:

```tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";

const [duration, setDuration] = useState(25);

<div className="flex gap-3 mt-3">
  <Button
    variant={duration === 25 ? "default" : "outline"}
    onClick={() => setDuration(25)}
  >
    25 minutes
  </Button>
  <Button
    variant={duration === 50 ? "default" : "outline"}
    onClick={() => setDuration(50)}
  >
    50 minutes
  </Button>
</div>
```

Then pass this `duration` to API call:

```tsx
await api.bookings.create({
  tutorId: tutor.id,
  startAt,
  durationMinutes: duration,
  lessonType: "REGULAR",
});
```

---

### 4️⃣ Confirmation Screen or Dashboard (`frontend/app/bookings/page.tsx`)

Show duration explicitly:

```tsx
<p>{booking.durationMinutes} min session • ${booking.totalPrice}</p>
```

---

### 5️⃣ Price Calculation Adjustments

If frontend computes “hourly → per session” locally (in `frontend/lib/usePrice.ts`), modify logic:

```ts
export function computeSessionPrice(hourlyRate: number, duration: number) {
  // old: return hourlyRate * (duration / 60)
  if (duration === 25) return Math.round(hourlyRate / 60 * 25);
  if (duration === 50) return Math.round(hourlyRate / 60 * 50);
}
```

---

## 🎨 UI/UX Copy Adjustments

| Area             | Old Text                   | New Text                                   |
| ---------------- | -------------------------- | ------------------------------------------ |
| Tutor card       | `$25/hr`                   | `$25 / 50 min`                             |
| Tutor detail     | “Hourly Rate”              | “Lesson Price”                             |
| Booking modal    | “Select time and duration” | “Choose your session length: 25 or 50 min” |
| Tooltip / helper | —                          | “All sessions last 25 or 50 minutes only.” |

---

## ✅ Summary of Required Frontend Changes

| Component         | File                                | What to do                |
| ----------------- | ----------------------------------- | ------------------------- |
| Tutor card        | `components/TutorCard.tsx`          | Replace “/hr” → “/50 min” |
| Tutor detail      | `app/tutors/[id]/page.tsx`          | Replace rate label        |
| Booking modal     | `components/ModernBookingModal.tsx` | Add 25/50 min selector    |
| Price util        | `lib/usePrice.ts`                   | Update math to 25/50 min  |
| Student dashboard | `app/bookings/page.tsx`             | Show duration explicitly  |

