# Motion Canvas Reference Notes & Comparative Evaluation

This document evaluates Motion Canvas and the `VideoZero/skills` package (`motion-canvas`, `motion-canvas-agent`, `animation-basics`) in the context of `football-video-pipeline`.

---

## 1. Overview of Motion Canvas

Motion Canvas is an open-source, TypeScript-based programmatic animation framework developed by acko.net / Motion Canvas community. Unlike Remotion, which renders using standard React DOM and Chromium, Motion Canvas executes animations inside an HTML5 Canvas using TypeScript generator functions (`function*`) and an observable reactive signal system.

### Generator Paradigm Example
```ts
import { makeScene2D } from '@motion-canvas/2d';
import { Circle, createRef, all } from '@motion-canvas/2d';

export default makeScene2D(function* (view) {
  const circle = createRef<Circle>();
  view.add(<Circle ref={circle} width={120} height={120} fill={'#E63946'} />);

  // Sequential execution paused per frame via yield*
  yield* circle().position.x(200, 1);
  yield* circle().scale(1.5, 0.5);
});
```

---

## 2. Technical Comparison: Remotion vs. Motion Canvas

| Dimension | Remotion | Motion Canvas | Decision for Football Pipeline |
| :--- | :--- | :--- | :--- |
| **Rendering Backend** | Web DOM / Chromium (HTML, CSS, SVG, WebGL) | HTML5 2D Canvas Context / WebGL | **Remotion**: Standard CSS flexbox, typography, text-wrapping, and drop-shadows are essential for news lower thirds. |
| **Control Flow** | React state & pure mathematical frame index (`useCurrentFrame()`) | Generator threads (`function*`, `yield*`) & Signals | **Remotion**: Pure mathematical functions of `frame` are easier for agents to parameterize deterministically from JSON. |
| **Asset & Image Handling** | Native `<img>`, `<video>`, SVG paths, web fonts | Canvas bitmap drawing, manual texture loading | **Remotion**: Direct integration with local high-res sports photography and web font loaders. |
| **Headless Production CLI** | Mature CLI (`npx remotion render`, `--props`, `--frames`) | Primarily designed around an interactive Vite web editor | **Remotion**: Far simpler headless batch rendering in server/CLI environments. |
| **Vertical Video Ecosystem** | Rich community ecosystem (`video-motion-graphics`, safe-zone containers) | Focus on 16:9 technical and mathematical YouTube videos | **Remotion**: Out-of-the-box vertical 9:16 safe-zone components. |

---

## 3. Retained Asset: `animation-basics`

While Motion Canvas as a rendering runtime was not selected to avoid dual-engine complexity, its foundational companion skill—**`animation-basics`**—was installed into `.agents/skills/animation-basics`.

The principles in `animation-basics` directly improve our Remotion components:
- **Staging & Hierarchy:** Keeping secondary stats and background stadium photos subdued so that the primary transfer headline and financial terms command immediate focus.
- **Timing & Mass:** Assigning heavier spring mass to large contract cards (`mass: 1.2`) and snappy, lightweight mass to breaking news badges (`mass: 0.4`).
- **Anticipation & Squash/Stretch:** Adding subtle pre-motion scaling to lower thirds before settling into resting position.
