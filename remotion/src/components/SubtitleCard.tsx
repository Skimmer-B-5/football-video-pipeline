import React from "react";
import { useCurrentFrame } from "remotion";
import { SubtitleCue } from "../types";

export interface SubtitleCardProps {
  subtitles: SubtitleCue[];
}

export const SubtitleCard: React.FC<SubtitleCardProps> = ({ subtitles }) => {
  const frame = useCurrentFrame();

  // Find active subtitle cue at current frame
  const activeCue = subtitles.find(
    (cue) => frame >= cue.start_frame && frame <= cue.end_frame
  );

  if (!activeCue) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: 90,
        right: 90,
        bottom: 600, // Directly above the lower third card
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 45,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          background: "rgba(11, 19, 43, 0.88)",
          padding: "10px 24px",
          borderRadius: 6,
          border: "1px solid rgba(255, 209, 102, 0.4)",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.8)",
          maxWidth: "85%",
          textAlign: "center",
        }}
      >
        <span
          style={{
            color: "#FFD166",
            fontFamily: "'Barlow Condensed', 'Arial Black', sans-serif",
            fontWeight: 900,
            fontSize: 40,
            lineHeight: 1.15,
            letterSpacing: "1px",
            textTransform: "uppercase",
            textShadow: "0 2px 10px rgba(0, 0, 0, 0.9)",
          }}
        >
          {activeCue.text}
        </span>
      </div>
    </div>
  );
};
