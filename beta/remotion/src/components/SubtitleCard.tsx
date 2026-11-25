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
        fontFamily: tokens.typography.fontReading,
      }}
    >
      <div
        style={{
          background: "linear-gradient(180deg, rgba(11, 19, 43, 0) 0%, rgba(11, 19, 43, 0.82) 100%)",
          padding: "12px 28px",
          borderRadius: 8,
          maxWidth: "92%",
          textAlign: "center",
        }}
      >
        <span
          style={{
            color: tokens.colors.textWhite,
            fontWeight: tokens.typography.weights.semiBold,
            fontSize: activeCue.text.length > 34 ? 38 : tokens.typography.sizes.subtitleCard,
            lineHeight: tokens.typography.lineHeights.subtitle,
            letterSpacing: tokens.typography.letterSpacing.tight,
            textTransform: "none", // Sentence case, never forced uppercase
            textShadow: "0 2px 8px rgba(0, 0, 0, 0.95)",
            display: "inline-block",
            maxWidth: "920px",
          }}
        >
          {activeCue.text}
        </span>
      </div>
    </div>
  );
};
