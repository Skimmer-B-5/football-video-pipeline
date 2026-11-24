# 30' Football Plus — Isolated Beta Pipeline

An isolated, sandbox copy of the **30' Football Plus** (90s retro TV sports broadcast) video production pipeline.

> [!IMPORTANT]
> **Production Protection Guarantee**:
> This directory (`beta/`) is completely isolated from the production pipeline.
> - **Zero shared runtime state**: Uses its own SQLite database (`beta/data/beta_news.db`), retention database (`beta/data/beta_retention.db`), intermediate media caches, and logs.
> - **Zero production overwrites**: All outputs are saved to `beta/output/` and evidence reports to `beta/evidence/`.
> - **Zero automatic publishing**: The YouTube uploader is strictly mocked in beta (`MOCK_VERIFIED`) to ensure experimental videos are never published to production channels.
> - **Production Stability**: Production entry points (`run.py`, `run_pipeline_service.py`, `start.bat`) continue operating completely untouched.

---

## 1. Directory Structure

```text
beta/
├── README.md                           # This documentation & provenance registry
├── run_beta.py                         # Independent CLI runner & stage dispatcher
├── .env.example                        # Beta-isolated environment template
├── .gitignore                          # Beta-local exclusion rules
├── requirements.txt                    # Python dependencies
├── config/
│   ├── config.yaml                     # Beta-isolated runtime configuration
│   └── design_tokens.py                # Broadcast layout, colors & typography tokens
├── pipeline/
│   ├── orchestrator.py                 # Isolated subprocess orchestrator
│   ├── state_manager.py                # Beta SQLite state manager (beta_news.db)
│   ├── resource_monitor.py             # RAM/VRAM resource monitor & ledger
│   └── retention_tracker.py            # Beta retention DB (beta_retention.db)
├── stages/
│   ├── schema_v2.py                    # Scene plan contract & schema validator
│   ├── groq_client.py                  # LLM inference client (supports BETA_GROQ_API_KEY)
│   ├── script_generator.py             # Script & scene plan generator with offline fallback
│   ├── claim_checker.py                # Factual verification against source text
│   ├── reddit_harvester.py             # Fan sentiment & debate harvester
│   ├── collector.py                    # RSS & web article collector
│   ├── ranker.py                       # Story clustering & recency-decay ranker
│   ├── image_sourcing.py               # Real match photo sourcing & deduplication
│   ├── image_scrapers.py               # Wikimedia & Wikipedia REST scrapers
│   ├── image_quality_sensor.py         # Laplacian blur & solid color rejection
│   ├── visual_agent.py                 # Visual planning & upper-third focal bias
│   ├── meme_vault.py                   # Contextual sports meme personality catalog
│   ├── jeff_stelling_synthesizer.py    # Jeff Stelling voice clone (Qwen3-TTS Base)
│   ├── tts_synthesizer.py              # Expressive neural speech synthesizer
│   ├── subtitles_engine.py             # Burned-in caption & SRT generator
│   ├── video_assembler.py              # FFmpeg 90s TV broadcast assembler
│   ├── remotion_renderer.py            # Remotion React composition renderer
│   ├── qa_engine.py                    # Engine QA suite (loudness, geometry, black frames)
│   ├── verify_video.py                 # Media stream & duration validator
│   ├── see_back.py                     # Self-healing visual audit
│   └── youtube_uploader.py             # STRICT OFFLINE MOCK: Staged locally only
├── remotion/
│   ├── package.json                    # Remotion project configuration
│   ├── package-lock.json
│   ├── remotion.config.ts
│   ├── tsconfig.json
│   ├── node_modules/                   # NTFS junction to shared node_modules
│   └── src/
│       ├── FootballShort.tsx           # Primary 9:16 composition (Series of scenes)
│       ├── Root.tsx                    # Composition registration
│       ├── index.ts                    # Remotion entrypoint
│       ├── types.ts                    # TypeScript types
│       ├── design/tokens.ts            # Remotion layout, color & spring physics tokens
│       └── components/
│           ├── TopHUD.tsx              # Channel bezel TV bug & status badge
│           ├── LowerThird.tsx          # 2-tier extruded broadcast headline plate
│           ├── RollingTicker.tsx       # 3D metallic news ticker tape
│           ├── RetroOverlay.tsx        # CRT scanlines & curved tube vignette
│           ├── SubtitleCard.tsx        # Floating phrase caption card
│           ├── OutroPlate.tsx          # 1.2s broadcast branding sign-off
│           ├── BackgroundMedia.tsx     # Full 9:16 match photography layer
│           └── infographics/           # Dynamic animated stats & clause cards
├── data/
│   ├── branding/                       # TV bugs, 3D ticker rails & outro audio
│   ├── fonts/                          # Barlow Condensed Bold & ExtraBold
│   ├── retro_90s/                      # crt_scanlines.png
│   ├── sfx/                            # Broadcast transition & breath sound effects
│   ├── audio/                          # Beta synthesized scene audio
│   └── images/                         # Beta sourced match images
├── cache/                              # Isolated temporary download cache
├── logs/                               # Isolated per-run logs
├── output/                             # Master rendered video outputs (*_final.mp4)
├── evidence/                           # QA reports, contact sheets & ledgers
└── tests/
    └── test_beta_pipeline.py           # Beta isolation test suite
```

---

## 2. Module Provenance Registry

Every module in `beta/` has been adapted with a provenance header indicating its source:

| Beta File | Source File in Production | Key Adaptations / Isolation Safeguards |
| :--- | :--- | :--- |
| `beta/config/config.yaml` | `config/config.yaml` | Scoped all data/output paths to `beta/`; `allow_public_upload: false`. |
| `beta/config/design_tokens.py` | `config/design_tokens.py` | Identical source of truth for broadcast coordinates and colors. |
| `beta/pipeline/orchestrator.py` | `pipeline/orchestrator.py` | Isolated subprocess launcher with `PYTHONPATH=beta/`; output to `beta/output/`. |
| `beta/pipeline/state_manager.py` | `pipeline/state_manager.py` | Dedicated database at `beta/data/beta_news.db`. |
| `beta/pipeline/resource_monitor.py` | `pipeline/resource_monitor.py` | Ledger writes to `beta/evidence/resource_ledger.json`. |
| `beta/pipeline/retention_tracker.py` | `pipeline/retention_tracker.py` | Dedicated database at `beta/data/beta_retention.db`. |
| `beta/stages/script_generator.py` | `stages/script_generator.py` | Added offline heuristic Schema v2.0 fallback for API-free testing. |
| `beta/stages/groq_client.py` | `stages/groq_client.py` | Supports `BETA_GROQ_API_KEY` from `beta/.env`. |
| `beta/stages/image_sourcing.py` | `stages/image_sourcing.py` | Scoped media downloads to `beta/data/images/`. |
| `beta/stages/tts_synthesizer.py` | `stages/tts_synthesizer.py` | Scoped audio outputs to `beta/data/audio/`; reads root `models/` read-only. |
| `beta/stages/jeff_stelling_synthesizer.py` | `stages/jeff_stelling_synthesizer.py` | Scoped audio outputs to `beta/data/audio/`. |
| `beta/stages/remotion_renderer.py` | `stages/remotion_renderer.py` | Scoped execution to `beta/remotion/` and outputs to `beta/output/`. |
| `beta/stages/video_assembler.py` | `stages/video_assembler.py` | Scoped assets to `beta/data/` and outputs to `beta/output/`. |
| `beta/stages/youtube_uploader.py` | `stages/youtube_uploader.py` | **Hardcoded safe mock**: Returns `MOCK_VERIFIED`, zero external publishing. |
| `beta/stages/qa_engine.py` | `stages/qa_engine.py` | Reports written to `beta/evidence/`. |

---

## 3. How to Run the Beta Pipeline

### Run Full End-to-End Cycle (Custom Story)
```cmd
.\.venv\Scripts\python.exe beta/run_beta.py --story "Your football story text here..."
```

### Dry Run (Script and Scene Plan Only)
```cmd
.\.venv\Scripts\python.exe beta/run_beta.py --story "Your football story text here..." --dry-run
```

### Choose Render Engine
```cmd
:: Using Remotion React Engine (default)
.\.venv\Scripts\python.exe beta/run_beta.py --story "..." --engine remotion

:: Using Standalone FFmpeg Engine
.\.venv\Scripts\python.exe beta/run_beta.py --story "..." --engine ffmpeg
```

### Run Automated Feed Ingestion Mode
```cmd
.\.venv\Scripts\python.exe beta/run_beta.py --auto
```

### Run Isolation Verification Tests
```cmd
.\.venv\Scripts\python.exe beta/tests/test_beta_pipeline.py
```
