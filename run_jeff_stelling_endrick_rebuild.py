"""
run_jeff_stelling_endrick_rebuild.py - Complete Voiceover Swap & Master Render with Jeff Stelling.
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path

from stages.jeff_stelling_synthesizer import synthesize_jeff_stelling_script
from stages.remotion_renderer import (
    prepare_remotion_props,
    render_with_remotion,
    master_audio_and_mux,
    generate_remotion_storyboard
)
from stages.verify_video import inspect_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JeffStellingRebuild")

def generate_aligned_srt(scenes_data: list, output_srt: Path) -> Path:
    """Generates natural phrase-level subtitle cards aligned to synthesized scene timings."""
    cues = []
    current_time = 0.0
    cue_index = 1
    
    for s in scenes_data:
        narration = s["narration"]
        dur = s["duration_sec"]
        words = narration.split()
        
        # Split narration into 3 to 6 word phrases
        chunk_size = 5
        chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        chunk_dur = dur / len(chunks)
        
        for c in chunks:
            start_t = current_time
            end_t = current_time + chunk_dur
            
            def fmt_time(t):
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                sec = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
                
            cues.append(f"{cue_index}\n{fmt_time(start_t)} --> {fmt_time(end_t)}\n{c.upper()}\n")
            cue_index += 1
            current_time = end_t
            
    output_srt.write_text("\n".join(cues), encoding="utf-8")
    return output_srt

def main():
    root = Path(__file__).resolve().parent
    evidence_dir = root / "evidence"
    remotion_dir = root / "remotion"
    audio_dir = root / "data" / "audio"
    temp_dir = root / "data" / "temp_jeff_assembly"
    
    script_file = evidence_dir / "endrick_milan_approved_script_v2.json"
    script_data = json.loads(script_file.read_text(encoding="utf-8"))
    scenes = script_data.get("scenes", [])
    
    logger.info("=== STEP 1: Synthesizing 7 Scenes with Jeff Stelling (Relaxed Pacing 1.02x & Human Breathing) ===")
    synth_results = synthesize_jeff_stelling_script(
        scenes=scenes,
        output_dir=audio_dir,
        speed_factor=1.02,
        breath_scenes=["s01", "s03", "s05", "s06", "s07"]
    )
    scene_durations = []
    for s, res in zip(scenes, synth_results):
        scene_durations.append({
            "scene_id": s["scene_id"],
            "narration": s["narration"],
            "duration_sec": res["audio_duration_sec"]
        })

    # Prepare broadcast outro audio with whoosh transition if not already generated
    outro_wav = audio_dir / "scene_outro.wav"
    raw_outro = audio_dir / "outro_jeff.wav"
    whoosh_sfx = root / "data" / "sfx" / "meme_whoosh_swoosh.wav"
    if not raw_outro.exists():
        from stages.jeff_stelling_synthesizer import synthesize_jeff_stelling_scene
        synthesize_jeff_stelling_scene(
            text="Follow Football in Thirty Seconds for daily breaking news.",
            output_wav_path=raw_outro,
            scene_id="outro",
            speed_factor=1.03
        )
    if not outro_wav.exists() or outro_wav.stat().st_size < 10000:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(raw_outro),
            "-i", str(whoosh_sfx),
            "-filter_complex",
            "[0:a]atempo=1.2,volume=1.1[vo]; [1:a]volume=0.35[sfx]; [vo]adelay=180|180[vodelayed]; [sfx][vodelayed]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-14:TP=-1.0:LRA=6,aformat=sample_rates=48000:channel_layouts=stereo[aout]",
            "-map", "[aout]",
            "-t", "2.4",
            str(outro_wav)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        
    logger.info("=== STEP 2: Generating Time-Aligned Subtitle File ===")
    srt_file = evidence_dir / "endrick_milan_v2_rebuild.srt"
    generate_aligned_srt(scene_durations, srt_file)
    logger.info(f"SRT generated: {srt_file}")
    
    logger.info("=== STEP 3: Preparing Remotion Props ===")
    props = prepare_remotion_props(script_data, root, fps=30.0)
    
    raw_video = evidence_dir / "endrick_milan_remotion_raw.mp4"
    master_video = evidence_dir / "endrick_milan_remotion_master.mp4"
    storyboard_img = evidence_dir / "endrick_milan_remotion_storyboard.jpg"
    qa_report_file = evidence_dir / "remotion_qa_report.json"
    
    logger.info("=== STEP 4: Headless Remotion Render ===")
    render_with_remotion(props, raw_video, remotion_dir)
    
    logger.info("=== STEP 5: Mastering Audio (-14 LUFS) & Muxing Master Video ===")
    master_audio_and_mux(raw_video, props["scenes"], master_video, temp_dir)
    
    logger.info("=== STEP 6: Generating Storyboard Contact Sheet ===")
    generate_remotion_storyboard(master_video, storyboard_img, num_samples=6)
    
    logger.info("=== STEP 7: Automated QA Audit ===")
    qa_report = inspect_video(master_video, scenes=props["scenes"])
    qa_report_file.write_text(json.dumps(qa_report, indent=2), encoding="utf-8")
    
    # Copy all master deliverables to artifact directory
    artifact_dir = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")
    if artifact_dir.exists():
        for f in [master_video, storyboard_img, qa_report_file, srt_file]:
            if f.exists():
                shutil.copy2(f, artifact_dir / f.name)
                logger.info(f"Copied to artifact: {f.name}")
                
        # Also copy Jeff Stelling sample
        sample_src = root / "temp" / "jeff_stelling_test" / "test_jeff_synth.wav"
        if sample_src.exists():
            shutil.copy2(sample_src, artifact_dir / "jeff_stelling_sample.wav")
            
    print("\n" + "="*60)
    print("  JEFF STELLING REBUILD COMPLETED SUCCESSFULLY! ✅")
    print(f"  Master MP4:  {master_video}")
    print(f"  Storyboard:  {storyboard_img}")
    print(f"  QA Verdict:  {qa_report.get('overall_status')}")
    print(f"  Loudness:    {qa_report.get('audio_loudness', {}).get('integrated_lufs')} LUFS")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
