"""
Configuration Loader for FS 30 Pipeline.
Reads config.yaml and environment settings.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    if config_path is None:
        cfg_main = PROJECT_ROOT / "config" / "config.yaml"
        config_path = cfg_main if cfg_main.exists() else (PROJECT_ROOT / "config.yaml")
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
        
    # Overlay environment variables if present
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        cfg.setdefault("llm", {})["api_key"] = groq_key
        
    tel_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if tel_token:
        cfg.setdefault("telegram", {})["bot_token"] = tel_token
        
    tel_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if tel_chat:
        cfg.setdefault("telegram", {})["chat_id"] = tel_chat
        
    return cfg

def get_run_dir(run_id: str) -> Path:
    run_dir = PROJECT_ROOT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "assets").mkdir(exist_ok=True)
    (run_dir / "audio").mkdir(exist_ok=True)
    (run_dir / "render").mkdir(exist_ok=True)
    return run_dir
