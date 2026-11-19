import React from "react";
import { useCurrentFrame } from "remotion";
import { SubtitleCue } from "../types";
import { tokens } from "../design/tokens";

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
        left: tokens.layout.subtitles.left,
        right: tokens.layout.subtitles.right,
        bottom: tokens.layout.subtitles.bottom, // Resting cleanly above the lower third
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        zIndex: tokens.layout.subtitles.zIndex,
        pointerEvents: "none",
        fontFamily: tokens.typography.fontPrimary,
      }}
    >
      <div
        style={{
          background: tokens.colors.navyGlass,
          padding: "10px 24px",
          borderRadius: 6,
          border: `1px solid ${tokens.colors.yellowSubtle}`,
          boxShadow: tokens.colors.shadowCard,
          maxWidth: "88%",
          textAlign: "center",
        }}
      >
        <span
          style={{
            color: tokens.colors.yellowHighlight,
            fontWeight: tokens.typography.weights.black,
            fontSize: tokens.typography.sizes.subtitleCard,
            lineHeight: tokens.typography.lineHeights.compact,
            letterSpacing: tokens.typography.letterSpacing.normal,
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
