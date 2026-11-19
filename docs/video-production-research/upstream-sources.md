# Upstream Sources, Licences & Commit Provenance

This document records the exact upstream repositories, commit hashes, licences, and source URLs for all agent skills retrieved during the video production research phase.

---

## 1. Upstream Repositories & Pinned Commits

| Skill / Package | Upstream Repository URL | Pinned Commit Hash | Author / Maintainer | Upstream Licence | Local Installation Path |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`remotion-dev/skills`** | `https://github.com/remotion-dev/skills.git` | `6f55706d1069e512430582ad86e4e57dc07afe1b` | Remotion GmbH | Remotion License (Free for individuals and small teams) | `.agents/skills/remotion-*` |
| **`ffmpeg-skill`** | `https://github.com/kajisho5/ffmpeg-skill.git` | `828efbb3a861e2e51529f60246741d13590c86a0` | kajisho5 | MIT License | `.agents/skills/ffmpeg-skill` |
| **`video-motion-graphics`** | `https://github.com/ramzieus/video-motion-graphics.git` | `a39a73c4645d324e1413f99ad4100d38cc5bd578` | ramzieus | MIT License | `.agents/skills/video-motion-graphics` |
| **`motion-canvas-skills`** (`animation-basics`) | `https://github.com/VideoZero/skills.git` | `4836b74bfb745d8ea73cbf55ae2378d1f62b910f` | VideoZero | Apache License 2.0 | `.agents/skills/animation-basics` |
| **`claude-remotion-skill`** | `https://github.com/haidrrrry/claude-remotion-skill.git` | `1dcbe5e3fc6cf970bd10d3cc05f0a8a5d19d0383` | haidrrrry | MIT License | Evaluated / Reference |

---

## 2. Discovery Platforms & Documentation Consulted

1. **Skills Registry (`skills.sh`):**
   - Catalog: `https://skills.sh/`
   - Listings evaluated: `remotion-dev/skills`, `kajisho5/ffmpeg-skill`, `ramzieus/video-motion-graphics`.
2. **Agent Skills Standard (`agentskills.io`):**
   - Specification: `https://agentskills.io/`
   - Format: `SKILL.md` frontmatter, schema specification, progressive disclosure rules.
3. **Remotion AI Documentation:**
   - Official Documentation: `https://www.remotion.dev/docs/ai/skills`
   - CLI Guide: `https://www.remotion.dev/docs/cli/render`
4. **Motion Canvas Documentation:**
   - Official Documentation: `https://motioncanvas.io/docs/`
5. **Google Antigravity Customization Documentation:**
   - Specification: `https://antigravity.google/docs/skills`
   - Local Reference: `C:\Users\sb000\.gemini\antigravity\builtin\skills\agy-customizations\SKILL.md`
   - Discovery Root: `.agents/skills/<name>/SKILL.md`
