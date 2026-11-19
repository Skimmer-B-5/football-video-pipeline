import React from "react";
import { useCurrentFrame } from "remotion";

export interface RollingTickerProps {
  text: string;
}

export const RollingTicker: React.FC<RollingTickerProps> = ({ text }) => {
  const frame = useCurrentFrame();

  // Scroll speed in pixels per frame
  const scrollOffset = (frame * 5) % 2500;

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 330, // Directly above the 320px bottom safe zone
        height: 48,
        display: "flex",
        alignItems: "center",
        zIndex: 50,
        boxShadow: "0 -4px 16px rgba(0, 0, 0, 0.6)",
      }}
    >
      {/* Red Ticker Lead Badge */}
      <div
        style={{
          background: "#D90429",
          color: "#FFFFFF",
          fontFamily: "'Barlow Condensed', sans-serif",
          fontWeight: 900,
          fontSize: 22,
          letterSpacing: "1.5px",
          padding: "0 24px",
          height: "100%",
          display: "flex",
          alignItems: "center",
          zIndex: 2,
          whiteSpace: "nowrap",
          boxShadow: "4px 0 12px rgba(0, 0, 0, 0.4)",
        }}
      >
        LATEST NEWS
      </div>

      {/* Navy Rolling Text Container */}
      <div
        style={{
          flex: 1,
          height: "100%",
          background: "#0B132B",
          borderTop: "1px solid rgba(255, 209, 102, 0.3)",
          borderBottom: "1px solid rgba(255, 209, 102, 0.3)",
          overflow: "hidden",
          position: "relative",
          display: "flex",
          alignItems: "center",
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 1080 - scrollOffset,
            whiteSpace: "nowrap",
            color: "#FFFFFF",
            fontFamily: "'Barlow Condensed', sans-serif",
            fontWeight: 700,
            fontSize: 24,
            letterSpacing: "1px",
            textTransform: "uppercase",
          }}
        >
          {text} &nbsp;&nbsp;✦&nbsp;&nbsp; {text}
        </div>
      </div>
    </div>
  );
};
