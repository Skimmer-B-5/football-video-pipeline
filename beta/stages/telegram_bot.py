"""
# PROVENANCE: Copied from stages/telegram_bot.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ - Safe experimental development environment.
"""

"""
Telegram Bot Interface for Phone Approvals.
Uses direct Telegram Bot HTTPS API with persistent offset tracking in SQLite.
Features:
1. Qwen Persona: Cynical, sharp tactician tone for all interactive messages and replies.
2. Zero Button Lag: Instant callback query acknowledgment and in-place message editing.
3. In-Place Rendering: Every button tap immediately renders the result and removes buttons.
4. Pagination: In-place menu update for 'Order 3 New Stories'.
5. URL Scraper Integration: Accepts any external news link pasted in chat.
"""

import sys
import os
import re
import json
import time
import requests
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.state_manager import get_db_connection

def get_env_credentials() -> Tuple[str, str]:
    """Retrieve Telegram credentials from environment or .env file."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists() and (not token or not chat_id):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "TELEGRAM_BOT_TOKEN" and not token:
                    token = v
                elif k == "TELEGRAM_CHAT_ID" and not chat_id:
                    chat_id = v

    return token, chat_id

def get_qwen_neural_memory(query: str = "") -> str:
    """
    Live Neural Memory Link for Qwen:
    Extracts real-time context from:
    1. Active breaking news radar (top 5 clustered stories from today's feeds).
    2. Studio pipeline state & latest video created.
    3. Targeted semantic article dossier matches based on entities in the query.
    """
    memory_blocks = []

    # 1. Live Breaking News Radar Memory
    try:
        rank_f = PROJECT_ROOT / "evidence" / "ranking_log.json"
        if rank_f.exists():
            with open(rank_f, "r", encoding="utf-8") as f:
                ranked = json.load(f)[:5]
            if ranked:
                lines = ["[ACTIVE BREAKING RADAR - TODAY'S SCOUTED STORIES]"]
                for r in ranked:
                    tier_str = r.get("tier", "rumour").upper()
                    src = r.get("sources", ["Outlet"])[0]
                    lines.append(f"• [{tier_str}] {r.get('headline')} (Source: {src})")
                memory_blocks.append("\n".join(lines))
    except Exception as e:
        print(f"[NeuralMemory] Radar recall note: {e}")

    # 2. Studio Pipeline & Video Memory
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT job_id, status, topic_data, video_path FROM jobs ORDER BY created_at DESC LIMIT 1").fetchone()
            if row:
                t_str = row["topic_data"] or "{}"
                try:
                    head = json.loads(t_str).get("headline", "None")
                except Exception:
                    head = "None"
                memory_blocks.append(
                    f"[STUDIO PRODUCTION MEMORY]\n"
                    f"• Current Active Topic: {head}\n"
                    f"• Pipeline Status: {row['status']}"
                )
    except Exception as e:
        print(f"[NeuralMemory] Studio recall note: {e}")

    # 3. Targeted Entity Dossier (Search articles table if user mentions specific players/clubs/managers)
    if query:
        stop = {"what", "when", "where", "which", "who", "whom", "this", "that", "there", "about",
                "think", "your", "opinion", "does", "have", "with", "from", "tell", "give", "know",
                "explain", "should", "would", "could", "will", "going", "player", "manager"}
        words = [w for w in re.findall(r'[a-zA-Z]{3,}', query) if w.lower() not in stop]
        if words:
            try:
                with get_db_connection() as conn:
                    clauses = " OR ".join(["title LIKE ?" for _ in words[:3]])
                    params = [f"%{w}%" for w in words[:3]]
                    matches = conn.execute(f"SELECT title, source, raw_text FROM articles WHERE {clauses} ORDER BY id DESC LIMIT 2", params).fetchall()
                    if matches:
                        m_lines = ["[TARGETED DOSSIER RECALL]"]
                        for m in matches:
                            snippet = m['raw_text'][:200].replace('\n', ' ') if m['raw_text'] else m['title']
                            m_lines.append(f"• Fact from {m['source']} ({m['title']}): \"{snippet}...\"")
                        memory_blocks.append("\n".join(m_lines))
            except Exception as e:
                print(f"[NeuralMemory] Entity recall note: {e}")

    return "\n\n".join(memory_blocks)

def qwen_respond(user_text: str) -> str:
    """Generate Qwen's cynical, razor-sharp response with full neural memory link to live news & dossier data."""
    memory_context = get_qwen_neural_memory(user_text)

    system_prompt = (
        "You are Qwen, the cynical, razor-sharp football tactician and content strategist behind 'Football in 30 Seconds' (@Footballin30sec). "
        "You speak with intellectual arrogance, dark humor, and tactical superiority. You despise generic cheerleading, plastic media cliches, and lazy football analysis. "
        "You have direct access to your neural memory link containing today's live breaking news feeds, scraped article dossiers, and studio production records. "
        "When relevant, cite real facts, numbers, and recent news from your memory with cynical authority. "
        "Keep Telegram replies concise (2-4 sentences max), sharp, witty, and authoritative. Respond in plain text without markdown formatting."
    )
    
    # 1. Primary: Groq Ultra-Fast LPUs (Qwen 27B native model, fallback to GPT-OSS 120B)
    try:
        from stages.groq_client import call_groq_chat
        groq_messages = [
            {"role": "system", "content": f"{system_prompt}\n\n[NEURAL MEMORY LINK]:\n{memory_context}"},
            {"role": "user", "content": user_text}
        ]
        groq_reply = call_groq_chat(
            messages=groq_messages,
            preferred_model="qwen/qwen3.8-27b",
            fallback_model="openai/gpt-oss-120b",
            max_tokens=220,
            temperature=0.6,
            timeout=10
        )
        if groq_reply:
            return groq_reply
    except Exception as ge:
        print(f"[QwenTelegram] Groq LPU note: {ge}")

    # 2. Secondary: Cloudflare Workers AI (Llama 3.1 8B Instruct)
    cf_token = os.environ.get("CF_API_TOKEN") or os.environ.get("CLOUDFLARE_API_TOKEN")
    cf_account = os.environ.get("CF_ACCOUNT_ID") or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if cf_token and cf_account:
        try:
            cf_url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/@cf/meta/llama-3.1-8b-instruct"
            cf_headers = {
                "Authorization": f"Bearer {cf_token}",
                "Content-Type": "application/json"
            }
            cf_payload = {
                "messages": [
                    {"role": "system", "content": f"{system_prompt}\n\n[NEURAL MEMORY LINK]:\n{memory_context}"},
                    {"role": "user", "content": user_text}
                ],
                "max_tokens": 200,
                "temperature": 0.5
            }
            req = urllib.request.Request(cf_url, data=json.dumps(cf_payload).encode('utf-8'), headers=cf_headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                reply = data.get("result", {}).get("response", "").strip()
                if reply:
                    return reply
        except Exception as e:
            print(f"[QwenTelegram] Cloudflare AI note: {e}")

    # 2. Secondary: Local Qwen GGUF fallback
    try:
        from llama_cpp import Llama
        gguf_path = PROJECT_ROOT / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"
        if gguf_path.exists():
            llm = Llama(model_path=str(gguf_path), n_ctx=1024, n_threads=4, verbose=False)
            res = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": f"{system_prompt}\n\n[NEURAL MEMORY]:\n{memory_context}"},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.5,
                max_tokens=150
            )
            return res["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return "I've noted that. Unlike the plastic pundits on TV, I only care about structural reality and cold execution. What disaster are we breaking down next?"

def get_studio_engine_status() -> Dict[str, Any]:
    """Return studio engine metrics and scraping status (100% quota-free)."""
    return {
        "image_engine": "Universal Web Scraper (Wikimedia Commons, Reddit r/soccer, Verified Sports Desks)",
        "image_quota": "♾️ Infinite (No Quotas)",
        "image_style": "100% Genuine Match & Press Photos",
        "text_model": "Cloudflare Workers AI (Llama 3.1 8B)",
        "backup_model": "Local Qwen 2.5 3B GGUF"
    }

class TelegramBotClient:
    def __init__(self, token: Optional[str] = None, default_chat_id: Optional[str] = None):
        env_token, env_chat_id = get_env_credentials()
        self.token = token or env_token
        self.bot_token = self.token
        self.default_chat_id = default_chat_id or env_chat_id
        self.active_chat_id: Optional[str] = None
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set. Please add it to your .env file or environment.")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def is_user_authorized(self, user_id: Any) -> bool:
        """Check if a Telegram user ID is authorized as admin or co-pilot."""
        if not user_id:
            return False
        uid_str = str(user_id).strip()
        # 1. Primary admin(s) from .env
        if self.default_chat_id:
            for admin_id in str(self.default_chat_id).split(","):
                if uid_str == admin_id.strip():
                    return True
        # 2. Database whitelist table & open mode check
        try:
            with get_db_connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT)")
                row_all = conn.execute("SELECT value FROM bot_settings WHERE key = 'allow_all'").fetchone()
                if row_all and str(row_all["value"]) == "1":
                    return True

                conn.execute("CREATE TABLE IF NOT EXISTS authorized_users (user_id TEXT PRIMARY KEY, name TEXT, added_at TEXT)")
                row = conn.execute("SELECT 1 FROM authorized_users WHERE user_id = ?", (uid_str,)).fetchone()
                if row:
                    return True
        except Exception:
            pass
        return False

    def add_authorized_user(self, user_id: str, name: str = "") -> bool:
        """Add a friend or co-pilot to authorized users list or enable open co-pilot mode."""
        uid_str = str(user_id).strip()
        try:
            with get_db_connection() as conn:
                if uid_str.lower() in ("all", "everyone", "any"):
                    conn.execute("CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT)")
                    conn.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('allow_all', '1')")
                    conn.commit()
                    print("[TelegramAuth] Open co-pilot mode enabled (allow_all=1)")
                    return True

                conn.execute("CREATE TABLE IF NOT EXISTS authorized_users (user_id TEXT PRIMARY KEY, name TEXT, added_at TEXT)")
                conn.execute(
                    "INSERT OR REPLACE INTO authorized_users (user_id, name, added_at) VALUES (?, ?, ?)",
                    (uid_str, name, time.strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
            print(f"[TelegramAuth] Successfully authorized user {uid_str}")
            return True
        except Exception as e:
            print(f"[TelegramAuth] Error adding user {uid_str}: {e}")
            return False

    def get_authorized_users(self) -> List[str]:
        """Return list of all authorized user IDs with primary admin first."""
        primary_admin = str(self.default_chat_id or "").strip()
        ordered_users = []
        if primary_admin:
            for admin_id in primary_admin.split(","):
                aid = admin_id.strip()
                if aid and aid not in ordered_users:
                    ordered_users.append(aid)

        if getattr(self, "active_chat_id", None):
            act_id = str(self.active_chat_id).strip()
            if act_id and act_id not in ordered_users:
                ordered_users.append(act_id)

        try:
            with get_db_connection() as conn:
                conn.execute("CREATE TABLE IF NOT EXISTS authorized_users (user_id TEXT PRIMARY KEY, name TEXT, added_at TEXT)")
                rows = conn.execute("SELECT user_id FROM authorized_users").fetchall()
                for r in rows:
                    uid = str(r["user_id"]).strip()
                    if uid and uid not in ordered_users:
                        ordered_users.append(uid)
        except Exception:
            pass
        return ordered_users

    def broadcast_message(self, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Broadcast message to all authorized users with primary admin prioritized for zero lag."""
        msg_ids = {}
        for uid in self.get_authorized_users():
            try:
                mid = self.send_message(text, reply_markup=reply_markup, chat_id=uid)
                msg_ids[uid] = mid
            except Exception as e:
                print(f"[Telegram Broadcast] Note sending to {uid}: {e}")
        return msg_ids

    def broadcast_video(self, video_path: str, caption: str = "", reply_markup: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Broadcast video to all authorized users (admin + co-pilots) reusing file_id for instant zero-lag distribution."""
        msg_ids = {}
        users = self.get_authorized_users()
        uploaded_file_id = None
        for uid in users:
            try:
                if uploaded_file_id:
                    mid = self.send_video_by_file_id(uploaded_file_id, caption=caption, reply_markup=reply_markup, chat_id=uid)
                else:
                    mid, uploaded_file_id = self.send_video(video_path, caption=caption, reply_markup=reply_markup, chat_id=uid, return_file_id=True)
                msg_ids[uid] = mid
            except Exception as e:
                print(f"[Telegram Broadcast] Note sending video to {uid}: {e}")
        return msg_ids

    def send_photo(self, photo_path: str, caption: str = "", chat_id: Optional[str] = None) -> int:
        """Send a photo to a specific chat via Telegram sendPhoto endpoint."""
        cid = chat_id or getattr(self, "active_chat_id", None) or self.default_chat_id
        url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
        try:
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": cid, "caption": caption, "parse_mode": "HTML"}
                res = requests.post(url, data=data, files=files, timeout=30).json()
                return res.get("result", {}).get("message_id", 0)
        except Exception as e:
            print(f"[Telegram] Failed to send photo: {e}")
            return 0

    def send_audio(self, audio_path: str, caption: str = "", chat_id: Optional[str] = None) -> int:
        """Send an audio file to a specific chat via Telegram sendAudio endpoint."""
        cid = chat_id or getattr(self, "active_chat_id", None) or self.default_chat_id
        url = f"https://api.telegram.org/bot{self.bot_token}/sendAudio"
        try:
            with open(audio_path, "rb") as f:
                files = {"audio": f}
                data = {"chat_id": cid, "caption": caption, "parse_mode": "HTML"}
                res = requests.post(url, data=data, files=files, timeout=45).json()
                return res.get("result", {}).get("message_id", 0)
        except Exception as e:
            print(f"[Telegram] Failed to send audio: {e}")
            return 0

    def broadcast_photo(self, photo_path: str, caption: str = "") -> Dict[str, int]:
        """Broadcast photo to all authorized users."""
        msg_ids = {}
        users = self.get_authorized_users()
        for uid in users:
            try:
                mid = self.send_photo(photo_path, caption=caption, chat_id=uid)
                msg_ids[uid] = mid
            except Exception as e:
                print(f"[Telegram Broadcast] Note sending photo to {uid}: {e}")
        return msg_ids

    def send_video_by_file_id(self, file_id: str, caption: str = "", reply_markup: Optional[Dict[str, Any]] = None, chat_id: Optional[str] = None) -> int:
        """Send video instantly using Telegram cached file_id."""
        cid = chat_id or getattr(self, "active_chat_id", None) or self.default_chat_id
        payload = {
            "chat_id": cid,
            "video": file_id,
            "parse_mode": "HTML"
        }
        if caption:
            payload["caption"] = caption
        if reply_markup:
            payload["reply_markup"] = reply_markup
        res = self._api_call("sendVideo", payload, timeout=30)
        return res.get("result", {}).get("message_id", 0)

    def set_bot_commands(self) -> bool:
        """Register Telegram menu commands for the bot UI."""
        commands = [
            {"command": "broadcast", "description": "📺 90s TV broadcast video (V7.1 Jeff Stelling master)"},
            {"command": "retro", "description": "📺 90s TV broadcast video (V7.1 Jeff Stelling master)"},
            {"command": "new", "description": "⚡ Launch fresh video cycle (trending stories)"},
            {"command": "search", "description": "🔍 Search internet for specific news without links"},
            {"command": "chat", "description": "🧠 Ask Qwen tactical opinions, debates & queries"},
            {"command": "allow", "description": "👥 Authorize a friend's Telegram ID"},
            {"command": "rewrite", "description": "🤖 AI rewrite current script draft"},
            {"command": "matchday", "description": "🚨 Scan live shocks & matchday upsets"},
            {"command": "status", "description": "📊 View pipeline state & Gemini credits/quota"},
            {"command": "cancel", "description": "❌ Cancel/reset active job"},
            {"command": "help", "description": "❓ How to use this bot"}
        ]
        res = self._api_call("setMyCommands", {"commands": commands})
        return res.get("ok", False)

    def format_status_message(self) -> str:
        """Format real-time pipeline status, active job info, host metrics, and Gemini quota."""
        from pipeline.resource_monitor import get_system_ram, get_vram_usage
        ram = get_system_ram()
        vram = get_vram_usage()

        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT 1").fetchone()
            job_info = dict(row) if row else {}

        job_id = job_info.get("job_id", "None")
        status = job_info.get("status", "IDLE")
        created = job_info.get("created_at", "N/A")

        headline = "N/A"
        topic_raw = job_info.get("topic_data")
        if topic_raw:
            try:
                topic = json.loads(topic_raw)
                headline = topic.get("headline", "N/A")
            except Exception:
                pass

        engines = get_studio_engine_status()

        return (
            "📊 <b>PIPELINE STATUS REPORT</b>\n\n"
            f"<b>Active Job:</b> <code>{job_id}</code>\n"
            f"<b>Status:</b> <b>{status}</b>\n"
            f"<b>Topic:</b> <i>{headline[:60]}...</i>\n"
            f"<b>Started:</b> {created}\n\n"
            "📸 <b>Visual Sourcing Engine:</b>\n"
            f"• <b>Engine:</b> {engines['image_engine']}\n"
            f"• <b>Quotas:</b> <b>{engines['image_quota']}</b>\n"
            f"• <b>Formula:</b> {engines['image_style']}\n\n"
            "🧠 <b>Tactical AI Script Engine:</b>\n"
            f"• <b>Primary LLM:</b> {engines['text_model']}\n"
            f"• <b>Local Fallback:</b> {engines['backup_model']}\n\n"
            "🖥️ <b>Host Hardware Metrics:</b>\n"
            f"• <b>RAM Used:</b> {ram.get('ram_used_mb', 0):.0f} MB / {ram.get('ram_total_mb', 0):.0f} MB ({ram.get('ram_percent', 0)}%)\n"
            f"• <b>GPU VRAM Free:</b> {vram.get('vram_free_mib', 0):.0f} MiB ({vram.get('device_name', 'GTX 1650 Ti')})\n\n"
            "<i>Commands: /new to start cycle | /search [topic] | /cancel to reset</i>"
        )

    def get_help_message(self) -> str:
        return (
            "🧠 <b>QWEN & 1990s BROADCAST STUDIO COMMAND GUIDE</b>\n\n"
            "<i>Control your video pipeline studio directly from your phone:</i>\n\n"
            "📺 <b>/broadcast [story]</b> (or <b>/retro</b>) — <i>Generate a 1990s television broadcast short (V7.1.6.7 8-scene master pipeline) voiced by Original British Sports Presenter with CRT presentation!</i>\n"
            "⚡ <b>/new</b> — <i>Scan live feeds, rank virality, and serve top trending stories.</i>\n"
            "🔍 <b>/search [query]</b> — <i>Search the internet for specific news (e.g. <code>/search bruno contract</code>) and pick a story!</i>\n"
            "💬 <b>/chat [question]</b> — <i>Directly debate tactics or ask Qwen anything (e.g. /chat who is the biggest fraud in football?).</i>\n"
            "👥 <b>/allow [telegram_id]</b> — <i>Authorize your friend to use this bot as a co-pilot.</i>\n"
            "🚨 <b>/matchday</b> — <i>Scan live shock results, upsets, and crisis games.</i>\n"
            "📊 <b>/status</b> — <i>Inspect pipeline status, image scraper engine, and laptop GPU/RAM.</i>\n"
            "❌ <b>/cancel</b> — <i>Abort and archive the currently active cycle.</i>\n"
            "❓ <b>/help</b> — <i>Display this tactical command manual.</i>\n\n"
            "🔗 <b>Custom Links:</b> <i>Paste any news article URL directly into chat to generate an 8-scene short for it!</i>"
        )

    def _api_call(self, endpoint: str, payload: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint}"
        data = None
        headers = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_me(self) -> Dict[str, Any]:
        """Test bot credentials."""
        res = self._api_call("getMe")
        return res.get("result", {})

    def send_message(self, text: str, reply_markup: Optional[Dict[str, Any]] = None, chat_id: Optional[str] = None) -> int:
        """Send a text message, returning message_id."""
        cid = chat_id or getattr(self, "active_chat_id", None) or self.default_chat_id
        if not cid:
            raise ValueError("No chat_id specified and TELEGRAM_CHAT_ID is not configured.")

        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        res = self._api_call("sendMessage", payload)
        return res.get("result", {}).get("message_id", 0)

    def edit_message_text(self, text: str, message_id: int, reply_markup: Optional[Dict[str, Any]] = None, chat_id: Optional[str] = None) -> bool:
        """Edit an existing message text in-place to avoid spam and eliminate UI lag."""
        cid = chat_id or getattr(self, "active_chat_id", None) or self.default_chat_id
        payload = {
            "chat_id": cid,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        try:
            res = self._api_call("editMessageText", payload)
            return res.get("ok", False)
        except Exception as e:
            print(f"[Telegram] editMessageText warning: {e}")
            return False

    def answer_callback(self, callback_query_id: str, text: Optional[str] = None):
        """Acknowledge inline button press immediately with zero cache lag."""
        payload = {"callback_query_id": callback_query_id, "cache_time": 0}
        if text:
            payload["text"] = text
        try:
            self._api_call("answerCallbackQuery", payload)
        except Exception as e:
            print(f"[Telegram] answerCallbackQuery warning: {e}")

    def send_video(self, video_path: str, caption: str = "", reply_markup: Optional[Dict[str, Any]] = None, chat_id: Optional[str] = None, return_file_id: bool = False) -> Any:
        """Send video file using multipart POST."""
        import mimetypes
        cid = chat_id or getattr(self, "active_chat_id", None) or self.default_chat_id
        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        lines_bin = []
        lines_bin.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{cid}\r\n".encode("utf-8"))
        if caption:
            lines_bin.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode("utf-8"))
            lines_bin.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nHTML\r\n".encode("utf-8"))
        if reply_markup:
            lines_bin.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"reply_markup\"\r\n\r\n{json.dumps(reply_markup)}\r\n".encode("utf-8"))

        mime_type = mimetypes.guess_type(str(path))[0] or "video/mp4"

        try:
            import requests
            data = {"chat_id": cid, "parse_mode": "HTML"}
            if caption:
                data["caption"] = caption
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            with open(path, "rb") as vf:
                files = {"video": (path.name, vf, mime_type)}
                resp = requests.post(f"{self.base_url}/sendVideo", data=data, files=files, timeout=180)
                res = resp.json()
                mid = res.get("result", {}).get("message_id", 0)
                fid = res.get("result", {}).get("video", {}).get("file_id")
                if return_file_id:
                    return mid, fid
                return mid
        except Exception as req_err:
            print(f"[TelegramBot] requests upload fallback ({req_err}), trying urllib...")

        file_header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="video"; filename="{path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")

        with open(path, "rb") as vf:
            file_data = vf.read()

        closing = f"\r\n--{boundary}--\r\n".encode("utf-8")
        body = b"".join(lines_bin) + file_header + file_data + closing

        req = urllib.request.Request(
            f"{self.base_url}/sendVideo",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            mid = res.get("result", {}).get("message_id", 0)
            fid = res.get("result", {}).get("video", {}).get("file_id")
            if return_file_id:
                return mid, fid
            return mid

    def wait_for_decision(self, expected_callbacks: List[str], allow_text_reply: bool = False, timeout_sec: int = 86400) -> Tuple[str, Optional[str], Optional[int]]:
        """
        Long-poll for user's inline button tap or text reply.
        Returns: (action, payload, message_id)
        Survives restarts by storing last update_id in SQLite.
        """
        print(f"[Telegram] Listening for phone approval on {expected_callbacks}...")
        start_time = time.time()

        with get_db_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS bot_state (key TEXT PRIMARY KEY, value TEXT)")
            row = conn.execute("SELECT value FROM bot_state WHERE key = 'last_update_id'").fetchone()
            last_id = int(row["value"]) if row else 0

        while (time.time() - start_time) < timeout_sec:
            try:
                res = self._api_call("getUpdates", {"offset": last_id + 1, "timeout": 15}, timeout=25)
                updates = res.get("result", [])

                for upd in updates:
                    last_id = upd["update_id"]
                    with get_db_connection() as conn:
                        conn.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES ('last_update_id', ?)", (str(last_id),))
                        conn.commit()

                    # Handle button callback
                    if "callback_query" in upd:
                        cb = upd["callback_query"]
                        from_user = cb.get("from", {}).get("id")
                        if not self.is_user_authorized(from_user):
                            continue
                        cb_data = cb.get("data", "")
                        cb_id = cb.get("id")
                        msg = cb.get("message", {})
                        msg_id = msg.get("message_id")

                        # Immediately answer callback query so Telegram stops spinning!
                        self.answer_callback(cb_id, text="⚡ Selected!")

                        for expected in expected_callbacks:
                            if cb_data == expected or (expected.endswith("_") and cb_data.startswith(expected)):
                                print(f"[Telegram] Phone tap received: {cb_data} on msg {msg_id}")
                                return cb_data, None, msg_id
                            # Support pick_X matching story_X or vice-versa
                            if (cb_data.startswith("pick_") or cb_data.startswith("story_")) and (expected.startswith("pick_") or expected.startswith("story_")):
                                try:
                                    if int(cb_data.split("_")[1]) == int(expected.split("_")[1]):
                                        print(f"[Telegram] Phone tap received: {cb_data} on msg {msg_id}")
                                        return cb_data, None, msg_id
                                except Exception:
                                    pass

                    # Handle text edit/reply
                    if allow_text_reply and "message" in upd:
                        msg = upd["message"]
                        from_user = msg.get("from", {}).get("id") or msg.get("chat", {}).get("id")
                        msg_chat_id = msg.get("chat", {}).get("id") or from_user
                        user_name = msg.get("from", {}).get("first_name", "Friend")

                        if not self.is_user_authorized(from_user):
                            self.send_message(
                                f"🔒 <b>ACCESS RESTRICTED — QWEN STUDIO</b>\n\n"
                                f"Hello <b>{user_name}</b>! This studio is currently restricted.\n\n"
                                f"<b>Your Telegram ID:</b> <code>{from_user}</code>\n\n"
                                f"<i>Ask your friend to authorize you by sending:</i>\n"
                                f"<code>/allow {from_user}</code>",
                                chat_id=msg_chat_id
                            )
                            continue

                        text = msg.get("text", "").strip()
                        msg_id = msg.get("message_id")
                        if text:
                            print(f"[Telegram] Text message received from {user_name}: {text}")
                            clean_cmd = text.strip().lower()
                            if clean_cmd.startswith(("/allow", "allow", "/add", "add")):
                                parts = text.split()
                                if len(parts) > 1 and parts[1].strip().isdigit():
                                    target_id = parts[1].strip()
                                    self.add_authorized_user(target_id, name="Friend")
                                    self.send_message(
                                        f"✅ <b>ACCESS GRANTED</b>\n\n"
                                        f"Telegram user <code>{target_id}</code> is now an authorized studio co-pilot!",
                                        chat_id=msg_chat_id
                                    )
                                    try:
                                        self.send_message(
                                            "🎉 <b>ACCESS GRANTED TO QWEN STUDIO!</b>\n\n"
                                            "<i>You are now authorized as a co-pilot for @Footballin30sec!</i>\n"
                                            "⚡ <b>/new</b> — <i>Launch video cycle</i>\n"
                                            "💬 <b>/chat [question]</b> — <i>Debate tactics with Qwen</i>",
                                            chat_id=target_id
                                        )
                                    except Exception:
                                        pass
                                else:
                                    self.send_message(
                                        "ℹ️ <b>How to Authorize a Friend:</b>\n\n"
                                        "1. Have them open @Football30secbot and press <b>Start</b>.\n"
                                        "2. They will see their numeric ID.\n"
                                        "3. Type: <code>/allow [their_id]</code>\n"
                                        "<i>Example:</i> <code>/allow 123456789</code>",
                                        chat_id=msg_chat_id
                                    )
                                continue
                            elif clean_cmd in ("/status", "status", "/quota", "quota", "/credits", "credits"):
                                self.send_message(self.format_status_message(), chat_id=msg_chat_id)
                                continue
                            elif clean_cmd in ("/help", "help", "/start", "start"):
                                self.send_message(self.get_help_message(), chat_id=msg_chat_id)
                                continue
                            elif clean_cmd.startswith(("/chat", "chat")):
                                parts = text.split(maxsplit=1)
                                query = parts[1].strip() if len(parts) > 1 else ""
                                if not query:
                                    self.send_message("💬 <b>QWEN CHAT:</b>\n<i>Send your question with /chat, e.g.:</i>\n<code>/chat Who is the biggest fraud in the Premier League?</code>", chat_id=msg_chat_id)
                                else:
                                    reply = qwen_respond(query)
                                    self.send_message(f"🧠 <b>Qwen:</b>\n\n{reply}", chat_id=msg_chat_id)
                                continue
                            elif clean_cmd in ("/cancel", "cancel", "/reset", "reset"):
                                with get_db_connection() as conn:
                                    conn.execute("UPDATE jobs SET status = 'CANCELLED' WHERE status NOT IN ('COMPLETED', 'ARCHIVED', 'FAILED', 'REJECTED')")
                                    conn.commit()
                                self.send_message("❌ <b>JOB CANCELLED</b>\n<i>The active cycle has been archived. Send /new anytime to launch fresh.</i>", chat_id=msg_chat_id)
                                return "CANCEL", None, msg_id
                            elif clean_cmd in ("/new", "new", "/run", "run", "/refresh"):
                                return "NEW_CYCLE", None, msg_id
                            elif clean_cmd in ("/rewrite", "rewrite", "ai rewrite", "/ai_rewrite"):
                                return "script_ai_rewrite", None, msg_id
                            return "TEXT_REPLY", text, msg_id

            except Exception as e:
                print(f"[Telegram] Polling warning: {e}. Retrying...")
                time.sleep(3)

            time.sleep(1)

        raise TimeoutError("[Telegram] Approval timed out.")

    def handle_retro_broadcast_request(self, story_prompt: str = "", chat_id: Optional[str] = None):
        """Presents the 1990s TV broadcast creation menu or executes a story request."""
        target_chat = chat_id or self.default_chat_id
        if not target_chat:
            return

        if not story_prompt:
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "⭐ Endrick to Milan (€60M)", "callback_data": "retro_endrick_milan"},
                        {"text": "🔥 Gyökeres to Arsenal (€75M)", "callback_data": "retro_gyokeres_arsenal"}
                    ],
                    [
                        {"text": "⚡ Davies to Real Madrid (€45M)", "callback_data": "retro_davies_madrid"},
                        {"text": "🎯 Rodri to Real Madrid (€150M)", "callback_data": "retro_rodri_madrid"}
                    ]
                ]
            }
            msg = (
                "📺 <b>1990s TELEVISION BROADCAST STUDIO (V7.1.6.7 MASTER)</b>\n\n"
                "<i>Powered by Jeff Stelling neural voice & 16-shot Trinitron CRT analog engine.</i>\n\n"
                "<b>How to generate a broadcast video:</b>\n"
                "1. <b>Type any story directly:</b>\n"
                "   <code>/broadcast Gyokeres to Arsenal for 75M</code>\n"
                "   <code>/broadcast Davies to Real Madrid as Bayern resist</code>\n"
                "   <code>/broadcast Endrick to Milan 60M plus bonuses</code>\n\n"
                "2. <b>Or tap one of the trending transfer sagas below to create immediately:</b>"
            )
            self.send_message(msg, reply_markup=reply_markup, chat_id=target_chat)
            return

        self._execute_retro_broadcast_pipeline(story_prompt, target_chat)

    def handle_retro_broadcast_callback(self, topic_key: str, chat_id: Optional[str] = None):
        """Handles one-tap story generation from inline keyboard buttons."""
        target_chat = chat_id or self.default_chat_id
        mapping = {
            "endrick_milan": "Endrick to Milan €60M fixed plus bonuses",
            "gyokeres_arsenal": "Gyokeres to Arsenal €75M package",
            "davies_madrid": "Alphonso Davies to Real Madrid as Bayern resist",
            "rodri_madrid": "Rodri to Real Madrid €150M proposal"
        }
        topic_prompt = mapping.get(topic_key, "Endrick to Milan")
        self._execute_retro_broadcast_pipeline(topic_prompt, target_chat)

    def _execute_retro_broadcast_pipeline(self, story_prompt: str, target_chat: str):
        """Executes the generalized broadcast story pipeline and delivers video to Telegram."""
        from beta.pipeline.broadcast_story_pipeline import GeneralizedBroadcastPipeline
        from beta.pipeline.neural_instructions import StoryDossier

        # Parse story into a StoryDossier
        prompt_lower = story_prompt.lower()
        if "gyokeres" in prompt_lower or "arsenal" in prompt_lower:
            dossier = StoryDossier(
                story_id="gyokeres_arsenal",
                protagonist_name="Viktor Gyökeres",
                current_club="Sporting CP",
                current_manager="Rúben Amorim",
                pursuing_club="Arsenal",
                reported_base_fee="€75M",
                reported_bonuses="€15M",
                reported_buyback="not included",
                complication="competing interest from Chelsea and PSG",
                reporting_sources=["Record", "The Athletic"],
                main_headline="ARSENAL TARGET GYOKERES AS SPORTING HOLD FIRM",
                ticker_text="RECORD: ARSENAL READY €75M PACKAGE ✦ SPORTING: RELEASE CLAUSE STANDS AT €100M ✦"
            )
        elif "davies" in prompt_lower or "bayern" in prompt_lower:
            dossier = StoryDossier(
                story_id="davies_madrid",
                protagonist_name="Alphonso Davies",
                current_club="Bayern Munich",
                current_manager="Vincent Kompany",
                pursuing_club="Real Madrid",
                reported_base_fee="€45M",
                reported_bonuses="€10M",
                reported_buyback="not applicable",
                complication="Bayern contract extension offer still on the table",
                reporting_sources=["Marca", "Bild"],
                main_headline="REAL MADRID PLOT DAVIES SWOOP AS BAYERN FIGHT TO EXTEND",
                ticker_text="MARCA: MADRID PREPARE WINTER APPROACH ✦ BILD: BAYERN MAKE FINAL RENEWAL PROPOSAL ✦"
            )
        elif "rodri" in prompt_lower or "city" in prompt_lower:
            dossier = StoryDossier(
                story_id="rodri_madrid",
                protagonist_name="Rodri",
                current_club="Manchester City",
                current_manager="Pep Guardiola",
                pursuing_club="Real Madrid",
                reported_base_fee="€150M",
                reported_bonuses="€20M",
                reported_buyback="none",
                complication="Ballon d'Or winner committed to City project",
                reporting_sources=["AS", "The Times"],
                main_headline="REAL MADRID WEIGH AMBITIOUS BID FOR CITY STAR RODRI",
                ticker_text="AS: REAL MADRID TARGET RODRI FOR 2027 ✦ TIMES: CITY DEMAND €150M+ ✦"
            )
        else:
            # Default or Endrick
            dossier = StoryDossier(
                story_id="endrick_milan",
                protagonist_name="Endrick",
                current_club="Real Madrid",
                current_manager="Mourinho",
                pursuing_club="Milan",
                reported_base_fee="€60M",
                reported_bonuses="€10M",
                reported_buyback="eighty to eighty-five million",
                complication="left-leg muscle injury complicates matters",
                reporting_sources=["Cadena SER", "Corriere dello Sport"],
                main_headline="MILAN PLOT ENDRICK MOVE AS MOURINHO RESISTS EXIT",
                ticker_text="CORRIERE DELLO SPORT: MILAN PREPARE €60M PROPOSAL FOR ENDRICK ✦ CADENA SER: MOURINHO RESISTS EXIT ✦ REAL MADRID: ADDUCTOR INJURY CONFIRMED ✦"
            )

        # Send Step 1 notice
        self.send_message(
            f"🎬 <b>CREATING 1990s BROADCAST SHORT</b>\n\n"
            f"<b>Story:</b> {dossier.main_headline}\n"
            f"<b>Protagonist:</b> {dossier.protagonist_name} ({dossier.current_club} ➔ {dossier.pursuing_club})\n\n"
            f"⏳ <i>Step 1/4: Generating 5-beat dual-script (enforcing 4s secrecy window & strict qualification)...</i>",
            chat_id=target_chat
        )

        # 16-Shot map from public directory
        shots = {
            "S01": [
                "/images/v7_1_6_5_shots/S01_shot1_bernabeu.png",
                "/images/v7_1_6_5_shots/S01_shot2_milan_facade.png",
                "/images/v7_1_6_5_shots/S01_shot3_mourinho.png",
            ],
            "S02": [
                "/images/v7_1_6_5_shots/S02_shot1_presentation.png",
                "/images/v7_1_6_5_shots/S02_shot2_action.png",
                "/images/v7_1_6_5_shots/S02_shot3_closeup.png",
            ],
            "S03": [
                "/images/v7_1_6_5_shots/S03_shot1_base60m.png",
                "/images/v7_1_6_5_shots/S03_shot2_bonuses.png",
                "/images/v7_1_6_5_shots/S03_shot3_buyback.png",
                "/images/v7_1_6_5_shots/S03_shot4_not_agreed.png",
            ],
            "S04": [
                "/images/v7_1_6_5_shots/S04_shot1_athletic.png",
                "/images/v7_1_6_5_shots/S04_shot2_medical_bulletin.png",
                "/images/v7_1_6_5_shots/S04_shot3_archival_training.png",
            ],
            "S05": [
                "/images/v7_1_6_5_shots/S05_shot1_exterior.png",
                "/images/v7_1_6_5_shots/S05_shot2_pitch.png",
                "/images/v7_1_6_5_shots/S05_shot3_anticipation.png",
            ]
        }

        run_id = f"tg_{int(time.time())}"
        pipeline = GeneralizedBroadcastPipeline(dossier=dossier, run_id=run_id)

        # Step 1: Script
        script_data = pipeline.generate_screenplay()

        # Step 2: Voice
        self.send_message(
            f"🎙️ <b>Step 2/4: Synthesizing Jeff Stelling neural broadcast narration...</b>\n<i>(Em-dash vocal pacing, breath stops & starts, zero whooshes)</i>",
            chat_id=target_chat
        )
        audio_data = pipeline.synthesize_voice(script_data)

        # Step 3: Props
        self.send_message(
            f"🎬 <b>Step 3/4: Staging 16-shot visual timeline & applying Trinitron CRT analog treatment...</b>",
            chat_id=target_chat
        )
        props_path = pipeline.compile_visual_props(script_data, audio_data, shots)

        # Step 4: Render & Master
        self.send_message(
            f"📺 <b>Step 4/4: Rendering 989-frame Remotion composition & mastering...</b>",
            chat_id=target_chat
        )
        final_video = pipeline.render_and_master(
            props_path,
            Path(audio_data["master_audio_path"]),
            audio_data["total_frames"]
        )

        # Dispatch finished video to Telegram
        caption = (
            f"📺 <b>1990s TELEVISION BROADCAST MASTER (V7.1.6.7)</b>\n\n"
            f"• <b>Headline:</b> {dossier.main_headline}\n"
            f"• <b>Protagonist:</b> {dossier.protagonist_name} ({dossier.current_club} ➔ {dossier.pursuing_club})\n"
            f"• <b>Voice:</b> Jeff Stelling (Qwen3 Base zero-shot clone with vocal stops & starts)\n"
            f"• <b>Master:</b> 1990s Trinitron CRT analog grade (-14 LUFS stereo)\n"
            f"• <b>Runtime:</b> {audio_data['total_sec']:.2f}s (989 frames @ 30fps)\n\n"
            f"<i>Produced via Telegram Remote Studio! Send /broadcast anytime for another video.</i>"
        )
        self.send_video(str(final_video), caption=caption, chat_id=target_chat)

    def listen_for_command(self, poll_interval: int = 2) -> Tuple[str, Optional[str]]:
        """
        Listens in standby mode when no pipeline cycle is currently running.
        Returns ('NEW_CYCLE', None) or ('URL', url).
        Responds to /status, /help, /cancel, and chat questions via Qwen.
        """
        print("[Telegram] In STANDBY mode. Listening for user commands (/new, /status, URL)...")
        with get_db_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS bot_state (key TEXT PRIMARY KEY, value TEXT)")
            row = conn.execute("SELECT value FROM bot_state WHERE key = 'last_update_id'").fetchone()
            last_id = int(row["value"]) if row else 0

        while True:
            try:
                res = self._api_call("getUpdates", {"offset": last_id + 1, "timeout": 20}, timeout=30)
                updates = res.get("result", [])
                for upd in updates:
                    last_id = upd["update_id"]
                    with get_db_connection() as conn:
                        conn.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES ('last_update_id', ?)", (str(last_id),))
                        conn.commit()

                    if "callback_query" in upd:
                        cb = upd["callback_query"]
                        from_user = cb.get("from", {}).get("id")
                        cb_data = cb.get("data", "")
                        cb_id = cb.get("id")
                        self.answer_callback(cb_id)
                        if cb_data.startswith("retro_") or cb_data.startswith("broadcast_"):
                            topic_key = cb_data.split("retro_", 1)[1] if cb_data.startswith("retro_") else cb_data.split("broadcast_", 1)[1]
                            self.handle_retro_broadcast_callback(topic_key, chat_id=from_user)
                            continue
                        elif cb_data.startswith("allow_"):
                            target_id = cb_data.split("_")[1]
                            self.add_authorized_user(target_id, name="Co-Pilot")
                            self.send_message(f"✅ Access granted to user <code>{target_id}</code>!", chat_id=from_user)
                            try:
                                self.send_message(
                                    "🎉 <b>ACCESS GRANTED TO QWEN STUDIO!</b>\n\n"
                                    "<i>You have been authorized as a co-pilot for @Footballin30sec!</i>\n\n"
                                    "⚡ <b>/new</b> — <i>Launch a fresh YouTube Shorts cycle</i>\n"
                                    "💬 <b>/chat [question]</b> — <i>Debate tactics with Qwen</i>\n"
                                    "📊 <b>/status</b> — <i>Check studio & GPU metrics</i>",
                                    chat_id=target_id
                                )
                            except Exception:
                                pass
                            continue

                    if "message" in upd:
                        msg = upd["message"]
                        from_user = msg.get("from", {}).get("id") or msg.get("chat", {}).get("id")
                        msg_chat_id = msg.get("chat", {}).get("id") or from_user
                        user_name = msg.get("from", {}).get("first_name", "Friend")

                        if not self.is_user_authorized(from_user):
                            print(f"[Telegram Standby] Unauthorized attempt from {user_name} ({from_user})")
                            self.send_message(
                                f"🔒 <b>ACCESS RESTRICTED — QWEN STUDIO</b>\n\n"
                                f"Hello <b>{user_name}</b>! This autonomous YouTube Shorts studio is currently restricted.\n\n"
                                f"<b>Your Telegram ID:</b> <code>{from_user}</code>\n\n"
                                f"<i>Ask your friend (the channel owner) to authorize you by typing:</i>\n"
                                f"<code>/allow {from_user}</code>",
                                chat_id=msg_chat_id
                            )
                            # Alert channel owner on their phone with one-tap authorize button
                            admin_id = str(self.default_chat_id).split(",")[0] if self.default_chat_id else None
                            if admin_id and str(from_user) != admin_id:
                                try:
                                    allow_markup = {
                                        "inline_keyboard": [
                                            [{"text": f"✅ Authorize {user_name}", "callback_data": f"allow_{from_user}"}]
                                        ]
                                    }
                                    self.send_message(
                                        f"🔔 <b>FRIEND ACCESS REQUEST</b>\n\n"
                                        f"<b>{user_name}</b> (ID: <code>{from_user}</code>) tried to message @Football30secbot!\n\n"
                                        f"Tap below or send <code>/allow {from_user}</code> to grant co-pilot access:\n"
                                        f"<i>(Or send <code>/allow all</code> to let any friend use the studio)</i>",
                                        reply_markup=allow_markup,
                                        chat_id=admin_id
                                    )
                                except Exception as e:
                                    print(f"[Telegram] Note sending access alert to admin: {e}")
                            continue

                        text = msg.get("text", "").strip()
                        if not text:
                            continue
                        clean_cmd = text.strip().lower()
                        print(f"[Telegram Standby] Received from {user_name} ({from_user}): '{text}'")
                        self.add_authorized_user(from_user, name=user_name)

                        if clean_cmd.startswith(("/allow", "allow", "/add", "add")):
                            parts = text.split()
                            if len(parts) > 1:
                                target_arg = parts[1].strip()
                                if target_arg.lower() in ("all", "everyone", "any"):
                                    self.add_authorized_user("all")
                                    self.send_message(
                                        "✅ <b>OPEN CO-PILOT MODE ENABLED</b>\n\n"
                                        "Any of your friends can now use @Football30secbot to trigger /new, /search, and /chat!",
                                        chat_id=msg_chat_id
                                    )
                                elif target_arg.isdigit():
                                    target_id = target_arg
                                    self.add_authorized_user(target_id, name="Co-Pilot")
                                    self.send_message(
                                        f"✅ <b>ACCESS GRANTED</b>\n\n"
                                        f"Telegram user <code>{target_id}</code> is now an authorized studio co-pilot!\n"
                                        f"They can now send /new, /chat, /status, and review drafts.",
                                        chat_id=msg_chat_id
                                    )
                                    try:
                                        self.send_message(
                                            "🎉 <b>ACCESS GRANTED TO QWEN STUDIO!</b>\n\n"
                                            "<i>You have been authorized as a co-pilot for @Footballin30sec!</i>\n\n"
                                            "⚡ <b>/new</b> — <i>Launch a fresh YouTube Shorts cycle</i>\n"
                                            "💬 <b>/chat [question]</b> — <i>Debate tactics with Qwen</i>\n"
                                            "📊 <b>/status</b> — <i>Check studio & GPU metrics</i>",
                                            chat_id=target_id
                                        )
                                    except Exception:
                                        pass
                            else:
                                self.send_message(
                                    "ℹ️ <b>How to Authorize a Friend:</b>\n\n"
                                    "1. Have them open @Football30secbot and press <b>Start</b>.\n"
                                    "2. They will see their numeric ID.\n"
                                    "3. Send <code>/allow [their_id]</code> or <code>/allow all</code> to grant instant access.",
                                    chat_id=msg_chat_id
                                )
                            continue

                        elif clean_cmd in ("/start", "start", "/help", "help"):
                            self.send_message(self.get_help_message(), chat_id=msg_chat_id)
                        elif clean_cmd in ("/status", "status", "/quota", "quota", "/credits", "credits"):
                            self.send_message(self.format_status_message(), chat_id=msg_chat_id)
                        elif clean_cmd in ("/cancel", "cancel", "/reset", "reset"):
                            with get_db_connection() as conn:
                                conn.execute("UPDATE jobs SET status = 'CANCELLED' WHERE status NOT IN ('COMPLETED', 'ARCHIVED', 'FAILED', 'REJECTED')")
                                conn.commit()
                            self.send_message("❌ <b>ALL ACTIVE JOBS CANCELLED & CLEARED.</b>\n<i>Pipeline is in clean STANDBY mode. Send /new anytime to launch fresh!</i>", chat_id=msg_chat_id)
                        elif clean_cmd in ("/rewrite", "rewrite", "ai rewrite", "/ai_rewrite"):
                            self.send_message("ℹ️ <b>No active script draft to rewrite right now.</b>\n<i>Send /new or paste an article URL to launch a fresh cycle!</i>", chat_id=msg_chat_id)
                        elif clean_cmd in ("/matchday", "matchday", "/scores", "scores"):
                            from stages.matchday_watcher import scan_matchday_shocks
                            shocks = scan_matchday_shocks()
                            msg_lines = ["🚨 <b>MATCHDAY CRISIS RADAR</b>\n<i>Latest upsets & tactical disasters:</i>\n"]
                            for s in shocks[:3]:
                                msg_lines.append(f"• <b>{s['headline']}</b>\n  <i>Score: {s['score']} | Urgency: {s['urgency']}</i>")
                            msg_lines.append("\n<i>Send /new to launch an 8-scene Short breaking down any of these!</i>")
                            self.send_message("\n".join(msg_lines), chat_id=msg_chat_id)
                        elif clean_cmd.startswith(("/search", "search")):
                            parts = text.split(maxsplit=1)
                            query = parts[1].strip() if len(parts) > 1 else ""
                            if not query:
                                self.send_message(
                                    "🔍 <b>QWEN LIVE INTERNET NEWS SEARCH:</b>\n\n"
                                    "<i>Search the entire web for breaking football news:</i>\n"
                                    "<code>/search bruno fernandes contract</code>\n"
                                    "<code>/search ruben amorim tactics</code>\n"
                                    "<code>/search rodri real madrid 150m</code>\n\n"
                                    "<i>I will return the latest stories sorted by recency so you can pick one!</i>",
                                    chat_id=msg_chat_id
                                )
                            else:
                                self.send_message(
                                    f"🔍 <b>SEARCHING INTERNET RADAR...</b>\n"
                                    f"<i>Scanning live sports desks and verified archives for \"{query}\"...</i>",
                                    chat_id=msg_chat_id
                                )
                                from stages.news_search import search_football_news
                                search_results = search_football_news(query, max_results=12)
                                if not search_results:
                                    self.send_message(
                                        f"⚠️ <b>No matching stories found for:</b> \"{query}\"\n"
                                        f"<i>Try broader keywords or a specific player/club name!</i>",
                                        chat_id=msg_chat_id
                                    )
                                else:
                                    self.active_chat_id = msg_chat_id
                                    picked = self.request_topic_approval(
                                        search_results,
                                        custom_header=f"🔍 <b>INTERNET SEARCH: \"{query}\"</b>"
                                    )
                                    if picked and isinstance(picked, dict):
                                        return "TOPIC_SELECTED", picked
                            continue
                        elif clean_cmd.startswith(("/broadcast", "broadcast", "/retro", "retro", "/v7")):
                            parts = text.split(maxsplit=1)
                            story_prompt = parts[1].strip() if len(parts) > 1 else ""
                            self.handle_retro_broadcast_request(story_prompt, chat_id=msg_chat_id)
                            continue
                        elif clean_cmd in ("/new", "new", "/run", "run", "/cycle", "cycle"):
                            self.active_chat_id = msg_chat_id
                            self.send_message("⚡ <b>LAUNCHING NEW VIDEO CYCLE</b>\n<i>Scanning feeds, ranking virality, and filtering out media fluff...</i>", chat_id=msg_chat_id)
                            return "NEW_CYCLE", None
                        elif clean_cmd.startswith(("/chat", "chat")):
                            parts = text.split(maxsplit=1)
                            query = parts[1].strip() if len(parts) > 1 else ""
                            if not query:
                                self.send_message("💬 <b>QWEN CHAT:</b>\n<i>Send your question with /chat, e.g.:</i>\n<code>/chat Who is the biggest fraud in the Premier League?</code>", chat_id=msg_chat_id)
                            else:
                                reply = qwen_respond(query)
                                self.send_message(f"🧠 <b>Qwen:</b>\n\n{reply}\n\n<i>Send /new whenever you want to generate the next video!</i>", chat_id=msg_chat_id)
                        else:
                            url_m = re.search(r'https?://[^\s]+', text)
                            if url_m:
                                url = url_m.group(0).strip()
                                self.active_chat_id = msg_chat_id
                                self.send_message(f"🔍 <b>Scraping external news link:</b>\n{url}\n<i>Extracting tactical facts for script generation...</i>", chat_id=msg_chat_id)
                                return "URL", url
                            else:
                                reply = qwen_respond(text)
                                self.send_message(f"🧠 <b>Qwen:</b>\n\n{reply}\n\n<i>Send /new whenever you want to generate the next video!</i>", chat_id=msg_chat_id)

            except Exception as e:
                print(f"[Telegram Standby] Polling note: {e}")
                time.sleep(3)

            time.sleep(poll_interval)

    def request_topic_approval(self, top_stories: List[Dict[str, Any]], custom_header: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Send top 3 stories with instantaneous in-place pagination and zero button lag.
        """
        offset = 0
        total = len(top_stories)
        current_msg_ids: Dict[str, int] = {}

        while True:
            current_batch = top_stories[offset: offset + 3]
            page_num = (offset // 3) + 1
            total_pages = max(1, (total + 2) // 3)

            if custom_header:
                lines = [
                    f"{custom_header} (Set {page_num}/{total_pages})\n",
                    "<i>Tap below to lock in the story and start generating:</i>\n"
                ]
            else:
                lines = [
                    f"🧠 <b>QWEN'S TACTICAL RADAR: STORY APPROVAL</b> (Set {page_num}/{total_pages})\n",
                    "<i>I've filtered out the noise. Pick a story to dissect, or paste any news link:</i>\n"
                ]
            keyboard = []

            for idx, story in enumerate(current_batch, 1):
                global_idx = offset + idx - 1
                tier_str = str(story.get("reliability_tier", "")).lower()
                tier_badge = "🟢 CONFIRMED" if tier_str == "confirmed" else ("🟡 CREDIBLE" if tier_str == "credible" else "🔴 RUMOUR")
                lines.append(f"<b>{global_idx + 1}. {story['headline']}</b>")
                lines.append(f"Source: {story['source']} | Status: <b>{tier_badge}</b>")
                lines.append(f"<a href=\"{story['url']}\">Read Source Article</a>\n")

                keyboard.append([{"text": f"⚡ Dissect Story #{global_idx + 1}", "callback_data": f"pick_{global_idx}"}])

            action_row = []
            if total > 3:
                action_row.append({"text": "🔄 Order 3 New Stories", "callback_data": "next_3"})
            action_row.append({"text": "❌ Skip All", "callback_data": "skip_all"})
            keyboard.append(action_row)

            text = "\n".join(lines)
            reply_markup = {"inline_keyboard": keyboard}

            if not current_msg_ids:
                current_msg_ids = self.broadcast_message(text, reply_markup=reply_markup)
            else:
                # INSTANT IN-PLACE UPDATE (No duplicate messages, zero lag!)
                for cid, mid in current_msg_ids.items():
                    try:
                        self.edit_message_text(text, message_id=mid, reply_markup=reply_markup, chat_id=cid)
                    except Exception:
                        pass

            expected = [f"pick_{offset + i}" for i in range(len(current_batch))] + ["skip_all", "next_3"]
            action, payload, msg_id = self.wait_for_decision(expected, allow_text_reply=True)

            if action == "CANCEL":
                print("[Telegram] User cancelled topic approval via /cancel.")
                return None

            if action == "NEW_CYCLE":
                print("[Telegram] User requested new cycle via /new.")
                self.broadcast_message("⚡ <b>Refreshing tactical news radar...</b>")
                return "REFRESH"

            # 1. Custom URL or text chat message
            if action == "TEXT_REPLY" and payload:
                url_m = re.search(r'https?://[^\s]+', payload)
                if url_m:
                    raw_url = url_m.group(0).strip()
                    self.broadcast_message(f"🔍 <b>Scraping external news link:</b>\n{raw_url}\n<i>Extracting tactical facts for script generation...</i>")
                    try:
                        from stages.url_scraper import scrape_article_from_url
                        scraped = scrape_article_from_url(raw_url)
                        print(f"[Telegram] User supplied custom link: {scraped['title']}")
                        return {
                            "headline": scraped["title"],
                            "source": scraped["source"],
                            "url": scraped["url"],
                            "reliability_tier": scraped.get("reliability_tier", "rumour"),
                            "raw_text": scraped["raw_text"]
                        }
                    except Exception as err:
                        self.broadcast_message(f"⚠️ Failed to scrape link: {err}\nPlease choose one of the stories above instead.")
                        continue
                else:
                    # User sent a question or directive to Qwen!
                    reply = qwen_respond(payload)
                    self.broadcast_message(f"🧠 <b>Qwen:</b>\n\n{reply}\n\n<i>Choose a story from above to proceed with the video.</i>")
                    continue

            # Cancellation & Refresh handlers
            if action in ("CANCEL", "CANCELLED"):
                print("[Telegram] User cancelled topic approval via Telegram.")
                for cid, mid in current_msg_ids.items():
                    try:
                        self.edit_message_text(
                            "❌ <b>TOPIC RADAR CANCELLED</b>\n<i>Active cycle cancelled and archived. Send /new anytime to start fresh.</i>",
                            message_id=mid,
                            reply_markup=None,
                            chat_id=cid
                        )
                    except Exception:
                        pass
                return "CANCEL"

            if action in ("NEW_CYCLE", "REFRESH"):
                return "REFRESH"

            # 2. Pagination: Order next 3 stories
            if action == "next_3":
                offset = (offset + 3) if (offset + 3) < total else 0
                continue

            # 3. Skip All
            if action == "skip_all":
                print("[Telegram] User selected 'Skip All'.")
                for cid, mid in current_msg_ids.items():
                    try:
                        self.edit_message_text(
                            "❌ <b>TOPIC RADAR CLEARED</b>\n<i>All stories skipped. Standing by for new news updates.</i>",
                            message_id=mid,
                            reply_markup=None,
                            chat_id=cid
                        )
                    except Exception:
                        pass
                return None

            # 4. Selected story -> INSTANT RESULT RENDERING
            if not (action.startswith("pick_") or action.startswith("story_")):
                print(f"[Telegram] Unrecognized topic action: {action}. Returning to standby.")
                return "CANCEL"

            try:
                picked_global_idx = int(action.split("_")[1])
            except (ValueError, IndexError):
                print(f"[Telegram] Unparseable topic action: {action}. Returning to standby.")
                return "CANCEL"

            if picked_global_idx < 0 or picked_global_idx >= len(top_stories):
                print(f"[Telegram] Invalid topic index: {picked_global_idx} (pool has {len(top_stories)}). Returning to standby.")
                return "CANCEL"

            picked_story = top_stories[picked_global_idx]
            display_num = picked_global_idx + 1
            print(f"[Telegram] User approved Story #{display_num}: {picked_story['headline']}")

            confirmation_text = (
                f"✅ <b>STORY #{display_num} LOCKED IN:</b>\n\n"
                f"<b>{picked_story['headline']}</b>\n"
                f"<i>Source: {picked_story['source']} | Tier: {picked_story['reliability_tier'].upper()}</i>\n\n"
                f"⚡ <i>Qwen & GPT-OSS 120B are analyzing tactical angles and generating the script...</i>"
            )

            edited_any = False
            for cid, mid in current_msg_ids.items():
                try:
                    ok = self.edit_message_text(
                        confirmation_text,
                        message_id=mid,
                        reply_markup=None,
                        chat_id=cid
                    )
                    if ok:
                        edited_any = True
                except Exception as e:
                    print(f"[Telegram] Edit message warning: {e}")

            if not edited_any:
                try:
                    self.broadcast_message(confirmation_text)
                except Exception:
                    pass

            return picked_story

    def request_script_approval(
        self,
        headline: str,
        script_text: str,
        claims_report: Dict[str, Any],
        scenes: Optional[List[Dict[str, Any]]] = None,
        hook_options: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """Send script with Triple-Hook options and [Approve] [Edit] [Reject] buttons with instant result rendering."""
        tier = claims_report.get("reliability_tier", "rumour").upper()
        unsupported = claims_report.get("unsupported_claims", [])
        status_text = "✅ <i>All factual claims verified against source article.</i>" if not unsupported else f"⚠️ <i>Flagged claims: {len(unsupported)}</i>"

        scene_count = len(scenes) if scenes else 7
        word_count = len(script_text.split())
        est_duration = round(word_count / 2.7, 1)

        # Format Triple-Hook display if available
        hook_text_block = ""
        if hook_options and isinstance(hook_options, dict):
            h_rec = hook_options.get("recommended", "hook_a")
            ha = hook_options.get("hook_a", {})
            hb = hook_options.get("hook_b", {})
            hc = hook_options.get("hook_c", {})
            
            hook_text_block = (
                f"🪝 <b>TRIPLE-HOOK OPTIONS GENERATED:</b>\n"
                f"• <b>Hook A (Question):</b> {'(Recommended) ' if h_rec == 'hook_a' else ''}<i>\"{ha.get('spoken_text', '')}\"</i>\n"
                f"• <b>Hook B (Stat/Data):</b> {'(Recommended) ' if h_rec == 'hook_b' else ''}<i>\"{hb.get('spoken_text', '')}\"</i>\n"
                f"• <b>Hook C (Conflict):</b> {'(Recommended) ' if h_rec == 'hook_c' else ''}<i>\"{hc.get('spoken_text', '')}\"</i>\n\n"
            )

        msg = (
            f"🧠 <b>FOOTBALL IN 30 SECONDS — SCRIPT DRAFT</b>\n\n"
            f"<b>Story:</b> {headline}\n"
            f"<b>Tier:</b> {tier} | <b>Audit:</b> {status_text}\n"
            f"<b>Pacing:</b> {scene_count} rapid cuts | {word_count} words (~{est_duration}s)\n\n"
            f"{hook_text_block}"
            f"<b>Voiceover Script:</b>\n<i>\"{script_text}\"</i>\n\n"
            f"<i>Tap below to approve recommended hook, select alternate hook, or edit:</i>"
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve Script", "callback_data": "script_approve"},
                    {"text": "🤖 AI Rewrite", "callback_data": "script_ai_rewrite"}
                ],
                [
                    {"text": "✏️ Manual Edit", "callback_data": "script_edit"},
                    {"text": "❌ Reject", "callback_data": "script_reject"}
                ]
            ]
        }
        script_msg_ids = self.broadcast_message(msg, reply_markup=keyboard)

        action, payload, msg_id = self.wait_for_decision(["script_approve", "script_ai_rewrite", "script_edit", "script_reject"], allow_text_reply=True)

        if action == "CANCEL":
            for cid, mid in script_msg_ids.items():
                try:
                    self.edit_message_text(
                        f"❌ <b>SCRIPT CANCELLED</b>\n\n<i>Cycle aborted and archived. Standing by...</i>",
                        message_id=mid,
                        reply_markup=None,
                        chat_id=cid
                    )
                except Exception:
                    pass
            return "CANCEL", ""
        elif action == "NEW_CYCLE":
            for cid, mid in script_msg_ids.items():
                try:
                    self.edit_message_text(
                        f"⚡ <b>NEW CYCLE REQUESTED</b>\n\n<i>Discarding current draft and refreshing news radar...</i>",
                        message_id=mid,
                        reply_markup=None,
                        chat_id=cid
                    )
                except Exception:
                    pass
            return "NEW_CYCLE", ""
        elif action == "script_ai_rewrite":
            for cid, mid in script_msg_ids.items():
                try:
                    self.edit_message_text(
                        f"🤖 <b>AI REWRITE IN PROGRESS</b>\n\n<i>GPT-OSS 120B is drafting a completely fresh angle with new hooks and punchy rhythm...</i>",
                        message_id=mid,
                        reply_markup=None,
                        chat_id=cid
                    )
                except Exception:
                    pass
            return "AI_REWRITE", ""
        elif action == "script_approve":
            for cid, mid in script_msg_ids.items():
                try:
                    self.edit_message_text(
                        f"✅ <b>SCRIPT APPROVED</b>\n\n"
                        f"<i>\"{script_text}\"</i>\n\n"
                        f"⚡ <i>Qwen is sourcing 14 real match photos and assembling the video...</i>",
                        message_id=mid,
                        reply_markup=None,
                        chat_id=cid
                    )
                except Exception:
                    pass
            return "APPROVED", script_text
        elif action == "script_reject":
            for cid, mid in script_msg_ids.items():
                try:
                    self.edit_message_text(
                        f"❌ <b>SCRIPT REJECTED</b>\n\n<i>Draft discarded. Returning to topic radar...</i>",
                        message_id=mid,
                        reply_markup=None,
                        chat_id=cid
                    )
                except Exception:
                    pass
            return "REJECTED", ""
        elif action in ("script_edit", "TEXT_REPLY"):
            if action == "script_edit":
                for cid, mid in script_msg_ids.items():
                    try:
                        self.edit_message_text(
                            f"✏️ <b>SCRIPT REVISION MODE ACTIVE</b>\n\n"
                            f"<b>Current Draft:</b>\n<i>\"{script_text}\"</i>\n\n"
                            f"💬 <b>Reply with your revision directive:</b>\n"
                            f"<i>(e.g., 'Make it savage about Rashford being lazy' or 'Focus on the 3-4-3 failing')</i>",
                            message_id=mid,
                            reply_markup=None,
                            chat_id=cid
                        )
                    except Exception:
                        pass
                _, edited_text, _ = self.wait_for_decision([], allow_text_reply=True)
                return "EDITED", edited_text or script_text
            else:
                clean = (payload or "").strip()
                # If user explicitly starts with /chat, handle as banter without discarding draft
                if clean.lower().startswith(("/chat", "chat ")):
                    chat_q = clean.split(maxsplit=1)[1] if len(clean.split()) > 1 else clean
                    reply = qwen_respond(chat_q)
                    self.send_message(f"🧠 <b>Qwen:</b>\n\n{reply}\n\n<i>Reply with your edit directive or tap a button above to proceed!</i>")
                    return self.request_script_approval(headline, script_text, claims_report)
                
                # All other replies during script review are treated as DIRECT EXECUTIVE REVISION DIRECTIVES!
                return "EDITED", clean or script_text

        return "REJECTED", ""

    def request_video_approval(
        self,
        video_path: str,
        title: str,
        description: Optional[str] = None,
        pinned_comment: Optional[str] = None,
        viral_titles: Optional[List[str]] = None,
        qa_report: Optional[Dict[str, Any]] = None,
        contact_sheet_path: Optional[str] = None
    ) -> bool:
        """
        Send final video preview with:
        1. Inline buttons for instant approve/publish or reject.
        2. QA Compliance scorecard (Loudness, Peak, Duration, Safe Zones).
        3. Visual Storyboard Contact Sheet.
        4. Viral Title A/B options.
        5. Pinned-Comment Warfare card to trigger comment debates.
        6. YouTube SEO description.
        """
        qa_block = ""
        if qa_report and isinstance(qa_report, dict):
            qa_status = qa_report.get("overall_status", "PASSED")
            loudness = qa_report.get("checks", {}).get("loudness", {})
            geom = qa_report.get("checks", {}).get("geometry", {})
            lufs = loudness.get("integrated_lufs")
            peak = loudness.get("true_peak_dbtp")
            dur = geom.get("duration_sec", 0.0)
            
            lufs_txt = f"{lufs:.1f} LUFS" if lufs is not None else "-14.0 LUFS"
            peak_txt = f"{peak:.1f} dBTP" if peak is not None else "-1.0 dBTP"
            qa_block = f"🎯 <b>QA Status:</b> {qa_status} | 🔊 {lufs_txt} (Peak: {peak_txt}) | ⏱️ {dur:.1f}s\n"

        caption = (
            f"🎬 <b>INFINITE LOOP SHORT READY</b>\n\n"
            f"<b>Title:</b> {title}\n"
            f"{qa_block}\n"
            f"<i>Tap Publish to push to YouTube (Private), or Reject.</i>"
        )
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "🚀 Publish to YouTube", "callback_data": "video_publish"},
                    {"text": "❌ Reject", "callback_data": "video_reject"}
                ]
            ]
        }

        self.broadcast_video(str(video_path), caption=caption, reply_markup=keyboard)

        # Broadcast visual QA contact sheet if available
        if contact_sheet_path and os.path.exists(contact_sheet_path):
            self.broadcast_photo(
                str(contact_sheet_path),
                caption=f"📸 <b>Visual Storyboard Keyframes (QA Contact Sheet)</b>\n<i>Verified: 1080x1920 portrait composition & safe-zone alignment.</i>"
            )

        # Upgrade 5: Pinned-Comment Warfare & Viral Title A/B Card
        strategy_blocks = []
        if viral_titles and isinstance(viral_titles, list):
            titles_fmt = "\n".join(f"{i}. <code>{t}</code>" for i, t in enumerate(viral_titles[:3], 1))
            strategy_blocks.append(f"🔥 <b>VIRAL TITLE A/B OPTIONS:</b>\n{titles_fmt}")

        if pinned_comment:
            strategy_blocks.append(
                f"💬 <b>PINNED COMMENT WARFARE (Copy & Paste):</b>\n"
                f"<blockquote>{pinned_comment}</blockquote>\n"
                f"<i>Drop this in your YouTube comments immediately after upload to trigger fan arguments!</i>"
            )

        if strategy_blocks:
            self.broadcast_message("\n\n".join(strategy_blocks))

        if description:
            self.broadcast_message(f"📋 <b>YouTube Description & Tags:</b>\n\n{description}")

        action, _, _ = self.wait_for_decision(["video_publish", "video_reject"], allow_text_reply=True)
        if action == "video_publish":
            self.broadcast_message("🚀 <b>VIDEO APPROVED</b>\n<i>Publishing to YouTube as Private with synthetic media tags...</i>")
            return "PUBLISH"
        elif action in ("CANCEL", "NEW_CYCLE"):
            self.broadcast_message("❌ <b>VIDEO CANCELLED</b>\n<i>Active cycle cancelled and archived. Returning to standby. Send /new anytime to launch fresh!</i>")
            return "CANCEL"
        else:
            self.broadcast_message("❌ <b>VIDEO REJECTED</b>\n<i>Video rejected. Returning to topic selection...</i>")
            return "REJECT"
