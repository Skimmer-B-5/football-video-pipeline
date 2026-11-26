# Operations & Pipeline Runbook

## 1. Environment & Configuration

### `.env` Variables
Copy `.env.example` to `.env`:
- `TELEGRAM_BOT_TOKEN`: BotFather token for `@Football30secbot`
- `TELEGRAM_CHAT_ID`: Authorized target chat ID
- `GROQ_API_KEY` / `GROQ_API_KEY_BACKUP`: Primary & backup Groq API keys (`BETA_GROQ_API_KEY*` fallbacks are also still honored by `stages/groq_client.py`)
- `GEMINI_API_KEY`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `BING_API_KEY`: Optional vision/image backends
- `YOUTUBE_CLIENT_SECRETS_FILE`, `YOUTUBE_TOKEN_FILE`: OAuth paths (`config/client_secret.json`, `config/youtube_token.json`)

### Central Configuration (`config/config.yaml`)
- `paths.db_path`: `data/news.db` (SQLite WAL database storing scraped articles, jobs, and Telegram approval states)
- `paths.retention_db`: `data/retention.db` (SQLite database tracking rendered video parameters)
- `models.*`: `models/qwen3_tts_base`, `models/jeff_stelling_prompt.pt`, `models/martin_tyler_prompt.pt`, `models/kokoro-v0_19.onnx`
- `youtube.allow_public_upload`: **`false`** by default (`stages/youtube_uploader.py` uploads as `private` or creates a local `MOCK_VERIFIED` ledger receipt in `evidence/youtube_upload_receipt.json` if OAuth credentials are absent).

---

## 2. Running the Main Pipeline

### Telegram Studio Bot Service
```cmd
.venv\Scripts\python.exe -u run_telegram_broadcast_service.py
```
Or via the wrapper / Windows scripts:
```cmd
.venv\Scripts\python.exe -u run_pipeline_service.py
start_engine.bat
```
Supported Telegram workflow actions:
- `/new`: Scrapes live configured feeds, ranks clusters, presents top candidates with inline pagination.
- Send any football article URL directly: Scrapes and builds a broadcast draft immediately.
- Interactive script review buttons: `[Approve]`, `[AI Rewrite]`, `[Manual Edit]`, `[Reject]`.
- Automatic EN render (`FootballShort`) + optional `ES-419` / `PT-BR` localized masters delivered directly in chat.

### CLI Pipeline (`run_pipeline.py`)
```cmd
# Autonomous top-story pipeline
.venv\Scripts\python.exe -u run_pipeline.py --auto

# Direct story / URL
.venv\Scripts\python.exe -u run_pipeline.py --story "Arsenal prepare opening offer for Nico Williams"
.venv\Scripts\python.exe -u run_pipeline.py --url "https://..."

# Script/plan dry-run or FFmpeg fallback engine
.venv\Scripts\python.exe -u run_pipeline.py --auto --dry-run
.venv\Scripts\python.exe -u run_pipeline.py --story "..." --engine ffmpeg

# Single-stage execution
.venv\Scripts\python.exe -u run_pipeline.py --stage collector
.venv\Scripts\python.exe -u run_pipeline.py --stage ranker
```

### Multilingual Production Script
```cmd
.venv\Scripts\python.exe -u execute_multilang_production.py
```

---

## 3. Running the 2.5D Documentary Experiment (`fs30/`)

```cmd
.venv\Scripts\python.exe -u -m fs30.story_pipeline.runner --topic "Luis Suarez biting Liverpool Ajax Chiellini saga" --run-dir runs\suarez_doc
```
Outputs are written under `runs/<run_dir>/` (`story_package.json`, `visual_manifest.json`, `remotion_doc_props.json`, `audio/mastered_documentary_audio.wav`, and `<slug>_25d_master.mp4`).

Note: Remotion stages temporary beat assets into `remotion/public/doc_stories/` and news story assets into `remotion/public/images/`. Both directories are `.gitignored`.

---

## 4. Remotion Studio Preview & Checks
```cmd
cd remotion
npx remotion compositions src/index.ts
npx remotion studio
```

---

## 5. Verification Tests
```cmd
# Core promoted root pipeline, DB, safety defaults & Remotion structure
.venv\Scripts\python.exe tests\test_pipeline_core.py

# Preserved fs30 experiment stage 1-3 checks
.venv\Scripts\python.exe -m unittest tests.test_fs30_stages_1_to_3

# Editorial & CV framing regression suites
.venv\Scripts\python.exe -m unittest tests.test_editorial_intelligence
```

---

## 6. Accessing Legacy Pipeline Code via Git
To inspect or restore the historical pre-promotion pipelines:
```bash
# Pre-promotion snapshot (root wrappers + isolated /beta)
git checkout legacy

# Original V1 pipeline (root stages/, pipeline/, remotion/, run.py)
git checkout legacy-v1
```
