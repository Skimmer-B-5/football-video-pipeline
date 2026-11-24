# ⚽ Football in 30 Seconds (FS30) & 30 Football Plus — V2 Broadcast Studio

An end-to-end, high-retention video production pipeline for vertical short-form content (**YouTube Shorts**, **Instagram Reels**, **TikTok**).

Combines two complementary production pipelines:
1. **30 Football Plus V2 Primary Broadcast Engine** (`beta/`):
   - **8-Scene Screenplay Engine**: Written by OpenAI GPT-OSS 120B / Qwen 27B, strictly budgeted to 30–33 seconds (story ~26s + branded outro ~5s).
   - **Ground-Truth Fact-Checking**: Verified club database (e.g. Mauricio Pochettino officially appointed manager of Manchester United, Marco Silva at Fulham).
   - **Action-Aware Visual Director & Scraper**: Strictly bans static standing portraits; mandates real match action photography (sliding tackles, duels, sprints, celebrations, touchline shouts). Zero image reuse.
   - **Acoustic Quality Auditor & Presenter Voiceover**: Energetic original British sports presenter narration via Qwen3-TTS / Edge-TTS with pause pacing, silence trimming, and whisper/stutter suppression.
   - **Sony Trinitron CRT Analog Master**: Authentic 1990s TV broadcast aesthetic with 4px scanlines, aperture grille mask, curved tube vignette, chromatic aberration, and tape noise.
   - **Multilingual Support**: Fully localized Latin American Spanish (ES-419) with `es-MX-JorgeNeural` and Brazilian Portuguese (PT-BR) with `pt-BR-AntonioNeural` utilizing syllable-budgeted translations (6–8 words/scene).
   - **Interactive Telegram Remote Control**: Full `/new` scraper selection, script approval buttons ([Approve], [AI Rewrite], [Manual Edit], [Reject]), and in-place live progress bar.

2. **FS30 Historical Documentary Engine** (`fs30/`):
   - Vox-style 1990s newspaper collage aesthetic, 5-variant reusable graphic banners, authentic archival broadcast motion, dry British scholarly narration, and word-by-word **MrBeast-style kinetic captions**. Preserved and fully intact.

---

## ⚡ 1-Click Quick Setup (Windows)

### 1. Prerequisites
- **Windows 10 / 11**
- **Python 3.10+** (Ensure *"Add Python to PATH"* is checked)
- **FFmpeg** installed on system PATH (`winget install Gyan.FFmpeg`)
- *(Recommended)* NVIDIA GPU with CUDA for real-time speech synthesis & video rendering.

### 2. Auto-Installation
Double-click `install.bat` (or run in terminal):
```cmd
install.bat
```
This automated script:
- Verifies Python and FFmpeg.
- Creates an isolated `.venv` virtual environment.
- Auto-detects NVIDIA GPUs and installs PyTorch CUDA (cu121).
- Installs all dependencies from `requirements.txt`.
- Verifies Pillow, Transformers, SoundFile, and runs an internal health check.

### 3. Studio Launcher
Double-click `start.bat`:
```cmd
start.bat
```
Provides an interactive menu:
- `[1] Launch 30 Football Plus Primary V2 Broadcast Engine & Telegram Bot` (@Football30secbot)
- `[2] Produce Historical Documentary Video` (Zidane 2006, Cantona 1995, Suarez 2014)
- `[3] View Final Masters Vault & Open Catalog CSV`
- `[4] Run Studio QA Diagnostic & Verify Dependencies`

---

## 🎨 Key Features & Architectural Innovations

### 1. Zero Vertical Distortion (Proportional Photo Mounter)
- Replaces fixed bounding box distortions with uniform aspect ratio preservation (`fs30/story_pipeline/photo_mounter.py`).
- Calculates uniform scale: $s = \max(\text{target\_w} / w_0, \text{target\_h} / h_0)$ with intentional focus-centered cropping.
- Embeds photographs into off-white archival paper borders with simulated deckle edges and drop shadows.

### 2. Authentic Broadcast Archival Motion
- Sourced genuine historical television broadcast footage (e.g. 1995 Sky Sports broadcast of the Cantona kung-fu kick).
- 17-frame stabilized video loop running at 12.5 FPS inside a rounded archival film contact sheet panel (`ARCHIVAL FOOTAGE // 25.01.1995 // 48TH MINUTE`).
- Triggered precisely on the narration impact cue ($t_b \ge 3.5\text{s}$) while keeping the photographic composition dominant.

### 3. Five Reusable Banner Variants & Stock Library
- Five genuinely distinct headline banner designs (`fs30/story_pipeline/paper_widgets.py`):
  - **Variant A**: Torn newspaper edge with heavy left crimson stripe.
  - **Variant B**: Folded ivory paper with distressed red felt-tip marker tab.
  - **Variant C**: Rough-cut archival paper with corner tab and brass rivet.
  - **Variant D**: Narrow editorial strip with textured crimson underline.
  - **Variant E**: Layered paper sandwich with offset crimson backing.
- **43-Asset Reusable Stock Library** (`asset_manifest.json`): Banners, quote cards, photo frames, date labels, rubber stamps, paper textures, and match tickets.

### 4. Dynamic MrBeast-Style Animated Captions
- Dedicated kinetic subtitle engine (`fs30/story_pipeline/mrbeast_captions.py`).
- **Typography**: Heavy condensed sans (`Impact`, 64pt, uppercase).
- **Word-Level Highlighting**: Spoken word illuminates in **Electric Neon Yellow** (`#FFE800`), with climax words (`KICK`, `BANNED`, `KING`, `RED`) popping in **Crimson** (`#FF2D41`).
- **Tactile Scale Bounce**: Word expands $1.14\times \to 1.06\times$ on activation over 120ms.
- **100% Contrast**: Heavy 12px pure black stroke and deep $(+6\text{px}, +7\text{px})$ 3D drop shadow.
- **Burst Cadence**: 2–4 words per phrase (e.g. `JANUARY 1995`, `SELHURST PARK`, `STUDS-FIRST FLYING KICK`).

### 5. Script & British Scholar Voiceover
- Calm, articulate British documentary presenter tone (`Ryan`, Qwen3-TTS on CUDA).
- Subtle, dry intellectual irony (*"shadows Eric Cantona like a zealous tax collector"*, *"Apparently, even kings can be sent to their rooms"*).
- Historically verified suspension terms, dates, and legal outcomes.
- Mastered audio with sidechain-ducked score (*Opportunity Walks*) and broadcast EBU R128 loudness compliance (**-14.0 LUFS**, $\le -1.0\text{ dBTP}$).

### 6. Synchronized Spoken Outro
- Narrative ends naturally with a musical pause, transitioning to the official FS30 brand card at 56.0s.
- 580px FS30 logo badge slam entrance with ambient radial spotlight glow.
- Synchronized spoken farewell from the same presenter:
  *"See you later. This is Football in 30 Seconds. Follow for more."*
  aligned with `THIS IS FOOTBALL IN 30s.`, `NEW STORIES EVERY WEEK.`, and `FOLLOW FOR MORE.`

---

## 🏛️ Final Masters Vault & Catalog

All approved master productions are archived in `final_masters_vault/` and cataloged in `final_masters_vault/masters_catalog.csv`:

| Code | Title | Date | Duration | Resolution | Captions | Audio |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **FS30-HIST-001** | *The King's Madness: Eric Cantona Kung-Fu Kick* | 1995-01-25 | 60.00s | 1080x1920 | MrBeast Kinetic | EBU R128 (-14.3 LUFS) |
| **FS30-HIST-002** | *The Majestic Tragedy: Zinedine Zidane 2006 World Cup Headbutt* | 2006-07-09 | 60.00s | 1080x1920 | MrBeast Kinetic | EBU R128 (-14.2 LUFS) |

---

## 📁 Repository Structure

```
football-video-pipeline/
├── install.bat                     # 1-Click automated Windows installer
├── start.bat                       # Studio control center & launcher
├── requirements.txt                # Production dependencies
├── .gitignore                      # Secure compartmentalization
├── final_masters_vault/            # Production archive for master releases
│   ├── masters_catalog.csv         # Master video registry & metadata
│   ├── FS30-HIST-001/              # Cantona 1995 master package
│   │   ├── cantona_kungfu_master_60s.mp4
│   │   ├── cantona_mastered_audio_60s.wav
│   │   ├── cantona_master_12beat_contact_sheet.png
│   │   ├── cantona_mrbeast_captions.json
│   │   └── qa_report.md
│   └── FS30-HIST-002/              # Zidane 2006 master package
│       ├── zidane_headbutt_master_60s.mp4
│       ├── zidane_mastered_audio_60s.wav
│       ├── zidane_master_12beat_contact_sheet.png
│       ├── zidane_mrbeast_captions.json
│       └── qa_report.md
├── fs30/
│   └── story_pipeline/             # Modular documentary engine
│       ├── photo_mounter.py        # Proportional scaling & focus crop
│       ├── mrbeast_captions.py     # Animated kinetic captions
│       ├── paper_widgets.py        # 5 banner variants & paper widgets
│       ├── branding.py             # FS30 badge outro & TV watermark
│       ├── audio_engine.py         # EBU R128 audio mastering
│       └── assets/reusable_stock/  # 43 verified assets + manifest
├── runs/
│   ├── cantona_kungfu_kick_story/  # Cantona 1995 run directory
│   └── zidane_headbutt_story/      # Zidane 2006 run directory
└── stages/
    └── qwen_tts_synthesizer.py     # Qwen3-TTS local CUDA voiceover
```

---

## 📜 License & Usage Rights

- Archival footage and historic photography used under Fair Use / Fair Dealing provisions for documentary commentary, historical analysis, and education.
- Musical score: *Opportunity Walks* by Kevin MacLeod (incompetech.com), Licensed under Creative Commons: By Attribution 4.0.
