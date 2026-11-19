# Animation Techniques & Motion Design for Sports Shorts

This reference documents the motion design rules, spring calibrations, safe-zone layouts, and animation techniques synthesized from `animation-basics`, `video-motion-graphics`, and `remotion-best-practices` specifically tailored for the Football Video Pipeline.

---

## 1. The 12 Principles of Animation in Sports Motion Graphics

| Principle | Traditional Definition | Implementation in Remotion Sports Graphics |
| :--- | :--- | :--- |
| **1. Squash & Stretch** | Distorting an object to show flexibility and mass | When lower-third badges pop in, apply subtle scale overshoot on the Y-axis (`scaleY: 1.08, scaleX: 0.94`) before settling at `1.0`. |
| **2. Anticipation** | Preparing the viewer for an action | A small backward shift or slight fade-in scale prep (`scale: 0.95 -> 1.05 -> 1.0`) before a transfer headline springs into view. |
| **3. Staging** | Directing attention to what is important | Never compete for viewer focus. If a contract fee (€60M) is highlighted, keep background stadium action subdued with dark vignetting and motion blur. |
| **4. Pose-to-Pose** | Keyframing start, peak, and finish states | Define clear frame boundaries using `interpolate(frame, [0, 15, 30], [0, 1.05, 1.0], { extrapolateRight: 'clamp' })`. |
| **5. Follow Through & Overlap** | Unsynchronized movement communicating mass | When the lower-third plate enters from the left, let the kicker text arrive 3 frames later and the gold highlight line arrive 5 frames later. |
| **6. Slow In & Slow Out** | Natural acceleration and deceleration | Always use calibrated spring physics or cubic bezier curves (`ease-out`) for graphic cards; avoid robotic linear motion. |
| **7. Arcs** | Natural curved trajectories | Use subtle 2.5D camera parallax panning across player portraits along curved Bezier paths rather than rigid straight lines. |
| **8. Secondary Action** | Supporting motion enhancing the main action | While the primary player photo slowly pushes in, a glowing gold status indicator pulses subtly (`opacity: 0.8 -> 1.0`). |
| **9. Timing** | Spacing and speed setting weight and urgency | Snappy 8–12 frame transitions for breaking news punches; steady 20–30 frame holds for tactical explainers and contract numbers. |
| **10. Exaggeration** | Amplifying action to convey impact | Emphasize huge numbers (e.g. `€60M`) with a bold pop-in and yellow highlight color rather than plain white text. |
| **11. Solid Drawing / Form** | Realistic volume, perspective, and depth | Crisp drop shadows (`rgba(0, 0, 0, 0.75) 0px 8px 24px`) beneath lower-third panels to cleanly separate text from match photos. |
| **12. Appeal** | Cleanliness, legibility, and visual charisma | High-contrast typography (Barlow Condensed ExtraBold), crisp borders, and a balanced 9:16 layout that feels authoritative. |

---

## 2. Spring Physics Calibration Presets

Remotion's `spring()` function calculates physical spring kinematics based on frame number, fps, and a configuration object:

```tsx
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

const progress = spring({
  frame,
  fps,
  config: {
    damping: 12,
    mass: 0.5,
    stiffness: 120,
  },
});
```

### Curated Presets for Football Broadcast Shorts

1. **Breaking News Badge / Kicker (`Snappy Pop`):**
   - `mass: 0.4`, `damping: 11`, `stiffness: 150`
   - *Feel:* Rapid, authoritative snap. Best for `REPORTED`, `RUMOUR`, `TRANSFER WATCH` pill reveals.
2. **Lower-Third Panel Entry (`Tactile Slide`):**
   - `mass: 0.8`, `damping: 14`, `stiffness: 110`
   - *Feel:* Solid broadcast bar entering smoothly from the left margin, coming to rest with minimal wobble.
3. **Player Photo Parallax Push (`Cinematic Camera`):**
   - `mass: 1.5`, `damping: 24`, `stiffness: 60`
   - *Feel:* High-mass, slow cinematic zoom that simulates a professional camera jib or steadycam.
4. **Contract Card Pop-In (`Data Reveal`):**
   - `mass: 0.6`, `damping: 12`, `stiffness: 130`
   - *Feel:* Clean graphic card bounce for deal terms, financial fees, and tactical formation diagrams.

---

## 3. Platform Safe-Zone Geometry (1080 × 1920)

To ensure headlines and subtitles are never obscured by native mobile app UI elements across YouTube Shorts, Instagram Reels, and TikTok, the composition adheres strictly to the vertical safe zones:

```
┌────────────────────────────────────────────────────────┐ (0, 0)
│ TOP DANGER ZONE (180px)                                │
│ Channels name, sound icon, search, status bar          │
├────────────────────────────────────────────────────────┤ (y = 180px)
│                                                        │
│ TOP HUD: Channel bug & Truthful Kicker (y = 190 - 240) │
│                                                        │
│                                                        │
│               EDITORIAL FOCUS AREA                     │
│                                                        │
│                                                        │
│ LOWER-THIRD HEADLINES: (y = 1320 - 1500)               │
│                                                        │
│ SUBTITLE CAPTION BAND: (y = 1200 - 1300)               │
│                                                        │
│ ROLLING FACTUAL TICKER: (y = 1520 - 1580)              │
├────────────────────────────────────────────────────────┤ (y = 1600px)
│ BOTTOM DANGER ZONE (320px)                             │
│ Video title, description, music ticker, like/comment   │
└────────────────────────────────────────────────────────┘ (1080, 1920)
```

- **Top Safe Margin:** `180px`
- **Bottom Safe Margin:** `320px`
- **Side Margins:** `90px` left and right to clear the right-side engagement buttons (Like, Comment, Share, Remix).

---

## 4. Preserving the Channel's 90s Broadcast Visual Identity

The existing visual identity of the channel is iconic and must not be replaced by generic corporate or Vox aesthetics:

1. **Color Palette:**
   - Primary Panel Background: Dark Navy Blue (`#0B132B`, `#1C2541`) with 92% opacity.
   - News/Alert Accents: Vibrant Crimson Red (`#D90429`, `#EF233C`).
   - Secondary Emphasis & Badges: Golden Yellow (`#FFD166`, `#F4A261`).
   - Body & Subtitles: Pure White (`#FFFFFF`) with dark drop shadows (`0 4px 12px rgba(0,0,0,0.85)`).
2. **Typography:**
   - Font Family: `Barlow Condensed`, `Arial Black`, or `Impact` (ExtraBold uppercase for headlines).
   - Headline Sizing: 58px–68px with tight line height (`0.95`).
   - Subheadline Sizing: 32px–38px with clean letter spacing.
3. **No Cheesy Gimmicks:**
   - Prohibit heavy simulated CRT distortion, curved cathode screens, or static TV noise overlays.
   - Deliver clean, ultra-crisp 1080x1920 graphics that evoke the energy of 90s sports television while maintaining modern mobile clarity.
