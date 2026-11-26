# ⚽ 30 Football Plus & FS30 Studio

An automated vertical video production platform (`1080x1920`, `30fps`, `-14.0 LUFS` stereo) for **YouTube Shorts**, **Instagram Reels**, and **TikTok**, combining:

1. **Main Production Pipeline (Promoted from `/beta`)**: A 90s Sony Trinitron CRT football broadcast news & transfer short engine with live multi-feed scraping, fact checking, CUDA identity verification, multilingual output (`EN`, `ES-419`, `PT-BR`), Remotion rendering (`FootballShort`), and remote Telegram studio control (`@Football30secbot`).
2. **2.5D Documentary Experiment (`fs30/`)**: A Vox / tactile paper-cut mini-documentary engine preserved under `fs30/` with a sarcastic British `qwen3_tts_base` voice clone, 8 alternating 2.5D compositing layouts (`DocumentaryPaperShort`), live SVG marker circles, highlighter sweeps, and animated camera multiplane motion.

---

## 📁 Organized Repository Structure

```text
football-video-pipeline/
├── run_telegram_broadcast_service.py  # Main Telegram Studio Daemon (@Football30secbot)
├── run_pipeline_service.py            # Service launcher delegating to Telegram daemon
├── run_pipeline.py                    # Main CLI runner (--story / --url / --auto / --stage)
├── execute_multilang_production.py    # Multi-language EN / ES-419 / PT-BR batch runner
├── start.bat / start_engine.bat       # Windows studio launchers
├── install.bat / setup_and_run.bat    # Environment & CUDA PyTorch bootstrap scripts
├── pipeline/                          # Core broadcast orchestrators & SQLite state managers
│   ├── broadcast_story_pipeline.py    # Generalized 8-scene 90s TV broadcast assembly & render
│   ├── multilang_orchestrator.py      # EN / ES-419 / PT-BR orchestration
│   ├── neural_instructions.py         # StoryDossier schema, screenplay prompts, CRT/voice specs
│   ├── orchestrator.py                # Subprocess stage orchestrator
│   ├── resource_monitor.py            # RAM / VRAM usage tracker
│   ├── retention_tracker.py           # Retention metrics SQLite DB (data/retention.db)
│   └── state_manager.py               # Jobs/articles SQLite state DB (data/news.db)
├── stages/                            # Core modular pipeline stages
│   ├── groq_client.py                 # Dual-key Groq client (GPT-OSS-120B / 20B / Qwen-27B)
│   ├── collector.py / ranker.py       # RSS/ESPN/Reddit/Google News ingest & ranking
│   ├── fact_checker.py / claim_*.py   # Grounding verification & 4-gate editorial policy
│   ├── editorial_image_sourcer.py     # Real press/match photo sourcing (zero reuse)
│   ├── semantic_image_procurement.py  # CUDA FasterRCNN + OpenCV YuNet/SFace identity check
│   ├── action_aware_cropper.py        # 9:16 portrait, dual-landscape & cut-out framing
│   ├── production_voice_engine.py     # Qwen3-TTS Aiden anchor + Edge-TTS fallback + mastering
│   ├── multilang_engine.py            # Syllable-budgeted ES-419 & PT-BR localization
│   ├── remotion_renderer.py           # Remotion props prep & CLI invocation
│   ├── telegram_bot.py                # Interactive approvals, progress bars & pagination
│   └── youtube_uploader.py            # OAuth YouTube uploader (private by default)
├── remotion/                          # Unified Remotion Studio (1080x1920 @ 30fps)
│   ├── src/FootballShort.tsx          # Main 90s broadcast CRT composition
│   ├── src/DocumentaryPaperShort.tsx  # Experiment 2.5D tactile collage composition
│   └── src/Root.tsx                   # Composition registry & bundled OFL fonts
├── fs30/                              # Preserved 2.5D Documentary Experiment
│   ├── story_pipeline/                # Active 8-beat 2.5D documentary engine (runner.py)
│   └── stage1..8 / assets / config.py # Historical paper-cut stages & stock asset toolkit
├── config/                            # Central configuration & typography design tokens
│   ├── config.yaml                    # Feeds, models, paths, rendering & upload settings
│   ├── typography.py / typography.ts  # Shared font & safe-zone tokens
│   └── design_tokens.py               # Broadcast coordinate constants
├── assets/                            # Shared OFL fonts & experiment textures/stock/SFX
├── data/                              # Active SQLite DBs (news.db, retention.db), branding, voices, music, sfx
├── models/                            # Local weights (Qwen3-TTS Base/CustomVoice, YuNet, SFace, prompts)
├── prompts/                           # Experiment stage prompt templates (fs30/)
├── tests/                             # Verification suites (core, editorial, fs30, regression)
├── docs/                              # Architecture & operational runbooks
├── final_masters_vault/               # Archived verified master videos & catalog CSV
├── runs/ / workspaces/                # Runtime execution outputs (.gitignored)
├── logs/ / output/ / cache/           # Local logs, staging & cache (.gitignored)
└── evidence/                          # Diagnostic artifacts (.gitignored except .gitkeep)
```

---

## ⚡ Quick Start

### 1. Environment Setup
Copy `.env.example` to `.env` and fill in your credentials (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GROQ_API_KEY`, optional `GROQ_API_KEY_BACKUP`, `GEMINI_API_KEY`):
```cmd
install.bat
```

### 2. Run the Main Production Pipeline

**Interactive Telegram Studio Daemon (Recommended):**
```cmd
.venv\Scripts\python.exe -u run_telegram_broadcast_service.py
```
Then send `/new` in Telegram (`@Football30secbot`), pick a scraped story (or paste a URL), review/edit the generated screenplay via inline buttons, and receive the mastered `1080x1920` broadcast short (plus optional `ES-419` / `PT-BR` localizations).

**Direct CLI Run:**
```cmd
.venv\Scripts\python.exe -u run_pipeline.py --auto
.venv\Scripts\python.exe -u run_pipeline.py --story "Club news text" --dry-run
```

**Windows Launcher Menu:**
```cmd
start.bat
```

### 3. Run the 2.5D Documentary Experiment (`fs30/`)
```cmd
.venv\Scripts\python.exe -u -m fs30.story_pipeline.runner --topic "Eric Cantona kung fu kick Selhurst Park 1995"
```

---

## 🧪 Verification Tests
```cmd
.venv\Scripts\python.exe tests\test_pipeline_core.py
.venv\Scripts\python.exe -m unittest tests.test_fs30_stages_1_to_3
.venv\Scripts\python.exe -m unittest tests.test_editorial_intelligence
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/PIPELINES_AND_OPERATIONS.md](docs/PIPELINES_AND_OPERATIONS.md) for deep technical details and legacy git archive instructions (`legacy` branch & `legacy-v1` tag).
