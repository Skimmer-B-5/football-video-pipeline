"""
beta/stages/contact_sheet_builder_v3.py - 3-View Diagnostic Contact Sheet Builder (V6.4.2).

Satisfies Section 6 Requirements:
Shows 3 views per scene:
1. Original Raw Asset (full native aspect ratio).
2. Proposed Vertical Crop (with diagnostic bounding boxes, focal crosshair, and safe-zone guides).
3. Final Broadcast Crop (clean 9:16 master preview with all overlays removed).

Features:
- Separate diagnostic overlays from clean visual preview.
- 4 Independent Quality Gates: Visual Relevance, Event Provenance, Composition, Rights Status.
- Source provenance, original image date, event date, effective crop resolution, scale factor.
- Narrative suitability explanation ("What information does this photograph add?").
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


class DiagnosticContactSheetBuilderV3:
    @staticmethod
    def create_story_contact_sheet(
        story_title: str,
        story_id: str,
        scenes_data: List[Dict[str, Any]],
        out_path: Path
    ) -> bool:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        total_w = 1920
        row_h = 560
        header_h = 120
        total_h = header_h + len(scenes_data) * row_h + 40

        canvas = Image.new("RGB", (total_w, total_h), color=(15, 17, 23))
        draw = ImageDraw.Draw(canvas)

        # Main Header Bar
        draw.rectangle([(0, 0), (total_w, header_h)], fill=(22, 26, 36))
        draw.text((40, 22), "30 FOOTBALL PLUS — V6.4.2 3-VIEW COMPOSITION & IMAGE RELEVANCE AUDIT", fill=(255, 215, 0))
        draw.text((40, 58), f"STORY: {story_title.upper()}", fill=(240, 245, 255))
        draw.text((40, 88), "INDEPENDENT GATES: Visual Relevance | Event Provenance | Action-Aware Composition | Rights Classification", fill=(170, 185, 205))

        for idx, sc in enumerate(scenes_data):
            y_base = header_h + idx * row_h + 15
            sc_id = sc.get("scene_id", f"s{idx+1:02d}")
            role = sc.get("role", "scene")
            overall_status = sc.get("overall_status", "PROVISIONAL_REVIEW")
            gates = sc.get("gates", {})
            orig_bgr = sc.get("orig_bgr")
            clean_crop_bgr = sc.get("clean_crop_bgr")
            crop_meta = sc.get("crop_meta", {})
            prov = sc.get("provenance", {})
            suitability_note = sc.get("suitability_note", "Contextual storytelling illustration.")

            # Row container card
            status_color = (46, 204, 113) if overall_status == "APPROVED" else \
                           (241, 196, 15) if "PROVISIONAL" in overall_status else \
                           (230, 126, 34) if "MANUAL" in overall_status else (231, 76, 60)

            draw.rectangle([(20, y_base), (total_w - 20, y_base + row_h - 15)], fill=(20, 24, 33), outline=(40, 48, 64), width=1)

            # Header row inside card
            draw.rectangle([(20, y_base), (total_w - 20, y_base + 46)], fill=(26, 32, 45))
            draw.text((35, y_base + 12), f"SCENE {sc_id.upper()} — ROLE: {role.upper()}", fill=(255, 215, 0))
            intended_subj = sc.get("intended_subject", "Subject")
            assessed_subj = sc.get("assessed_subject", intended_subj)
            draw.text((320, y_base + 12), f"INTENDED: {intended_subj} | ASSESSED: {assessed_subj}", fill=(210, 225, 245))

            # Overall Status Badge (Top right)
            badge_w = 230
            draw.rectangle([(total_w - 20 - badge_w, y_base + 8), (total_w - 30, y_base + 38)], fill=status_color)
            draw.text((total_w - 20 - badge_w + 15, y_base + 14), f"STATUS: {overall_status}", fill=(15, 17, 23))

            # Spoken Narration line
            narration = sc.get("narration", "")
            if narration:
                draw.text((35, y_base + 52), f"Narration: \"{narration}\"", fill=(180, 195, 215))

            pane_y = y_base + 80
            pane_h = 440

            # ---------------------------------------------------------
            # VIEW 1: RAW ASSET (Full Uncropped Native Aspect Ratio)
            # ---------------------------------------------------------
            view1_w = 380
            view1_x = 35
            draw.rectangle([(view1_x, pane_y), (view1_x + view1_w, pane_y + pane_h)], fill=(12, 14, 20), outline=(50, 60, 80))
            draw.text((view1_x + 10, pane_y + 8), "VIEW 1: ORIGINAL ASSET", fill=(200, 215, 240))

            if orig_bgr is not None and orig_bgr.size > 0:
                o_h, o_w = orig_bgr.shape[:2]
                draw.text((view1_x + 190, pane_y + 8), f"({o_w}x{o_h})", fill=(140, 155, 175))
                # Fit into 360x390
                scale_fit = min(360.0 / float(o_w), 390.0 / float(o_h))
                fit_w = max(1, int(o_w * scale_fit))
                fit_h = max(1, int(o_h * scale_fit))
                fitted = cv2.resize(orig_bgr, (fit_w, fit_h), interpolation=cv2.INTER_AREA)
                fit_pil = Image.fromarray(cv2.cvtColor(fitted, cv2.COLOR_BGR2RGB))

                off_x = view1_x + int((view1_w - fit_w) / 2.0)
                off_y = pane_y + 35 + int((390 - fit_h) / 2.0)
                canvas.paste(fit_pil, (off_x, off_y))
            else:
                draw.text((view1_x + 100, pane_y + 200), "NO ASSET (EDITORIAL GAP)", fill=(231, 76, 60))

            # ---------------------------------------------------------
            # VIEW 2: PROPOSED VERTICAL CROP (With Diagnostic Overlays)
            # ---------------------------------------------------------
            view2_w = 248
            view2_x = view1_x + view1_w + 25
            draw.rectangle([(view2_x, pane_y), (view2_x + view2_w, pane_y + pane_h)], fill=(12, 14, 20), outline=(50, 60, 80))
            draw.text((view2_x + 10, pane_y + 8), "VIEW 2: DIAGNOSTIC CROP", fill=(255, 215, 0))

            if clean_crop_bgr is not None and clean_crop_bgr.size > 0 and overall_status != "REJECTED_GAP":
                diag_bgr = clean_crop_bgr.copy()
                dh, dw = diag_bgr.shape[:2]

                # Draw Safe-Zone Boundaries (y=260 and y=1150 in 1080x1920)
                y_safe_top = int(260 / 1920.0 * dh)
                y_safe_bot = int(1150 / 1920.0 * dh)
                cv2.line(diag_bgr, (0, y_safe_top), (dw, y_safe_top), (0, 255, 255), 3)  # Yellow top guide
                cv2.line(diag_bgr, (0, y_safe_bot), (dw, y_safe_bot), (0, 165, 255), 3)  # Orange bottom guide

                # Draw Subject Detection Box & Center Crosshair
                det = crop_meta.get("detection", {})
                subj_box = crop_meta.get("final_subj_box")
                if subj_box:
                    sx, sy, sw, sh = subj_box
                    cv2.rectangle(diag_bgr, (sx, sy), (sx + sw, sy + sh), (0, 255, 0), 3)

                # Subject focal crosshair
                f_cy = crop_meta.get("final_subj_center_y")
                if f_cy:
                    cv2.drawMarker(diag_bgr, (int(dw / 2.0), int(f_cy)), (0, 0, 255), cv2.MARKER_CROSS, 28, 3)

                # Scale diagnostic crop to 225x400 (9:16)
                disp_w = 225
                disp_h = 400
                diag_resized = cv2.resize(diag_bgr, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
                diag_pil = Image.fromarray(cv2.cvtColor(diag_resized, cv2.COLOR_BGR2RGB))
                off_x2 = view2_x + int((view2_w - disp_w) / 2.0)
                off_y2 = pane_y + 35
                canvas.paste(diag_pil, (off_x2, off_y2))
            else:
                draw.text((view2_x + 40, pane_y + 200), "CROP REJECTED / GAP", fill=(231, 76, 60))

            # ---------------------------------------------------------
            # VIEW 3: CLEAN CROP (Broadcast Master Preview, Zero Overlays)
            # ---------------------------------------------------------
            view3_w = 248
            view3_x = view2_x + view2_w + 25
            draw.rectangle([(view3_x, pane_y), (view3_x + view3_w, pane_y + pane_h)], fill=(12, 14, 20), outline=(50, 60, 80))
            draw.text((view3_x + 10, pane_y + 8), "VIEW 3: CLEAN BROADCAST", fill=(46, 204, 113))

            if clean_crop_bgr is not None and clean_crop_bgr.size > 0 and overall_status != "REJECTED_GAP":
                disp_w = 225
                disp_h = 400
                clean_resized = cv2.resize(clean_crop_bgr, (disp_w, disp_h), interpolation=cv2.INTER_AREA)
                clean_pil = Image.fromarray(cv2.cvtColor(clean_resized, cv2.COLOR_BGR2RGB))
                off_x3 = view3_x + int((view3_w - disp_w) / 2.0)
                off_y3 = pane_y + 35
                canvas.paste(clean_pil, (off_x3, off_y3))
            else:
                draw.text((view3_x + 40, pane_y + 200), "CLEAN CROP VOID", fill=(231, 76, 60))

            # ---------------------------------------------------------
            # METADATA & 4 INDEPENDENT QUALITY GATES COLUMN
            # ---------------------------------------------------------
            info_x = view3_x + view3_w + 25
            info_w = total_w - info_x - 35
            draw.rectangle([(info_x, pane_y), (info_x + info_w, pane_y + pane_h)], fill=(16, 20, 28), outline=(45, 55, 75))

            # Section A: Provenance & Technical Metadata
            draw.text((info_x + 15, pane_y + 12), "PROVENANCE & TECHNICAL METADATA", fill=(255, 215, 0))
            pub_title = prov.get("title", "N/A")[:55]
            draw.text((info_x + 15, pane_y + 35), f"Title: {pub_title}", fill=(210, 220, 235))
            draw.text((info_x + 15, pane_y + 55), f"Source Domain: {prov.get('domain', 'N/A')}", fill=(180, 195, 210))
            draw.text((info_x + 15, pane_y + 75), f"Pub Date: {prov.get('pub_date', 'N/A')} | Event Date: {prov.get('event_date', 'N/A')}", fill=(180, 195, 210))

            eff_res = crop_meta.get("effective_crop_res", "N/A")
            scale_f = crop_meta.get("scale_factor", 1.0)
            strat = crop_meta.get("strategy", sc.get("crop_strategy", "portrait"))
            draw.text((info_x + 15, pane_y + 95), f"Strategy: {strat.upper()} | Native Crop: {eff_res} | Scale: {scale_f}x", fill=(180, 195, 210))

            # Divider line
            draw.line([(info_x + 15, pane_y + 122), (info_x + info_w - 15, pane_y + 122)], fill=(40, 50, 70))

            # Section B: 4 Independent Quality Gates
            draw.text((info_x + 15, pane_y + 132), "INDEPENDENT QUALITY GATES", fill=(255, 215, 0))

            # Gate 1: Visual Relevance
            g_rel = gates.get("visual_relevance", "REVIEW")
            c_rel = (46, 204, 113) if g_rel == "PASS" else (241, 196, 15) if g_rel == "REVIEW" else (231, 76, 60)
            draw.rectangle([(info_x + 15, pane_y + 158), (info_x + 135, pane_y + 184)], fill=c_rel)
            draw.text((info_x + 22, pane_y + 162), f"RELEVANCE: {g_rel}", fill=(15, 17, 23))
            draw.text((info_x + 145, pane_y + 164), f"Adds: {suitability_note[:62]}", fill=(200, 215, 230))

            # Gate 2: Provenance
            g_prov = gates.get("event_provenance", "REVIEW")
            c_prov = (46, 204, 113) if g_prov in ["EXACT_MATCH", "SAME_MATCH"] else (241, 196, 15) if g_prov == "ARCHIVAL" else (231, 76, 60)
            draw.rectangle([(info_x + 15, pane_y + 192), (info_x + 135, pane_y + 218)], fill=c_prov)
            draw.text((info_x + 22, pane_y + 196), f"PROVENANCE: {g_prov[:6]}", fill=(15, 17, 23))
            draw.text((info_x + 145, pane_y + 198), f"Class: {sc.get('asset_classification', 'N/A')}", fill=(200, 215, 230))

            # Gate 3: Composition
            g_comp = gates.get("composition", "REVIEW")
            c_comp = (46, 204, 113) if g_comp == "PASS" else (241, 196, 15) if g_comp == "REVIEW" else (231, 76, 60)
            draw.rectangle([(info_x + 15, pane_y + 226), (info_x + 135, pane_y + 252)], fill=c_comp)
            draw.text((info_x + 22, pane_y + 230), f"COMPOSITION: {g_comp}", fill=(15, 17, 23))
            comp_detail = crop_meta.get("reason", f"Safe-zone: {crop_meta.get('in_safe_zone', False)}")[:62]
            draw.text((info_x + 145, pane_y + 232), comp_detail, fill=(200, 215, 230))

            # Gate 4: Rights Status
            g_rts = gates.get("rights", "UNVERIFIED")
            c_rts = (46, 204, 113) if g_rts == "PUBLIC_DOMAIN" else (52, 152, 219) if g_rts == "EDITORIAL_USE_ONLY" else (231, 76, 60)
            draw.rectangle([(info_x + 15, pane_y + 260), (info_x + 135, pane_y + 286)], fill=c_rts)
            draw.text((info_x + 22, pane_y + 264), f"RIGHTS: {g_rts[:6]}", fill=(15, 17, 23))
            draw.text((info_x + 145, pane_y + 266), f"Status: {g_rts} (Strictly not commercial)", fill=(200, 215, 230))

            # Section C: Editorial Narrative Alignment
            draw.line([(info_x + 15, pane_y + 298), (info_x + info_w - 15, pane_y + 298)], fill=(40, 50, 70))
            draw.text((info_x + 15, pane_y + 308), "EDITORIAL NARRATIVE ALIGNMENT", fill=(255, 215, 0))
            editorial_text = sc.get("editorial_alignment", "Alignment verified.")
            draw.text((info_x + 15, pane_y + 330), editorial_text[:85], fill=(210, 225, 240))
            if len(editorial_text) > 85:
                draw.text((info_x + 15, pane_y + 350), editorial_text[85:170], fill=(210, 225, 240))

            # Rejection / Limitation Note if applicable
            rej_note = sc.get("rejection_or_limitation_note")
            if rej_note:
                draw.text((info_x + 15, pane_y + 380), f"Note: {rej_note[:85]}", fill=(241, 196, 15))

        canvas.save(out_path, format="PNG")
        return True
