import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";

export interface TopHUDProps {
  kicker: string;
}

export const TopHUD: React.FC<TopHUDProps> = ({ kicker }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Subtle spring entry for HUD
  const hudProgress = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.5, stiffness: 120 },
  });

  const translateY = (1 - hudProgress) * -20;
  const opacity = Math.min(hudProgress, 1);

  return (
    <div
      style={{
        position: "absolute",
        top: 195,
        left: 90,
        right: 90,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        zIndex: 50,
        transform: `translateY(${translateY}px)`,
        opacity,
      }}
    >
      {/* Channel Bug / Brand */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 12,
          background: "rgba(11, 19, 43, 0.92)",
          padding: "10px 18px",
          borderLeft: "4px solid #D90429",
          borderRadius: 4,
          boxShadow: "0 4px 16px rgba(0, 0, 0, 0.6)",
        }}
      >
        <span
          style={{
            background: "#D90429",
            color: "#FFFFFF",
            fontFamily: "'Barlow Condensed', 'Arial Black', sans-serif",
            fontWeight: 900,
            fontSize: 22,
            padding: "2px 8px",
            borderRadius: 2,
            letterSpacing: "1px",
          }}
        >
          30s
        </span>
        <span
          style={{
            color: "#FFFFFF",
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 800,
            fontSize: 24,
            letterSpacing: "2px",
            textTransform: "uppercase",
          }}
        >
          FOOTBALL IN 30 SECONDS
        </span>
      </div>

      {/* Truthful Kicker / Badge */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "rgba(11, 19, 43, 0.92)",
          padding: "10px 20px",
          borderRight: "4px solid #FFD166",
          borderRadius: 4,
          boxShadow: "0 4px 16px rgba(0, 0, 0, 0.6)",
        }}
      >
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            background: "#FFD166",
            boxShadow: "0 0 10px #FFD166",
          }}
        />
        <span
          style={{
            color: "#FFD166",
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 800,
            fontSize: 22,
            letterSpacing: "1.5px",
            textTransform: "uppercase",
          }}
        >
          {kicker || "TRANSFER WATCH"}
        </span>
      </div>
    </div>
  );
};
