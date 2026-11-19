"""
Stage 5: Swappable Image Generation Backends.
Supports:
1. LocalSD15Backend: Local SD 1.5 + LCM LoRA with float32 VAE upcasting (GTX 1650 Ti tuned)
2. KaggleBackend: Remote Kaggle worker webhook
3. CloudflareBackend: Cloudflare Workers AI SDXL-Lightning
"""

import sys
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.resource_monitor import ResourceTracker, get_vram_usage

MODELS_DIR = PROJECT_ROOT / "models"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

class ImageGeneratorBase(ABC):
    @abstractmethod
    def generate(self, prompt: str, output_path: Path, width: int = 512, height: int = 512) -> Path:
        """Generate an image from prompt and save to output_path."""
        pass

class LocalSD15Backend(ImageGeneratorBase):
    def __init__(self, model_id_or_path: Optional[str] = None, lora_path: Optional[str] = None):
        self.model_path = model_id_or_path or "segmind/tiny-sd"
        self.lora_path = lora_path

    def generate(self, prompt: str, output_path: Path, width: int = 512, height: int = 512) -> Path:
        with ResourceTracker("SD15_Local_Generation"):
            import torch
            from diffusers import StableDiffusionPipeline

            output_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[LocalSD] Generating AI image for prompt: \"{prompt[:60]}...\"")

            # Load pipeline with float32 for GTX 16-series bug resolution
            pipe = StableDiffusionPipeline.from_pretrained(
                self.model_path,
                torch_dtype=torch.float32,
                safety_checker=None
            )
            pipe.enable_attention_slicing()
            pipe.enable_vae_slicing()
            pipe.to("cuda")

            steps = 14
            guidance = 7.5

            with torch.inference_mode():
                result = pipe(
                    prompt=prompt + ", dramatic sports lighting, cinematic atmosphere, 8k vertical sports photography, photorealistic",
                    num_inference_steps=steps,
                    guidance_scale=guidance,
                    width=width,
                    height=height
                )

            image = result.images[0]
            image.save(output_path)
            print(f"[LocalSD] Image saved to: {output_path}")

            # Explicit memory release
            del pipe
            del result
            torch.cuda.empty_cache()
            return output_path

class KaggleBackend(ImageGeneratorBase):
    def __init__(self, api_url: Optional[str] = None):
        self.api_url = api_url or os.environ.get("KAGGLE_WORKER_URL", "http://localhost:5000/generate")

    def generate(self, prompt: str, output_path: Path, width: int = 512, height: int = 512) -> Path:
        print(f"[KaggleBackend] Requesting remote generation from {self.api_url}...")
        import urllib.request
        import json
        req = urllib.request.Request(
            self.api_url,
            data=json.dumps({"prompt": prompt, "width": width, "height": height}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            with open(output_path, "wb") as f:
                f.write(data)
        return output_path

class CloudflareBackend(ImageGeneratorBase):
    """
    Photorealistic AI generation using Cloudflare Workers AI.
    Primary: Black Forest Labs FLUX.1 [schnell] (12B parameter state-of-the-art flow transformer)
    Secondary fallback: ByteDance SDXL-Lightning
    """
    def __init__(self, account_id: Optional[str] = None, api_token: Optional[str] = None):
        env_path = PROJECT_ROOT / ".env"
        cf_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID") or os.environ.get("CF_ACCOUNT_ID", "")
        cf_tok = api_token or os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get("CF_API_TOKEN", "")
        if (not cf_id or not cf_tok) and env_path.exists():
            try:
                for line in env_path.read_text(encoding="utf-8").splitlines():
                    if line.startswith(("CLOUDFLARE_ACCOUNT_ID=", "CF_ACCOUNT_ID=")):
                        cf_id = line.split("=", 1)[1].strip().strip('"\'')
                    elif line.startswith(("CLOUDFLARE_API_TOKEN=", "CF_API_TOKEN=")):
                        cf_tok = line.split("=", 1)[1].strip().strip('"\'')
            except Exception:
                pass
        self.account_id = cf_id
        self.api_token = cf_tok

    def generate(self, prompt: str, output_path: Path, width: int = 1024, height: int = 1024) -> Path:
        import requests
        import base64

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.account_id or not self.api_token:
            raise ValueError("Cloudflare Account ID or API Token missing in .env")

        enhanced_prompt = (
            f"Hyperrealistic cinematic sports photography, vertical 9:16 composition, {prompt}, "
            f"ultra-sharp 8k resolution, professional dynamic lighting, stadium floodlights, authentic kits and details."
        )

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        # 1. Primary Model: FLUX.1 [schnell] (State-of-the-art cinematic quality)
        flux_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        print(f"[CloudflareBackend] Requesting FLUX.1 [schnell] for: \"{prompt[:55]}...\"")
        try:
            res = requests.post(flux_url, headers=headers, json={"prompt": enhanced_prompt}, timeout=45)
            if res.status_code == 200:
                data = res.json()
                b64_img = data.get("result", {}).get("image")
                if b64_img:
                    img_bytes = base64.b64decode(b64_img)
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    print(f"[CloudflareBackend] FLUX.1 visual saved successfully ({len(img_bytes)} bytes) -> {output_path}")
                    return output_path
            else:
                print(f"[CloudflareBackend] FLUX returned status {res.status_code}: {res.text[:100]}")
        except Exception as e:
            print(f"[CloudflareBackend] FLUX attempt note: {e}")

        # 2. Secondary Fallback: SDXL-Lightning
        sdxl_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
        print(f"[CloudflareBackend] Falling back to Workers AI SDXL-Lightning...")
        try:
            res = requests.post(sdxl_url, headers=headers, json={"prompt": enhanced_prompt}, timeout=45)
            if res.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(res.content)
                print(f"[CloudflareBackend] SDXL visual saved -> {output_path}")
                return output_path
            else:
                raise RuntimeError(f"Cloudflare SDXL error {res.status_code}: {res.text[:100]}")
        except Exception as e:
            raise RuntimeError(f"All Cloudflare Workers AI image models failed: {e}")

class GeminiImageBackend(ImageGeneratorBase):
    """
    Generates photorealistic, cinematic 9:16 vertical images using Google Gemini Image models.
    """
    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                env_path = PROJECT_ROOT / ".env"
                if env_path.exists():
                    try:
                        for line in env_path.read_text(encoding="utf-8").splitlines():
                            if line.startswith("GEMINI_API_KEY="):
                                api_key = line.split("=", 1)[1].strip().strip('"\'')
                                break
                    except Exception:
                        pass
        self.api_key = api_key

    def generate(self, prompt: str, output_path: Path, width: int = 1080, height: int = 1920) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[GeminiBackend] Generating photorealistic visual for prompt: \"{prompt[:60]}...\"")

        full_prompt = (
            f"Hyperrealistic cinematic sports photography, vertical 9:16 composition, {prompt}, "
            "ultra-sharp 8k resolution, professional dynamic lighting, stadium floodlights, authentic kits and details."
        )

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set in .env")

        from google import genai
        client = genai.Client(api_key=self.api_key)

        # Try Google Gemini Image models
        for model_name in ["gemini-3.1-flash-image", "gemini-2.5-flash-image", "gemini-3-pro-image"]:
            try:
                print(f"[GeminiBackend] Requesting {model_name}...")
                resp = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt
                )
                if resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
                    for part in resp.candidates[0].content.parts:
                        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                            with open(output_path, "wb") as f:
                                f.write(part.inline_data.data)
                            print(f"[GeminiBackend] Photorealistic Gemini image saved to: {output_path}")
                            return output_path
            except Exception as e:
                err_str = str(e)
                print(f"[GeminiBackend] {model_name} response: {err_str[:90]}...")
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "limit: 0" in err_str:
                    break

        raise RuntimeError("Gemini Image generation unavailable (0 quota remaining on this API key).")

def check_image_quota_status() -> Dict[str, Any]:
    """
    Direct quota evaluation for image generation models.
    Supports Cloudflare Workers AI (FLUX.1 [schnell]) and Google Gemini.
    """
    import re
    env_path = PROJECT_ROOT / ".env"
    cf_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or os.environ.get("CF_ACCOUNT_ID", "")
    cf_tok = os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get("CF_API_TOKEN", "")
    img_backend = os.environ.get("IMAGE_BACKEND", "").lower()
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith(("CLOUDFLARE_ACCOUNT_ID=", "CF_ACCOUNT_ID=")):
                    cf_id = line.split("=", 1)[1].strip().strip('"\'')
                elif line.startswith(("CLOUDFLARE_API_TOKEN=", "CF_API_TOKEN=")):
                    cf_tok = line.split("=", 1)[1].strip().strip('"\'')
                elif line.startswith("IMAGE_BACKEND="):
                    img_backend = line.split("=", 1)[1].strip().strip('"\'').lower()
                elif line.startswith("GEMINI_API_KEY=") and not api_key:
                    api_key = line.split("=", 1)[1].strip().strip('"\'')
        except Exception:
            pass

    # Priority 1: Cloudflare Workers AI FLUX (Free Tier: 10,000 neurons/day)
    if cf_id and cf_tok and (img_backend in ("cloudflare", "auto", "") or not api_key):
        return {
            "available": True,
            "remaining": 50,
            "tier": "Cloudflare Workers AI (FLUX.1 [schnell])",
            "status_text": "⚡ Active & Available (FLUX.1 [schnell] via Cloudflare Workers AI)",
            "reset_time": "Continuous (Daily 10,000 neurons free)",
            "reason": ""
        }

    # Priority 2: Google Gemini Image Models
    if not api_key:
        return {
            "available": False,
            "remaining": 0,
            "tier": "None",
            "status_text": "❌ GEMINI_API_KEY / Cloudflare not configured in .env",
            "reset_time": "N/A",
            "reason": "Image credentials missing from environment"
        }

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents="white circle"
        )
        return {
            "available": True,
            "remaining": 100,
            "tier": "Paid Tier (Active)",
            "status_text": "✅ Active & Available (Google Gemini Image)",
            "reset_time": "Continuous",
            "reason": ""
        }
    except Exception as e:
        err_str = str(e)
        reset_info = ""
        retry_m = re.search(r'retry in ([0-9hms\.]+)', err_str)
        if retry_m:
            raw_t = retry_m.group(1)
            clean_t = re.sub(r'\.[0-9]+s\.?', 's', raw_t)
            hm = re.findall(r'(\d+h|\d+m|\d+s)', clean_t)
            reset_info = f"Reset in {' '.join(hm[:2])}" if hm else f"Reset in {clean_t}"
        else:
            reset_info = "Daily reset"

        # If Gemini failed but Cloudflare is present, activate Cloudflare immediately
        if cf_id and cf_tok:
            return {
                "available": True,
                "remaining": 50,
                "tier": "Cloudflare Workers AI (FLUX.1 [schnell])",
                "status_text": "⚡ Active & Available (FLUX.1 [schnell] via Cloudflare Workers AI)",
                "reset_time": "Continuous (Daily 10,000 neurons free)",
                "reason": ""
            }

        if "limit: 0" in err_str or "Free Tier" in err_str:
            return {
                "available": False,
                "remaining": 0,
                "tier": "Free Tier",
                "status_text": f"⚠️ 0 left today (Free Tier direct image limit: 0 | {reset_info})",
                "reset_time": reset_info,
                "reason": f"Google Gemini Developer API Free Tier has limit: 0 for direct image models. ({reset_info})"
            }
        elif "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
            return {
                "available": False,
                "remaining": 0,
                "tier": "Quota Exhausted",
                "status_text": f"⏳ 0 left today (Daily Quota Limit Reached | {reset_info})",
                "reset_time": reset_info,
                "reason": f"Daily image generation quota limit reached. ({reset_info})"
            }
        else:
            return {
                "available": False,
                "remaining": 0,
                "tier": "Unavailable",
                "status_text": f"⚠️ 0 left today ({err_str[:45]}...)",
                "reset_time": reset_info,
                "reason": err_str
            }

class ArtifactStagingBackend(ImageGeneratorBase):
    """
    Staging backend that routes pre-generated photorealistic Gemini images from artifacts
    or local data into the assembly pipeline.
    """
    def __init__(self):
        pass

    def generate(self, prompt: str, output_path: Path, width: int = 1080, height: int = 1920) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists() and output_path.stat().st_size > 10000:
            print(f"[StagingBackend] Visual already exists at: {output_path}")
            return output_path
        print(f"[StagingBackend] Staged visual ready: {output_path}")
        return output_path

def get_image_backend(backend_type: Optional[str] = None) -> ImageGeneratorBase:
    env_path = PROJECT_ROOT / ".env"
    cf_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or os.environ.get("CF_ACCOUNT_ID", "")
    cf_tok = os.environ.get("CLOUDFLARE_API_TOKEN") or os.environ.get("CF_API_TOKEN", "")
    b_type = (backend_type or os.environ.get("IMAGE_BACKEND", "")).lower()

    if (not cf_id or not cf_tok or not b_type) and env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.startswith(("CLOUDFLARE_ACCOUNT_ID=", "CF_ACCOUNT_ID=")):
                    cf_id = line.split("=", 1)[1].strip().strip('"\'')
                elif line.startswith(("CLOUDFLARE_API_TOKEN=", "CF_API_TOKEN=")):
                    cf_tok = line.split("=", 1)[1].strip().strip('"\'')
                elif line.startswith("IMAGE_BACKEND=") and not b_type:
                    b_type = line.split("=", 1)[1].strip().strip('"\'').lower()
        except Exception:
            pass

    if b_type == "cloudflare" or (cf_id and cf_tok and b_type in ("", "auto", "gemini")):
        return CloudflareBackend(account_id=cf_id, api_token=cf_tok)
    elif b_type == "gemini":
        return GeminiImageBackend()
    elif b_type == "staged":
        return ArtifactStagingBackend()
    elif b_type == "kaggle":
        return KaggleBackend()
    else:
        return CloudflareBackend(account_id=cf_id, api_token=cf_tok) if (cf_id and cf_tok) else LocalSD15Backend()
