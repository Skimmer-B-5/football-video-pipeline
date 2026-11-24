"""
# PROVENANCE: Copied from stages/unified_image_engine.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ - Safe experimental development environment.
"""

"""
Unified Tri-Agent Image Engine for @Footballin30sec.
Coordinates:
- Agent 1: Multi-Source Scrapers (Bing High-Res & Tall, DuckDuckGo, Wikimedia 4K, Reddit)
- Agent 2: Computer Vision Quality Gate & OpenCV Subject Centering (1080x1920 broadcast framing)
- Agent 3: Groq Qwen/GPT Semantic Query Planner, Pre-Download Context Audit & Perceptual Anti-Repetition
"""

import os
import sys
import time
import io
import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from stages.image_scrapers import (
    HighResImagePipeline,
    ScrapedImage,
    is_stock_watermark_url,
    get_request_headers
)
from stages.image_quality_sensor import (
    get_image_quality_sensor,
    process_and_frame,
    QualityGateResult,
    FramingResult
)
from stages.image_semantic_agent import (
    get_semantic_agent,
    SemanticQueryPlan,
    CandidateAuditResult
)

class UnifiedImageEngine:
    """
    Production-grade image engine that coordinates all 3 visual agents to guarantee:
    1. Zero out-of-context images (e.g. Bale golfing, not 2014 Madrid)
    2. Zero low-resolution or blurry imagery (Strict max_dim >= 1080p, Laplacian > 80)
    3. Zero watermark stock photos (Alamy/Getty preview ban)
    4. Perfect subject centering in 9:16 broadcast framing
    5. Zero duplicate images across videos (Perceptual dHash/pHash deduplication)
    """

    def __init__(self):
        self.scraper_pipeline = HighResImagePipeline()
        self.quality_sensor = get_image_quality_sensor()
        self.semantic_agent = get_semantic_agent()

    def source_scene_image(
        self,
        scene_id: int,
        scene_text: str,
        entity: Optional[str] = None,
        action: Optional[str] = None,
        scene_type: str = "editorial",
        output_path: Optional[str] = None,
        prefer_aspect: str = "tall",
        framing_mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        Executes the tri-agent pipeline to find, verify, and frame an image for a script scene.
        """
        start_time = time.time()
        print(f"\n=======================================================")
        print(f" [Tri-Agent] Sourcing Visual Asset for Scene {scene_id}")
        print(f" Script: \"{scene_text}\"")
        print(f" Entity: '{entity}' | Action: '{action}' | Type: '{scene_type}'")
        print(f"=======================================================")

        # -------------------------------------------------------------
        # STEP 1 (Agent 3): Semantic Query Planning with Negative Filters
        # -------------------------------------------------------------
        plan: SemanticQueryPlan = self.semantic_agent.plan_queries(
            scene_desc=scene_text,
            scene_type=scene_type,
            context=action or "",
            entity=entity
        )
        print(f" [Agent 3 Plan] Primary Query: \"{plan.primary_query}\"")
        print(f" [Agent 3 Plan] Negatives: {plan.negative_filters}")
        print(f" [Agent 3 Plan] Alternatives: {plan.alternative_queries}")

        # -------------------------------------------------------------
        # STEP 2 (Agent 1): Multi-Source High-Res Web Scraping
        # -------------------------------------------------------------
        scraped_candidates = []
        queries = [plan.primary_query] + plan.alternative_queries

        for q in queries[:3]:
            print(f" [Agent 1 Scraper] Querying sources for: \"{q}\" (aspect={prefer_aspect})...")
            results = self.scraper_pipeline.scrape_all(
                query=q,
                aspect=prefer_aspect,
                min_dimension=1080,
                verify_online=False,  # We will verify during download
                max_verified=10
            )
            for r in results:
                scraped_candidates.append({
                    "url": r.url,
                    "title": r.title,
                    "desc": r.metadata.get("snippet", "") if hasattr(r, "metadata") and r.metadata else r.title,
                    "source": r.source,
                    "page_url": r.page_url,
                    "aspect_ratio": r.aspect,
                    "width": r.width,
                    "height": r.height
                })
            if len(scraped_candidates) >= 12:
                break

        print(f" [Agent 1 Scraper] Collected {len(scraped_candidates)} raw candidate images.")

        if not scraped_candidates:
            # Fallback to general query if specific query returned zero
            fallback_q = f"{entity or 'football player'} {action or 'match'}"
            print(f" [Agent 1 Scraper] Fallback to broad query: \"{fallback_q}\"")
            results = self.scraper_pipeline.scrape_all(
                query=fallback_q,
                aspect="any",
                min_dimension=1080,
                verify_online=False,
                max_verified=8
            )
            for r in results:
                scraped_candidates.append({
                    "url": r.url,
                    "title": r.title,
                    "desc": r.metadata.get("snippet", "") if hasattr(r, "metadata") and r.metadata else r.title,
                    "source": r.source,
                    "page_url": r.page_url,
                    "aspect_ratio": r.aspect,
                    "width": r.width,
                    "height": r.height
                })

        # -------------------------------------------------------------
        # STEP 3 (Agent 3): Candidate Semantic Audit & Negative Filtering
        # -------------------------------------------------------------
        audited_pairs = self.semantic_agent.audit_candidates_batch(
            candidates=scraped_candidates,
            plan=plan,
            max_verified=10,
            use_llm=False
        )

        valid_candidates = []
        for cand, audit in audited_pairs:
            if audit.passed:
                cand["semantic_score"] = audit.confidence
                cand["audit_reasons"] = [audit.reason]
                valid_candidates.append(cand)
            else:
                print(f" [Agent 3 Audit] Rejected '{cand.get('title', '')[:40]}': {audit.reason}")

        print(f" [Agent 3 Audit] {len(valid_candidates)} candidates passed semantic context audit.")

        # Sort highest confidence first
        valid_candidates.sort(key=lambda x: x.get("semantic_score", 0.0), reverse=True)

        # -------------------------------------------------------------
        # STEP 4 (Agent 2): Quality Gate Download & Framing
        # -------------------------------------------------------------
        if not output_path:
            out_dir = PROJECT_ROOT / "data" / "unified_images"
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(out_dir / f"scene_{scene_id}_1080x1920.png")

        temp_dir = PROJECT_ROOT / "data" / "temp_downloads"
        temp_dir.mkdir(parents=True, exist_ok=True)

        accepted_data = None
        framing_result = None
        quality_result = None

        for i, cand in enumerate(valid_candidates[:12]):
            img_url = cand.get("url")
            if not img_url or is_stock_watermark_url(img_url):
                continue

            temp_file = str(temp_dir / f"scene_{scene_id}_candidate_{i}.jpg")
            try:
                # Clean URL spaces if any
                clean_url = urllib.parse.quote(img_url, safe=':/?=&%#+~')
                # Download bytes with host-specific headers
                req_headers = get_request_headers(clean_url)
                req = urllib.request.Request(clean_url, headers=req_headers)
                with urllib.request.urlopen(req, timeout=9) as resp:
                    raw_bytes = resp.read()

                if len(raw_bytes) < 40000:  # Minimum 40KB
                    continue

                with open(temp_file, "wb") as f_out:
                    f_out.write(raw_bytes)

                # Process with Agent 2 (Strict Quality Gate + Centered 9:16 Framing)
                passed, f_res, q_res = process_and_frame(
                    image_input=temp_file,
                    output_path=output_path,
                    source_ref=img_url,
                    strict_gate=True,
                    framing_mode=framing_mode
                )

                if not passed or not f_res:
                    print(f" [Agent 2 Vision] Candidate {i} failed gate/framing: {q_res.rejection_reasons}")
                    continue

                # Record download in Agent 3's Perceptual History
                is_unique, dedup_reason, _ = self.semantic_agent.verify_and_record_download(
                    image_bytes=raw_bytes,
                    url=img_url,
                    entity=entity or "",
                    scene_id=scene_id
                )

                if not is_unique:
                    print(f" [Agent 3 Dedup] Candidate {i} is a perceptual duplicate: {dedup_reason}")
                    continue

                # Success!
                accepted_data = cand
                framing_result = f_res
                quality_result = q_res
                print(f" [SUCCESS] Scene {scene_id} asset verified and framed!")
                print(f"  Output Path: {output_path}")
                print(f"  Source: {cand.get('source')} | Dimensions: {q_res.width}x{q_res.height} -> 1080x1920")
                print(f"  Sharpness (Laplacian): {q_res.laplacian_variance:.1f} | Quality Score: {q_res.quality_score:.1f}/100")
                print(f"  Framing Mode: {f_res.framing_mode} | Aspect: {f_res.aspect_tag}")
                break

            except Exception as dl_err:
                print(f" [Download Error] Candidate {i}: {dl_err}")
                continue

        elapsed = time.time() - start_time

        if accepted_data and framing_result and quality_result:
            return {
                "success": True,
                "scene_id": scene_id,
                "output_path": output_path,
                "url": accepted_data.get("url"),
                "source": accepted_data.get("source"),
                "aspect_tag": quality_result.aspect_tag,
                "framing_mode": framing_result.framing_mode,
                "quality_score": quality_result.quality_score,
                "sharpness": quality_result.laplacian_variance,
                "resolution": f"{quality_result.width}x{quality_result.height}",
                "elapsed_sec": round(elapsed, 2)
            }
        else:
            return {
                "success": False,
                "scene_id": scene_id,
                "error": "No candidates passed strict tri-agent verification",
                "elapsed_sec": round(elapsed, 2)
            }

_GLOBAL_ENGINE = None

def get_unified_image_engine() -> UnifiedImageEngine:
    global _GLOBAL_ENGINE
    if _GLOBAL_ENGINE is None:
        _GLOBAL_ENGINE = UnifiedImageEngine()
    return _GLOBAL_ENGINE

if __name__ == "__main__":
    engine = get_unified_image_engine()
    # Test on Gareth Bale golfing (the exact user pain point!)
    res = engine.source_scene_image(
        scene_id=1,
        scene_text="Gareth Bale has retired from football to play golf on the sunny greens of California.",
        entity="Gareth Bale",
        action="playing golf swing fairway",
        scene_type="editorial",
        prefer_aspect="tall"
    )
    print("\nResult:")
    print(json.dumps(res, indent=2))
