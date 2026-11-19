"""
run_remotion_endrick_test_render.py - Full End-to-End Test Render using the new Remotion Visual Director.
"""

import json
import logging
import shutil
from pathlib import Path

from stages.remotion_renderer import (
    prepare_remotion_props,
    render_with_remotion,
    master_audio_and_mux,
    generate_remotion_storyboard
)
from stages.verify_video import inspect_video

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RemotionTestRender")

def main():
    root = Path(__file__).resolve().parent
    remotion_dir = root / "remotion"
    evidence_dir = root / "evidence"
    temp_dir = root / "data" / "temp_remotion_assembly"
    
    script_file = evidence_dir / "endrick_milan_approved_script_v2.json"
    if not script_file.exists():
        raise FileNotFoundError(f"Missing approved script: {script_file}")
        
    script_data = json.loads(script_file.read_text(encoding="utf-8"))
    
    logger.info("1. Preparing typed Remotion props from Schema v2.0...")
    props = prepare_remotion_props(script_data, root, fps=30.0)
    
    props_dump = evidence_dir / "remotion_render_props.json"
    props_dump.write_text(json.dumps(props, indent=2), encoding="utf-8")
    logger.info(f"Props dumped to: {props_dump}")
    
    raw_video = evidence_dir / "endrick_milan_remotion_raw.mp4"
    master_video = evidence_dir / "endrick_milan_remotion_master.mp4"
    storyboard_img = evidence_dir / "endrick_milan_remotion_storyboard.jpg"
    qa_report_file = evidence_dir / "remotion_qa_report.json"
    
    logger.info("2. Executing headless Remotion video render...")
    render_with_remotion(props, raw_video, remotion_dir)
    
    logger.info("3. Mastering audio to -14 LUFS and muxing master video...")
    master_audio_and_mux(raw_video, props["scenes"], master_video, temp_dir)
    
    logger.info("4. Generating storyboard contact sheet...")
    generate_remotion_storyboard(master_video, storyboard_img, num_samples=6)
    
    logger.info("5. Running broadcast QA verification...")
    qa_report = inspect_video(
        master_video,
        scenes=props["scenes"]
    )
    qa_report_file.write_text(json.dumps(qa_report, indent=2), encoding="utf-8")
    logger.info(f"QA Report written: {qa_report_file}")
    
    # Copy key deliverables to conversation artifact directory
    artifact_dir = Path(r"C:\Users\sb000\.gemini\antigravity\brain\39259585-6e0b-4fd0-8946-7c7ef3b89b1d")
    if artifact_dir.exists():
        for f in [master_video, storyboard_img, qa_report_file, props_dump]:
            if f.exists():
                shutil.copy2(f, artifact_dir / f.name)
                logger.info(f"Copied to artifact directory: {f.name}")
                
    logger.info("REMOTION VIDEO RENDER & MASTERING COMPLETED SUCCESSFULLY! ✅")
    print("\n" + "="*60)
    print("  REMOTION MASTER VIDEO RENDERED")
    print(f"  Master MP4: {master_video}")
    print(f"  Storyboard: {storyboard_img}")
    print(f"  QA Status:  {qa_report.get('overall_status')}")
    print(f"  Loudness:   {qa_report.get('audio_loudness', {}).get('integrated_lufs')} LUFS")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
