"""
FS 30 Composition Recipes Subsystem (H1).
Defines 8 deterministic in-code composition recipes:
1. hook_portrait
2. stat_callout
3. versus
4. quote_card
5. timeline
6. rumour_stamp
7. newspaper_headline
8. location_card

Each recipe defines layout geometry, safe-zone coordinates, layer stacking (z-index),
and stop-motion animation timing. The LLM only supplies slot parameters.
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import numpy as np

from fs30.paper_compositor import (
    create_dual_paper_shadows,
    apply_handcut_paper_edge,
    multiply_paper_texture,
    create_text_card_taped_label,
    create_text_card_torn_strip,
    create_text_card_newspaper,
    create_text_card_rubber_stamp,
    create_text_card_ticket,
    create_content_starburst,
    DEFAULT_PALETTE
)
from fs30.cutout_refiner import refine_cutout_matte
from fs30.paper_motion import (
    apply_paper_boil,
    render_stroke_reveal_mark,
    render_safe_zone_caption
)
from fs30.assets.library import library

RECIPE_REGISTRY = [
    "hook_portrait",
    "stat_callout",
    "versus",
    "quote_card",
    "timeline",
    "rumour_stamp",
    "newspaper_headline",
    "location_card"
]

_RECIPE_IMAGE_CACHE: Dict[str, Image.Image] = {}
_RECIPE_CUTOUT_CACHE: Dict[Tuple[str, int, int], Image.Image] = {}

def get_cached_cutout(sub_path: str, target_size: Tuple[int, int]) -> Image.Image:
    key = (str(sub_path), target_size[0], target_size[1])
    if key not in _RECIPE_CUTOUT_CACHE:
        with Image.open(sub_path) as s_raw:
            ref = refine_cutout_matte(s_raw, erode_px=2, defringe=True)
            _RECIPE_CUTOUT_CACHE[key] = apply_handcut_paper_edge(ref, stroke_w=10).resize(target_size, Image.Resampling.LANCZOS)
    return _RECIPE_CUTOUT_CACHE[key]

def render_recipe_frame(
    recipe_name: str,
    slots: Dict[str, Any],
    t: float,
    duration: float = 4.0,
    boil_enabled: bool = True
) -> Image.Image:
    """
    Renders a single 1080x1920 frame for a chosen recipe and slot dictionary at time t.
    """
    canvas = Image.new("RGBA", (1080, 1920), (14, 16, 22, 255))
    f_idx = int(t * 12)

    # 1. Background layer (Shared across all recipes)
    bg_path = slots.get("bg_path")
    if bg_path and Path(bg_path).exists():
        bg_key = str(bg_path)
        if bg_key not in _RECIPE_IMAGE_CACHE:
            with Image.open(bg_path) as bg:
                _RECIPE_IMAGE_CACHE[bg_key] = bg.convert("RGB")
        bg = _RECIPE_IMAGE_CACHE[bg_key]
        # Subtle camera motion
        scale = 1.0 + (t / max(0.1, duration)) * 0.05
        tw, th = int(1080 * scale), int(1920 * scale)
        bg_fit = ImageOps.fit(bg, (tw, th))
        crop_x = (tw - 1080) // 2
        crop_y = (th - 1920) // 2
        bg_cropped = bg_fit.crop((crop_x, crop_y, crop_x + 1080, crop_y + 1920))
        bg_textured = multiply_paper_texture(bg_cropped, intensity=0.35)
        canvas.paste(bg_textured, (0, 0))

    # 2. Recipe Specific Layouts
    if recipe_name == "hook_portrait":
        # Slots: headline_text, stat_text, subject_path, caption_words, active_word_idx
        # Event 1 (t=0.0): Taped headline card
        head_text = slots.get("headline_text", "BREAKING NEWS")
        card = create_text_card_taped_label(head_text, font_size=46)
        card_boil = apply_paper_boil(card, f_idx, enabled=boil_enabled)
        c_sh, c_pad = create_dual_paper_shadows(card_boil, z_gap=0.75)
        cx = (1080 - card_boil.width) // 2
        canvas.paste(c_sh, (cx - c_pad, 130 - c_pad), c_sh)
        canvas.paste(card_boil, (cx, 130), card_boil)

        # Event 1 (t=0.0): Subject cutout
        sub_path = slots.get("subject_path")
        if sub_path and Path(sub_path).exists():
            paper_sub = get_cached_cutout(sub_path, (700, 990))
            sub_boil = apply_paper_boil(paper_sub, f_idx, enabled=boil_enabled)
            s_sh, s_pad = create_dual_paper_shadows(sub_boil, z_gap=0.6)
            canvas.paste(s_sh, (220 - s_pad, 680 - s_pad), s_sh)
            canvas.paste(sub_boil, (220, 680), sub_boil)

        # Event 2 (t >= 1.0s): Content Starburst
        stat_text = slots.get("stat_text", "OFFICIAL")
        if t >= 0.8:
            p_pop = min(1.0, (t - 0.8) / 0.25)
            sb = create_content_starburst(stat_text, color=DEFAULT_PALETTE["red"], size=(420, 420))
            if p_pop < 1.0:
                sw = max(10, int(420 * p_pop))
                sb = sb.resize((sw, sw), Image.Resampling.BILINEAR)
            sb_boil = apply_paper_boil(sb, f_idx, enabled=boil_enabled)
            sb_sh, sb_pad = create_dual_paper_shadows(sb_boil, z_gap=0.45)
            canvas.paste(sb_sh, (130 - sb_pad, 330 - sb_pad), sb_sh)
            canvas.paste(sb_boil, (130, 330), sb_boil)

        # Event 3 (t >= 2.0s): Scribble arrow pointing to subject
        if t >= 1.8:
            p_arr = min(1.0, (t - 1.8) / 0.35)
            arrow_item = library.pick("arrow", tags=["arrow", "pointer", "yellow"])
            if arrow_item and Path(arrow_item["path"]).exists():
                with Image.open(arrow_item["path"]) as arr_im:
                    arr_rot = arr_im.resize((220, 150), Image.Resampling.BILINEAR).rotate(15, expand=True)
                    rev_arr = render_stroke_reveal_mark(arr_rot, p_arr, direction="left_to_right")
                    canvas.paste(rev_arr, (560, 420), rev_arr)

    elif recipe_name == "stat_callout":
        # Slots: headline_text, stat_number, stat_label, subject_path
        # Event 1: Admission Ticket Card
        ticket = create_text_card_ticket(slots.get("headline_text", "OFFICIAL RECORD"), meta_text="STAT REPORT")
        t_boil = apply_paper_boil(ticket, f_idx, enabled=boil_enabled)
        t_sh, t_pad = create_dual_paper_shadows(t_boil, z_gap=0.7)
        cx = (1080 - t_boil.width) // 2
        canvas.paste(t_sh, (cx - t_pad, 140 - t_pad), t_sh)
        canvas.paste(t_boil, (cx, 140), t_boil)

        # Event 2: Giant Stat Card in center
        stat_num = slots.get("stat_number", "£120M")
        stat_card = create_text_card_torn_strip(f"{stat_num} VALUE", font_size=58, fill_color=DEFAULT_PALETTE["cream"], text_color=DEFAULT_PALETTE["red"])
        sc_boil = apply_paper_boil(stat_card, f_idx, enabled=boil_enabled)
        sc_sh, sc_pad = create_dual_paper_shadows(sc_boil, z_gap=0.6)
        sc_x = (1080 - sc_boil.width) // 2
        canvas.paste(sc_sh, (sc_x - sc_pad, 520 - sc_pad), sc_sh)
        canvas.paste(sc_boil, (sc_x, 520), sc_boil)

        # Event 3: Scribble underline + push-pin
        pin_item = library.pick("sticker", tags=["push_pin", "pin"])
        if pin_item and Path(pin_item["path"]).exists():
            with Image.open(pin_item["path"]) as pin_im:
                p_thumb = pin_im.resize((140, 160), Image.Resampling.LANCZOS).rotate(-12, expand=True)
                canvas.paste(p_thumb, (sc_x - 30, 480), p_thumb)

        # Subject in lower-right
        sub_path = slots.get("subject_path")
        if sub_path and Path(sub_path).exists():
            p_sub = get_cached_cutout(sub_path, (580, 820))
            canvas.paste(p_sub, (420, 840), p_sub)

    elif recipe_name == "versus":
        # Slots: team_a, team_b, score_text, headline_text
        # Event 1: Newspaper top banner
        head_text = slots.get("headline_text", "CLASH OF TITANS")
        n_card = create_text_card_newspaper(head_text, sub_tag="MATCHDAY SHOWDOWN")
        n_sh, n_pad = create_dual_paper_shadows(n_card, z_gap=0.7)
        cx = (1080 - n_card.width) // 2
        canvas.paste(n_sh, (cx - n_pad, 130 - n_pad), n_sh)
        canvas.paste(n_card, (cx, 130), n_card)

        # Event 2: Stadium Scoreboard Card
        from fs30.assets.sticker_kit import make_scoreboard
        scoreboard = make_scoreboard(size=(680, 340))
        sb_boil = apply_paper_boil(scoreboard, f_idx, enabled=boil_enabled)
        sb_sh, sb_pad = create_dual_paper_shadows(sb_boil, z_gap=0.55)
        sb_x = (1080 - sb_boil.width) // 2
        canvas.paste(sb_sh, (sb_x - sb_pad, 540 - sb_pad), sb_sh)
        canvas.paste(sb_boil, (sb_x, 540), sb_boil)

        # Event 3: Action burst "VERSUS" in center
        burst = create_content_starburst("VS", color=DEFAULT_PALETTE["yellow"], size=(280, 280))
        b_sh, b_pad = create_dual_paper_shadows(burst, z_gap=0.8)
        canvas.paste(b_sh, (400 - b_pad, 940 - b_pad), b_sh)
        canvas.paste(burst, (400, 940), burst)

    elif recipe_name == "quote_card":
        # Slots: quote_text, speaker_name, subject_path
        q_text = slots.get("quote_text", "WE MUST WIN")
        spk_name = slots.get("speaker_name", "MANAGER")
        
        # Newsprint card with large quote
        q_card = create_text_card_newspaper(f"\"{q_text}\"", sub_tag=f"STATEMENT: {spk_name}", font_size=40)
        q_boil = apply_paper_boil(q_card, f_idx, enabled=boil_enabled)
        q_sh, q_pad = create_dual_paper_shadows(q_boil, z_gap=0.75)
        cx = (1080 - q_boil.width) // 2
        canvas.paste(q_sh, (cx - q_pad, 160 - q_pad), q_sh)
        canvas.paste(q_boil, (cx, 160), q_boil)

        # Subject reaction cutout below
        sub_path = slots.get("subject_path")
        if sub_path and Path(sub_path).exists():
            p_sub = get_cached_cutout(sub_path, (660, 940))
            canvas.paste(p_sub, (210, 680), p_sub)

    elif recipe_name == "timeline":
        # Slots: event_1, event_2, headline_text
        head_text = slots.get("headline_text", "CRISIS TIMELINE")
        strip_top = create_text_card_torn_strip(head_text, font_size=46, fill_color=DEFAULT_PALETTE["cream"], text_color=DEFAULT_PALETTE["red"])
        cx = (1080 - strip_top.width) // 2
        canvas.paste(strip_top, (cx, 130), strip_top)

        # Timeline cards
        t1 = create_text_card_taped_label(slots.get("event_1", "OCT: HAMSTRING STRAIN"), font_size=38)
        canvas.paste(t1, (100, 480), t1)

        t2 = create_text_card_taped_label(slots.get("event_2", "NOV: SURGERY CONFIRMED"), font_size=38)
        canvas.paste(t2, (140, 820), t2)

        # Arrow pointing down
        arrow_item = library.pick("arrow", tags=["arrow", "down", "yellow"])
        if arrow_item and Path(arrow_item["path"]).exists():
            with Image.open(arrow_item["path"]) as arr_im:
                arr_rot = arr_im.resize((180, 180), Image.Resampling.BILINEAR).rotate(-90, expand=True)
                canvas.paste(arr_rot, (450, 680), arr_rot)

    elif recipe_name == "rumour_stamp":
        # Slots: headline_text, stamp_text, subject_path
        head_text = slots.get("headline_text", "ARSENAL TARGET")
        taped_card = create_text_card_taped_label(head_text, font_size=44)
        cx = (1080 - taped_card.width) // 2
        canvas.paste(taped_card, (cx, 140), taped_card)

        # Subject
        sub_path = slots.get("subject_path")
        if sub_path and Path(sub_path).exists():
            p_sub = get_cached_cutout(sub_path, (680, 960))
            canvas.paste(p_sub, (200, 660), p_sub)

        # Slamming Rubber Stamp (t >= 1.0s)
        stamp_str = slots.get("stamp_text", "RUMOUR")
        stamp = create_text_card_rubber_stamp(stamp_str, color=DEFAULT_PALETTE["red"])
        st_sh, st_pad = create_dual_paper_shadows(stamp, z_gap=0.9)
        canvas.paste(st_sh, (260 - st_pad, 420 - st_pad), st_sh)
        canvas.paste(stamp, (260, 420), stamp)

    elif recipe_name == "newspaper_headline":
        # Slots: headline_text, sub_tag, subject_path
        head_text = slots.get("headline_text", "GLOBAL CONTROVERSY")
        n_card = create_text_card_newspaper(head_text, sub_tag=slots.get("sub_tag", "SPECIAL REPORT"), font_size=42)
        cx = (1080 - n_card.width) // 2
        canvas.paste(n_card, (cx, 140), n_card)

        # Cutout
        sub_path = slots.get("subject_path")
        if sub_path and Path(sub_path).exists():
            p_sub = get_cached_cutout(sub_path, (660, 940))
            canvas.paste(p_sub, (210, 680), p_sub)

    elif recipe_name == "location_card":
        # Slots: stadium_name, match_text
        ticket = create_text_card_ticket(slots.get("match_text", "CHAMPIONS LEAGUE NIGHT"), meta_text=slots.get("stadium_name", "SANTIAGO BERNABÉU"))
        cx = (1080 - ticket.width) // 2
        canvas.paste(ticket, (cx, 160), ticket)

        # Push-pin & Trophy
        trophy_item = library.pick("sticker", tags=["trophy", "cup"])
        if trophy_item and Path(trophy_item["path"]).exists():
            with Image.open(trophy_item["path"]) as tr_im:
                tr_thumb = tr_im.resize((360, 420), Image.Resampling.LANCZOS)
                canvas.paste(tr_thumb, (360, 680), tr_thumb)

    # 3. Safe-Zone Caption Strip (Shared across all recipes at y = 1920 - 380px)
    caption_words = slots.get("caption_words", ["FOOTBALL", "IN", "THIRTY", "SECONDS"])
    active_idx = slots.get("active_word_idx", 0)
    cap = render_safe_zone_caption(caption_words, active_idx, strip_width=860)
    canvas.paste(cap, ((1080 - 860) // 2, 1920 - 380), cap)

    return canvas.convert("RGB")
