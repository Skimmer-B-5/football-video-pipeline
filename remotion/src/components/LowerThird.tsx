import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { SceneOnScreen } from "../types";

export interface LowerThirdProps {
  onScreen: SceneOnScreen;
}

export const LowerThird: React.FC<LowerThirdProps> = ({ onScreen }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Snappy spring entrance for lower third
  const entrance = spring({
    frame,
    fps,
    config: { damping: 14, mass: 0.7, stiffness: 120 },
  });

  const translateX = (1 - entrance) * -80;
  const opacity = Math.min(entrance * 1.5, 1);

  const { headline, subheadline, data_callout, status_badge } = onScreen;

  return (
    <div
      style={{
        position: "absolute",
        left: 90,
        right: 90,
        bottom: 390, // Resting cleanly above subtitle/ticker band
        transform: `translateX(${translateX}px)`,
        opacity,
        zIndex: 40,
      }}
    >
      <div
        style={{
          background: "rgba(11, 19, 43, 0.94)",
          borderLeft: "8px solid #D90429",
          borderRadius: "0 8px 8px 0",
          padding: "20px 28px",
          boxShadow: "0 12px 32px rgba(0, 0, 0, 0.75)",
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        {/* Top Badges Row */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {status_badge && (
            <span
              style={{
                background: status_badge === "RUMOUR" ? "#F77F00" : "#D90429",
                color: "#FFFFFF",
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 900,
                fontSize: 18,
                letterSpacing: "1.5px",
                padding: "3px 10px",
                borderRadius: 3,
                textTransform: "uppercase",
              }}
            >
              {status_badge}
            </span>
          )}

          {data_callout && (
            <span
              style={{
                background: "#FFD166",
                color: "#0B132B",
                fontFamily: "'Barlow Condensed', sans-serif",
                fontWeight: 900,
                fontSize: 18,
                letterSpacing: "1px",
                padding: "3px 10px",
                borderRadius: 3,
                textTransform: "uppercase",
              }}
            >
              {data_callout}
            </span>
          )}
        </div>

        {/* Primary Headline */}
        <div
          style={{
            color: "#FFFFFF",
            fontFamily: "'Barlow Condensed', 'Arial Black', sans-serif",
            fontWeight: 900,
            fontSize: 54,
            lineHeight: 1.05,
            letterSpacing: "0.5px",
            textTransform: "uppercase",
            textShadow: "0 2px 8px rgba(0, 0, 0, 0.8)",
          }}
        >
          {headline}
        </div>

        {/* Supporting Subheadline */}
        {subheadline && (
          <div
            style={{
              color: "#FFD166",
              fontFamily: "'Barlow Condensed', sans-serif",
              fontWeight: 700,
              fontSize: 32,
              lineHeight: 1.15,
              letterSpacing: "1px",
              textTransform: "uppercase",
              opacity: 0.95,
            }}
          >
            {subheadline}
          </div>
        )}
      </div>
    </div>
  );
};
