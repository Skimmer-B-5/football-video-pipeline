# Video Production Agent Skills Inventory & Evaluation

This document catalogues and evaluates candidate agent skills discovered across the Agent Skills ecosystem (`skills.sh`, `agentskills.io`, GitHub, and official vendor repositories) for local, programmable video production in `football-video-pipeline`.

---

## 1. Skill Evaluation Matrix

| Skill Name | Repository URL | Rendering Framework | Main Purpose | Production Problem Solved | Included Supporting Files | Required Dependencies | Operates Locally? | Paid APIs? | Licence | Security Assessment | Relevance to Project |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- | :---: |
| **`remotion-best-practices`** | `https://github.com/remotion-dev/skills` | Remotion (React) | Master router and rule guide for Remotion compositions | Enforces frame determinism, prevents non-deterministic hooks, guides spring physics calibration | `SKILL.md`, sub-skill references, agent definitions | Node.js 18+, `@remotion/cli` | Yes | No | Remotion License / Free tier for small teams | Safe; local rules engine | **Critical** (Primary Remotion engine) |
| **`remotion-render`** | `https://github.com/remotion-dev/skills` | Remotion (Chromium / FFmpeg) | Headless video, frame, and still export | Programmatic rendering via CLI with input JSON props and custom output formats | `SKILL.md`, `agents/openai.yaml` | Node.js, Remotion bundled browser, FFmpeg | Yes | No | Remotion License | Safe; local subprocess invocation | **Critical** (Headless rendering pipeline) |
| **`remotion-markup`** | `https://github.com/remotion-dev/skills` | Remotion (React) | Layout, styling, animation, and effects best practices | Frame-locked CSS, SVG shapes, spring curves, responsive 9:16 layout | `SKILL.md`, references, code examples | React 18/19, `@remotion/shapes` | Yes | No | Remotion License | Safe; static reference | **Critical** (Component authoring) |
| **`remotion-captions`** | `https://github.com/remotion-dev/skills` | Remotion | Subtitle display, SRT ingestion, karaoke animations | Eliminates caption drift; renders word-by-word synchronized subtitles | `SKILL.md`, `display-captions.md`, `import-srt-captions.md` | `@remotion/captions`, Node.js | Yes | No | Remotion License | Safe; local parser | **Critical** (High-retention captions) |
| **`remotion-create`** | `https://github.com/remotion-dev/skills` | Remotion | Bootstrapping new Remotion templates and compositions | Scaffolds deterministic composition boilerplate with config and entrypoints | `SKILL.md`, setup references | `@remotion/cli`, npm | Yes | No | Remotion License | Low risk; template generator | **High** (Project setup) |
| **`remotion-studio`** | `https://github.com/remotion-dev/skills` | Remotion | Interactive browser-based preview server | Enables visual preview, scrub controls, and WebMCP visual inspection | `SKILL.md`, launch guides | Remotion Studio HTTP server | Yes | No | Remotion License | Low risk; local localhost server | **High** (Developer preview) |
| **`remotion-docs`** | `https://github.com/remotion-dev/skills` | Remotion | Offline and online Remotion API documentation lookup | Provides syntax and API references for composition properties | `SKILL.md` | Local markdown search | Yes | No | Remotion License | Safe; reference only | **Medium** (Reference lookups) |
| **`ffmpeg-skill`** | `https://github.com/kajisho5/ffmpeg-skill` | Local FFmpeg 6.1+ | 42 standalone Python tools for precise audio/video manipulation | Loudness mastering (-14 LUFS), silent gap trimming, sub-frame sync, verification, look sheets | 42 standalone Python scripts (`scripts/loudness.py`, `cut.py`, `sync.py`, `probe.py`, `look.py`, `verify.py`), `references/` | Python 3.10+, FFmpeg 6.1+ binary (stdlib only) | Yes | No | MIT | Safe; clean stdlib Python wrappers around local FFmpeg | **Critical** (Audio mastering, media prep, QA) |
| **`video-motion-graphics`** | `https://github.com/ramzieus/video-motion-graphics` | Remotion (React) | Code-driven 1080x1920 vertical motion graphics | Enforces mobile safe-zones (180 top, 320 bottom, 90 sides), kinetic typography, camera rig, and scene phase approvals | `SKILL.md`, `templates/primitives/` (`SafeZoneContainer.tsx`, `KineticText.tsx`, `AnimatedCounter.tsx`, `CameraRig.tsx`), `examples/` | Remotion 4+, React 18+ | Yes | No | MIT | Safe; pure TypeScript/React templates | **Critical** (Shorts/Reels 9:16 layout) |
| **`animation-basics`** | `https://github.com/VideoZero/skills` | Framework-agnostic | 12 principles of animation & duration/timing guide | Provides mathematical curves, squash & stretch, staging, and timing rules | `SKILL.md` | None (pure conceptual rules) | Yes | No | Apache-2.0 | Safe; pure markdown theory | **High** (Motion polish & realism) |
| **`motion-canvas`** | `https://github.com/VideoZero/skills` | Motion Canvas (TypeScript generators) | Code-based procedural vector animation via generators | Alternative animation framework using `function*` and signals | `SKILL.md` | `@motion-canvas/core`, `@motion-canvas/2d` | Yes | No | MIT / Apache-2.0 | Safe; open source | **Low / Reference** (Remotion selected for video) |
| **`motion-canvas-agent`** | `https://github.com/VideoZero/skills` | Motion Canvas | Agent HTTP control for live browser canvas inspection | Inspects live generator tree via browser automation | `SKILL.md` | Headless browser + Motion Canvas editor | Yes | No | Apache-2.0 | Medium; requires live browser listener | **Excluded** (Unneeded complexity) |
| **`claude-remotion-skill`** | `https://github.com/haidrrrry/claude-remotion-skill` | Remotion | Motion graphics, B-roll handling, and sound design prompt guidance | Prompt design patterns for AI-directed Remotion video production | `SKILL.md`, `examples/`, `references/` | Remotion | Yes | No | MIT | Safe; markdown prompt rules | **High / Evaluated** (Incorporated into design) |

---

## 2. Selected Minimal Toolset

To prevent framework bloat while providing complete broadcast-grade production capabilities, the following minimal combination was selected:

1. **Composition & Motion Engine:** **Remotion** (`remotion-best-practices`, `remotion-render`, `remotion-markup`, `remotion-captions`, `remotion-create`, `remotion-studio`, `remotion-docs`).
2. **Mobile Layout & Safe-Zones:** **`video-motion-graphics`** (1080x1920 vertical canvas, 180px top / 320px bottom safe margins, spring motion presets).
3. **Audio Mastering & Video QA:** **`ffmpeg-skill`** (42 local Python CLI tools for exact LUFS mastering, duration probing, silence trimming, and contact sheet extraction).
4. **Motion Design Theory:** **`animation-basics`** (12 principles of animation applied to programmatic keyframes and springs).

Higgsfield and external cloud video generation APIs are **strictly excluded**. All selected tools execute 100% locally on CPU/GPU without recurring API charges.
