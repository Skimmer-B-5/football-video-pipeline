---
name: vox-video-editor
description: >-
  Industry-grade Vox Media documentary & visual essay video editing skill for high-retention YouTube Shorts.
  Guides the automated generation of 2.5D subject cutouts (background removal with white paper sticker strokes),
  authentic newspaper & article clippings with neon highlighter wipes, kinetic stat callouts, and multiplane FFmpeg parallax motion.
---

# Vox Media Documentary Video Editing Skill (`vox-video-editor`)

This skill defines the signature visual language and technical pipeline for transforming static web images into dynamic, multi-layered, documentary-grade visual essays in the style of **Vox Media**, **Magnates Media**, and **Johnny Harris**.

---

## 1. Core Visual Techniques & Philosophy

A static full-screen image slide show causes viewer fatigue. The Vox visual style creates visual momentum through:

1. **2.5D Multiplane Subject Cutout (Parallax)**:
   - Strips the background from human subjects using lightweight AI segmentation (`rembg` with `u2netp`).
   - Applies an iconic **white paper sticker outline** (4-6px dilated alpha stroke) and soft directional drop shadow.
   - Places the subject over an atmospheric, slightly blurred and darkened background.
   - Animate with opposing motion: Background slowly pans/zooms in ($1.0 \to 1.05$), while the foreground subject floats or scales ($1.0 \to 1.08$), producing a multiplane camera depth effect.

2. **Editorial Newspaper & Document Clippings**:
   - Renders authentic cream/parchment paper cards (`#f8f7f2`) with rounded corners, subtle drop shadows, and publication mastheads (e.g. *FourFourTwo*, *The Athletic*, *Marca*).
   - **Neon Marker Highlighter Wipe**: A vibrant translucent yellow highlighter stroke (`rgba(255, 235, 30, 0.65)`) reveals across the key sentence as the narrator speaks it.
   - Subtle 3D card tilt (-2.5 degrees) and push-in camera motion.

3. **Kinetic Financial & Stat Callout Badges**:
   - Dark matte slate `#12151a` badges with warning red or gold accent indicator bars.
   - Heavy condensed monospace figures (e.g. `[ - €90M DEBT - ]` or `[ 8-YEAR CONTRACT ]`).

4. **Visual Alternation Across Cuts**:
   - **Hook (Cut 1)**: 2.5D Subject Cutout floating over context background.
   - **Crisis (Cut 2)**: Dark vignette pitch crisis with kinetic stat callout badge overlay.
   - **Fact (Cut 3)**: Vox Newspaper Clipping card with neon highlighter wipe.
   - **Irony / Tactics (Cut 4)**: 2.5D Formal Subject Cutout with multiplane drift.
   - **Meme (Cut 5-6)**: High-impact meme visual with subtle sound effects.
   - **Climax (Cut 7)**: Dramatic full-bleed focal photo.
   - **Outro (Cut 8)**: Clean circular FS30 badge on solid matte black with spoken voiceover.

---

## 2. Python Architecture (`stages/vox_visual_engine.py`)

The pipeline implements this through modular Python components:

```python
from stages.vox_visual_engine import (
    create_subject_cutout,
    create_newspaper_clipping_card,
    create_stat_callout_badge,
    render_vox_parallax_slide,
    render_vox_clipping_slide
)

# 1. Subject cutout sticker
cutout_path = create_subject_cutout(raw_image_path, out_png, stroke_width=6)

# 2. Newspaper clipping card with highlighter
clipping_path = create_newspaper_clipping_card(
    headline="Gareth Bale plotting audacious takeover of Sevilla",
    source_name="FourFourTwo",
    highlight_phrase="takeover of Sevilla",
    output_png_path=out_clipping
)

# 3. Kinetic stat badge
badge_path = create_stat_callout_badge(
    stat_value="€90M DEBT",
    stat_label="SEVILLA FINANCIAL CRISIS",
    output_png_path=out_badge
)

# 4. Multiplane FFmpeg Parallax Slide
render_vox_parallax_slide(bg_image, cutout_path, output_mp4, duration_sec=3.8)

# 5. Newspaper Clipping Slide
render_vox_clipping_slide(bg_image, clipping_path, output_mp4, duration_sec=3.8)
```

---

## 3. FFmpeg Parallax & Multiplane Compositor Rules

When layering cutouts and backgrounds in FFmpeg:
- Always use `s=1080x1920` for portrait 9:16 Shorts.
- Never add `-loop 1` before a stream that is fed into `zoompan`, as `zoompan` operates on single still frames.
- Use `shortest=1` on the overlay filter to tie stream duration cleanly to the primary slide duration.
- Scale foreground cutouts proportionally (`scale=980:-1`) so they anchor naturally in the lower two-thirds of the frame.
